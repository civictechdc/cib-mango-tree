"""
Framework-agnostic ECharts figure builder for the time_coordination analyzer.
"""

import polars as pl

from cibmangotree.analyzers.time_coordination.interface import (
    OUTPUT_COL_FREQ,
    OUTPUT_COL_USER1,
    OUTPUT_COL_USER2,
)

MANGO_DARK_ORANGE = "#f3921e"

TOP_N_PAIRS = 15


def plot_top_pairs_echart(df: pl.DataFrame) -> dict:
    """
    Build a horizontal bar chart of the most time-coordinated user pairs.

    Args:
        df: Deduplicated, self-pair-free output sorted by cooccurrence
            count descending (see data.load_coordinated_pairs).

    Returns:
        ECharts option dict ready for ui.echart().
    """
    df_top = df.head(TOP_N_PAIRS)

    labels = [
        f"{u1} & {u2}"
        for u1, u2 in zip(
            df_top[OUTPUT_COL_USER1].to_list(), df_top[OUTPUT_COL_USER2].to_list()
        )
    ]
    counts = df_top[OUTPUT_COL_FREQ].to_list()

    # Reverse so the highest count renders at the top of the horizontal chart.
    labels = list(reversed(labels))
    counts = list(reversed(counts))

    return {
        "title": {"text": "Most time-coordinated user pairs"},
        "tooltip": {"trigger": "axis", "axisPointer": {"type": "shadow"}},
        "grid": {"left": 150, "right": 30, "top": 50, "bottom": 40},
        "xAxis": {"type": "value", "name": "Co-occurrence count"},
        "yAxis": {
            "type": "category",
            "data": labels,
            "axisLabel": {"fontSize": 11},
        },
        "series": [
            {
                "name": "Co-occurrences",
                "type": "bar",
                "data": counts,
                "itemStyle": {"color": MANGO_DARK_ORANGE},
                "emphasis": {"itemStyle": {"color": "#d62728"}},
            }
        ],
    }
