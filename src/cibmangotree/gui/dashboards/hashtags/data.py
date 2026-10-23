"""
Thin data loading wrappers for the hashtags analyzer.

Provides functions to load and transform hashtag analysis data.
"""

import polars as pl

from cibmangotree.analyzers.hashtags.hashtags_base.interface import (
    COL_TIME,
    OUTPUT_COL_HASHTAGS,
    PRIMARY_OUTPUT_DATETIME_FORMAT,
    SECONDARY_COL_USERS_ALL,
)
from cibmangotree.app.project_context import _get_columns_with_semantic
from cibmangotree.gui.session import GuiSession

DISPLAY_DATE_FORMAT = "%B %d, %Y %H:%M"


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


def load_mapped_timestamps(session: GuiSession) -> pl.Series:
    """Load the mapped timestamp column for the project open in the session.

    Reads only that column. The semantic transform is the one inferred for the
    user column, applied to the full series rather than the preview slice.
    """
    project = session.current_project
    column_mapping = session.column_mapping
    if project is None or not column_mapping or COL_TIME not in column_mapping:
        raise ValueError("Timestamp column is not mapped")

    user_column = column_mapping[COL_TIME]
    input_path = session.app.context.storage._get_project_input_path(project.id)
    series = pl.read_parquet(input_path, columns=[user_column]).to_series()

    column = project.column_dict.get(user_column)
    if column is not None:
        series = column.semantic.try_convert(series)
    return series


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
    from cibmangotree.analyzers.hashtags.hashtags_base.interface import (
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
            pl.col(OUTPUT_COL_TIMESPAN).str.to_datetime(PRIMARY_OUTPUT_DATETIME_FORMAT)
        )

    return df


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
