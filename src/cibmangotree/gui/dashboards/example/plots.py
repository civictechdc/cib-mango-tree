"""
Framework-agnostic ECharts figure builder for the example analyzer.
"""

import polars as pl

CHARACTER_COUNT_COL = "character_count"
BUCKET_WIDTH = 20

MANGO_DARK_ORANGE = "#f3921e"


def plot_character_count_histogram_echart(df: pl.DataFrame) -> dict:
    """
    Build a histogram of message character counts, bucketed into fixed-width
    ranges (e.g. "0-19", "20-39", ...).
    """
    df_bucketed = (
        df.with_columns(
            (pl.col(CHARACTER_COUNT_COL) // BUCKET_WIDTH * BUCKET_WIDTH).alias(
                "bucket_start"
            )
        )
        .group_by("bucket_start")
        .agg(pl.len().alias("count"))
        .sort("bucket_start")
    )

    labels = [
        f"{start}-{start + BUCKET_WIDTH - 1}"
        for start in df_bucketed["bucket_start"].to_list()
    ]
    counts = df_bucketed["count"].to_list()

    return {
        "title": {"text": "Message length distribution"},
        "tooltip": {"trigger": "axis", "axisPointer": {"type": "shadow"}},
        "grid": {"left": 60, "right": 30, "top": 70, "bottom": 60},
        "xAxis": {
            "type": "category",
            "data": labels,
            "name": "Character count",
            "nameLocation": "middle",
            "nameGap": 40,
            "axisLabel": {"fontSize": 11, "rotate": 45},
        },
        "yAxis": {
            "type": "value",
            "name": "Number of messages",
            "nameLocation": "middle",
            "nameGap": 40,
        },
        "series": [
            {
                "name": "Messages",
                "type": "bar",
                "data": counts,
                "itemStyle": {"color": MANGO_DARK_ORANGE},
                "emphasis": {"itemStyle": {"color": "#d62728"}},
            }
        ],
    }


# Re-exported so callers only need one import for the analyzer's output column.
__all__ = ["plot_character_count_histogram_echart", "CHARACTER_COUNT_COL"]
