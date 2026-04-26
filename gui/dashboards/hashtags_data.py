"""
Thin data loading wrappers for the hashtags analyzer.

Provides functions to:
- Load and transform raw input data (replicates factory.py logic)
- Run secondary analysis on-demand from primary output
"""

from datetime import datetime

import polars as pl

from analyzers.hashtags.hashtags_base.interface import (
    COL_TIME,
    OUTPUT_COL_HASHTAGS,
    SECONDARY_COL_USERS_ALL,
)
from analyzers.hashtags.hashtags_web.analysis import secondary_analyzer
from app.project_context import _get_columns_with_semantic
from gui.session import GuiSession


def load_transformed_raw_input(session: GuiSession) -> pl.DataFrame:
    """
    Load raw input dataset and apply analysis preprocessing.

    Replicates the logic from hashtags_web/factory.py:
    1. Load parquet from storage
    2. Apply semantic transforms to time/identifier columns
    3. Rename columns via column_mapping
    4. Sort by timestamp

    Args:
        session: GuiSession with current_analysis and app context.

    Returns:
        Transformed DataFrame with schema columns (e.g., COL_TIME, COL_AUTHOR_ID, COL_POST).
    """
    analysis = session.current_analysis
    if analysis is None:
        raise ValueError("No analysis selected in session")

    storage = session.app.context.storage
    project_id = analysis.project_id

    df_raw = storage.load_project_input(project_id)

    columns_with_semantic = _get_columns_with_semantic(df_raw)
    semantic_dict = {col.name: col for col in columns_with_semantic}

    column_mapping = analysis.column_mapping
    if column_mapping is None:
        raise ValueError("No column mapping found in analysis")

    transformed_columns = {}
    for schema_col, user_col in column_mapping.items():
        if user_col in semantic_dict:
            transformed_columns[schema_col] = semantic_dict[
                user_col
            ].apply_semantic_transform()
        else:
            transformed_columns[schema_col] = df_raw[user_col]

    df_transformed = df_raw.with_columns(
        [
            transformed_columns[schema_col].alias(schema_col)
            for schema_col in column_mapping.keys()
        ]
    )

    df_transformed = df_transformed.select(
        [pl.col(schema_col) for schema_col in column_mapping.keys()]
    ).sort(pl.col(COL_TIME))

    return df_transformed


def load_primary_output(session: GuiSession) -> pl.DataFrame:
    """
    Load primary output parquet and convert timewindow_start to datetime.

    The analyzer writes timewindow_start as a string ("%Y-%m-%d %H:%M:%S").
    This function reads the parquet and converts it back to datetime for
    downstream use (charting, secondary analysis).

    Args:
        session: GuiSession with current_analysis and app context.

    Returns:
        DataFrame with timewindow_start as datetime column.
    """
    from analyzers.hashtags.hashtags_base.interface import (
        OUTPUT_COL_TIMESPAN,
        OUTPUT_GINI,
    )

    analysis = session.current_analysis
    if analysis is None:
        raise ValueError("No analysis selected in session")

    storage = session.app.context.storage
    parquet_path = storage.get_primary_output_parquet_path(
        analysis,
        OUTPUT_GINI,
    )

    df = pl.read_parquet(parquet_path)

    if OUTPUT_COL_TIMESPAN in df.columns and df[OUTPUT_COL_TIMESPAN].dtype == pl.String:
        df = df.with_columns(
            pl.col(OUTPUT_COL_TIMESPAN).str.to_datetime("%Y-%m-%d %H:%M:%S")
        )

    return df


def run_secondary_analysis(
    df_primary: pl.DataFrame,
    timewindow: datetime,
) -> pl.DataFrame:
    """
    Run secondary analysis for a single timewindow.

    Thin wrapper around secondary_analyzer() from the Shiny app.

    Args:
        df_primary: Primary output DataFrame with timewindow_start column.
        timewindow: The selected timewindow start datetime.

    Returns:
        DataFrame with per-hashtag stats (hashtags, users_all, users_unique, hashtag_perc).
    """
    return secondary_analyzer(df_primary, timewindow)


def extract_users_for_hashtag(
    df_secondary: pl.DataFrame,
    hashtag: str,
) -> pl.DataFrame:
    """
    Extract users who posted a specific hashtag from secondary analysis output.

    Args:
        df_secondary: Output of secondary_analyzer() with columns:
                      hashtags, users_all, users_unique, hashtag_perc
        hashtag: The hashtag to filter by.

    Returns:
        DataFrame with columns: User, Posts (sorted by Posts descending).
        Empty DataFrame if hashtag not found.
    """
    hashtag_rows = df_secondary.filter(pl.col(OUTPUT_COL_HASHTAGS) == hashtag)

    if hashtag_rows.is_empty():
        return pl.DataFrame()

    users_col = hashtag_rows[SECONDARY_COL_USERS_ALL].to_list()[0]
    return (
        pl.DataFrame({SECONDARY_COL_USERS_ALL: users_col})
        .group_by(SECONDARY_COL_USERS_ALL)
        .agg(pl.count().alias("count"))
        .sort("count", descending=True)
        .rename({SECONDARY_COL_USERS_ALL: "User", "count": "Posts"})
    )
