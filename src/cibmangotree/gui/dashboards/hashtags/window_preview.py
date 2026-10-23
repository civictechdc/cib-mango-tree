"""Post-activity bins and analysis-window edges for the parameter step.

The activity series is a fixed display resolution. Window lines follow the
same `group_by_dynamic(..., start_by="datapoint")` rule as hashtag analysis.
"""

from dataclasses import dataclass
from datetime import datetime

import polars as pl

from cibmangotree.analyzer_interface.params import TimeBinningValue
from cibmangotree.analyzers.hashtags.hashtags_base.interface import COL_TIME
from cibmangotree.gui.theme import MANGO_ORANGE

ACTIVITY_BIN_COUNT = 150
# The sample hashtag file has 91 occupied hours and 100 occupied minutes.
# 100 keeps a 12-hour or 1-hour choice drawable and still omits 1-minute windows.
MAX_WINDOW_LINES = 100


@dataclass(frozen=True)
class WindowEdges:
    """Window starts produced for one time-binning value.

    `starts` is None when there are too many lines to draw. `count` is always
    the number of windows.
    """

    count: int
    starts: list[datetime] | None


def activity_bins(
    timestamps: pl.Series, bin_count: int = ACTIVITY_BIN_COUNT
) -> pl.DataFrame:
    """Bin post counts from `timestamps` into at most `bin_count` equal spans.

    Null timestamps are dropped. The result has `bin_start` and `count`
    columns, including bins whose count is zero.
    """
    ts = _sorted_timestamps(timestamps)
    empty = pl.DataFrame(schema={"bin_start": pl.Datetime("us"), "count": pl.UInt32})
    if ts.len() == 0:
        return empty

    if bin_count < 1:
        bin_count = 1

    start = ts.item(0)
    if ts.len() == 1 or ts.item(-1) == start:
        return pl.DataFrame({"bin_start": [start], "count": [ts.len()]}).cast(
            {"count": pl.UInt32}
        )

    microseconds = ts.dt.timestamp("us")
    start_us = int(microseconds.min())
    span = int(microseconds.max()) - start_us
    if span <= 0:
        return pl.DataFrame({"bin_start": [start], "count": [ts.len()]}).cast(
            {"count": pl.UInt32}
        )

    frame = pl.DataFrame({"us": microseconds}).with_columns(
        ((pl.col("us") - start_us) * bin_count // span)
        .clip(0, bin_count - 1)
        .alias("bin_index")
    )
    counts = frame.group_by("bin_index").agg(pl.len().alias("count"))
    grid = pl.DataFrame({"bin_index": list(range(bin_count))})
    return (
        grid.join(counts, on="bin_index", how="left")
        .with_columns(pl.col("count").fill_null(0).cast(pl.UInt32))
        .with_columns(
            pl.from_epoch(
                start_us + pl.col("bin_index") * span // bin_count,
                time_unit="us",
            ).alias("bin_start")
        )
        .select("bin_start", "count")
        .sort("bin_start")
    )


def window_edges(
    timestamps: pl.Series,
    window: TimeBinningValue,
    *,
    max_lines: int = MAX_WINDOW_LINES,
) -> WindowEdges:
    """Window starts for `window`, using the hashtag analyzer's grouping rule.

    Line positions are omitted when the window count is above `max_lines`.
    """
    ts = _sorted_timestamps(timestamps)
    if ts.len() == 0 or window.amount < 1:
        return WindowEdges(count=0, starts=[])

    grouped = (
        pl.DataFrame({COL_TIME: ts})
        .group_by_dynamic(
            COL_TIME,
            every=window.to_polars_truncate_spec(),
            period=window.to_polars_truncate_spec(),
            start_by="datapoint",
        )
        .agg(pl.len())
    )
    starts = grouped[COL_TIME].to_list()
    if len(starts) >= max_lines:
        return WindowEdges(count=len(starts), starts=None)
    return WindowEdges(count=len(starts), starts=starts)


def window_count_text(count: int) -> str:
    if count == 1:
        return "1 window"
    return f"{count} windows"


def plot_activity_echart(bins: pl.DataFrame, edges: WindowEdges) -> dict:
    """ECharts option for cached activity bins and the current window edges."""
    series_data = [
        [ts.isoformat(), count]
        for ts, count in zip(bins["bin_start"].to_list(), bins["count"].to_list())
    ]
    line_data = (
        [{"xAxis": start.isoformat()} for start in edges.starts] if edges.starts else []
    )
    series: dict = {
        "name": "Posts",
        "type": "bar",
        "data": series_data,
        "itemStyle": {"color": MANGO_ORANGE},
        "barMaxWidth": 8,
        "markLine": {
            "symbol": "none",
            "silent": True,
            "lineStyle": {"color": "#424242", "type": "dashed"},
            "data": line_data,
        },
    }

    return {
        "tooltip": {"trigger": "axis"},
        "grid": {"left": 48, "right": 24, "top": 24, "bottom": 48},
        "xAxis": {"type": "time", "name": "Time"},
        "yAxis": {"type": "value", "name": "Posts", "minInterval": 1},
        "series": [series],
    }


def _sorted_timestamps(timestamps: pl.Series) -> pl.Series:
    ts = timestamps.drop_nulls()
    if ts.len() == 0:
        return ts
    if ts.dtype == pl.Date:
        ts = ts.cast(pl.Datetime("us"))
    elif not isinstance(ts.dtype, pl.Datetime):
        ts = ts.cast(pl.Datetime("us"))
    return ts.sort()
