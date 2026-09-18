"""
Framework-agnostic ECharts figure builder for the temporal analyzer.

Accepts a Polars DataFrame and returns an ECharts option dict, with no
dependency on NiceGUI.
"""

from datetime import time

import polars as pl

from cibmangotree.analyzers.temporal.temporal_base.interface import (
    OUTPUT_COL_POST_COUNT,
    OUTPUT_COL_TIME_INTERVAL_END,
    OUTPUT_COL_TIME_INTERVAL_START,
)

MANGO_DARK_ORANGE = "#f3921e"


def _format_interval(start: time, end: time) -> str:
    return f"{start.strftime('%H:%M')}-{end.strftime('%H:%M')}"


def plot_temporal_bar_echart(df: pl.DataFrame) -> dict:
    """
    Build a bar chart of post counts per time-of-day interval.

    Args:
        df: Primary output DataFrame with time_interval_start, time_interval_end,
            and count columns, sorted by time_interval_start.

    Returns:
        ECharts option dict ready for ui.echart().
    """
    labels = [
        _format_interval(start, end)
        for start, end in zip(
            df[OUTPUT_COL_TIME_INTERVAL_START].to_list(),
            df[OUTPUT_COL_TIME_INTERVAL_END].to_list(),
        )
    ]
    counts = df[OUTPUT_COL_POST_COUNT].to_list()

    return {
        "title": {"text": "Posting activity by time of day"},
        "tooltip": {
            "trigger": "axis",
            "axisPointer": {"type": "shadow"},
        },
        "grid": {"left": 60, "right": 30, "top": 70, "bottom": 60},
        "xAxis": {
            "type": "category",
            "data": labels,
            "name": "Time interval",
            "nameLocation": "middle",
            "nameGap": 40,
            "axisLabel": {"fontSize": 11, "rotate": 45},
        },
        "yAxis": {
            "type": "value",
            "name": "Number of posts",
            "nameLocation": "middle",
            "nameGap": 40,
        },
        "series": [
            {
                "name": "Posts",
                "type": "bar",
                "data": counts,
                "itemStyle": {"color": MANGO_DARK_ORANGE},
                "emphasis": {"itemStyle": {"color": "#d62728"}},
            }
        ],
    }
