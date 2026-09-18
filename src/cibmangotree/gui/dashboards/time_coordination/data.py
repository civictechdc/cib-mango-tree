"""
Thin data loading wrapper for the time_coordination analyzer.
"""

import polars as pl

from cibmangotree.analyzers.time_coordination.interface import (
    OUTPUT_COL_FREQ,
    OUTPUT_COL_USER1,
    OUTPUT_COL_USER2,
    OUTPUT_TABLE,
)
from cibmangotree.gui.dashboards.base_dashboard import BaseDashboardPage


def load_coordinated_pairs(dashboard: BaseDashboardPage) -> pl.DataFrame | None:
    """
    Load the analyzer's primary output and reduce it to distinct, meaningful
    pairs.

    The raw output includes a self-pair for every user (they always
    co-occur with themselves) and both directions of every real pair
    (A, B) and (B, A) with the same count. Keeping only rows where
    user_id_1 < user_id_2 drops both the self-pairs and the duplicate
    direction in one filter.
    """
    path = dashboard.get_primary_output_parquet_path(OUTPUT_TABLE)
    if path is None:
        return None

    df = pl.read_parquet(path)
    return df.filter(pl.col(OUTPUT_COL_USER1) < pl.col(OUTPUT_COL_USER2)).sort(
        OUTPUT_COL_FREQ, descending=True
    )
