import unicodedata

import polars as pl

from analyzer_interface.context import SecondaryAnalyzerContext
from terminal_tools import ProgressReporter

from ..ngrams_base.interface import (
    COL_AUTHOR_ID,
    COL_MESSAGE_SURROGATE_ID,
    COL_MESSAGE_TEXT,
    OUTPUT_MESSAGE,
)
from .interface import (
    COL_CLUSTER_ID,
    COL_LARGEST_CLUSTER_SIZE,
    COL_SOURCE_ID,
    COL_TARGET_ID,
    COL_TOTAL_CLUSTERS,
    COL_TOTAL_REPEATED_MESSAGES,
    COL_UNIQUE_AUTHORS,
    OUTPUT_COPYPASTA_EDGES,
    OUTPUT_COPYPASTA_NODES,
    OUTPUT_COPYPASTA_SUMMARY,
    PARAM_CROSS_AUTHOR_ONLY,
    interface,
)

_COL_NORMALIZED = "_normalized_text"
_COL_CLUSTER_SIZE = "_cluster_size"


def _get_param_default(param_id: str):
    for param in interface.params:
        if param.id == param_id:
            return param.default
    return None


def _normalize_text(text: str) -> str:
    """NFC-normalize, lowercase, and collapse whitespace."""
    normalized = unicodedata.normalize("NFC", text)
    return " ".join(normalized.lower().split())


def _build_clusters(
    df_messages: pl.DataFrame,
    cross_author_only: bool,
) -> pl.DataFrame:
    """
    Group messages by normalized text and return a cluster assignment table.

    Returns a DataFrame with cluster_id, message_surrogate_id, author_id,
    message_text columns — one row per message that belongs to a repeated cluster.
    """
    df = df_messages.with_columns(
        pl.col(COL_MESSAGE_TEXT)
        .map_elements(_normalize_text, return_dtype=pl.Utf8)
        .alias(_COL_NORMALIZED)
    )

    # Aggregate per normalized text: collect message IDs, authors, original text
    df_groups = df.group_by(_COL_NORMALIZED).agg(
        pl.col(COL_MESSAGE_SURROGATE_ID).alias("message_ids"),
        pl.col(COL_AUTHOR_ID).alias("author_ids"),
        pl.col(COL_MESSAGE_TEXT).first().alias(COL_MESSAGE_TEXT),
    )

    # Keep only groups with 2+ messages
    df_groups = df_groups.filter(pl.col("message_ids").list.len() >= 2)

    if cross_author_only:
        # Keep only groups where at least 2 distinct authors are involved
        df_groups = df_groups.filter(
            pl.col("author_ids").list.n_unique() >= 2
        )

    if df_groups.height == 0:
        return pl.DataFrame(
            schema={
                COL_CLUSTER_ID: pl.Int64,
                COL_MESSAGE_SURROGATE_ID: pl.Int64,
                COL_AUTHOR_ID: pl.Utf8,
                COL_MESSAGE_TEXT: pl.Utf8,
            }
        )

    # Assign cluster IDs
    df_groups = df_groups.with_row_index(name=COL_CLUSTER_ID)

    # Explode to one row per (cluster, message)
    df_nodes = (
        df_groups.select(
            COL_CLUSTER_ID,
            pl.col("message_ids").alias(COL_MESSAGE_SURROGATE_ID),
            pl.col("author_ids").alias(COL_AUTHOR_ID),
            COL_MESSAGE_TEXT,
        )
        .explode(COL_MESSAGE_SURROGATE_ID, COL_AUTHOR_ID)
        .sort([COL_CLUSTER_ID, COL_MESSAGE_SURROGATE_ID])
    )

    return df_nodes


def _build_edges(df_nodes: pl.DataFrame) -> pl.DataFrame:
    """
    Generate pairwise edges within each cluster.

    For each cluster, produces edges (source_id, target_id) for every pair of
    messages in that cluster (source_id < target_id to avoid duplicates).
    """
    if df_nodes.height == 0:
        return pl.DataFrame(
            schema={
                COL_SOURCE_ID: pl.Int64,
                COL_TARGET_ID: pl.Int64,
                COL_CLUSTER_ID: pl.Int64,
            }
        )

    # Self-join within clusters to get all pairs
    df_edges = (
        df_nodes.select(COL_CLUSTER_ID, COL_MESSAGE_SURROGATE_ID)
        .join(
            df_nodes.select(COL_CLUSTER_ID, COL_MESSAGE_SURROGATE_ID),
            on=COL_CLUSTER_ID,
            suffix="_b",
        )
        .filter(
            pl.col(COL_MESSAGE_SURROGATE_ID)
            < pl.col(f"{COL_MESSAGE_SURROGATE_ID}_b")
        )
        .rename(
            {
                COL_MESSAGE_SURROGATE_ID: COL_SOURCE_ID,
                f"{COL_MESSAGE_SURROGATE_ID}_b": COL_TARGET_ID,
            }
        )
        .select(COL_SOURCE_ID, COL_TARGET_ID, COL_CLUSTER_ID)
    )

    return df_edges


def main(context: SecondaryAnalyzerContext):
    cross_author_only = _get_param_default(PARAM_CROSS_AUTHOR_ONLY)
    if cross_author_only is None:
        cross_author_only = True

    df_messages = pl.read_parquet(context.base.table(OUTPUT_MESSAGE).parquet_path)

    with ProgressReporter("Detecting repeated messages"):
        df_nodes = _build_clusters(df_messages, cross_author_only)

    with ProgressReporter("Building graph edges"):
        df_edges = _build_edges(df_nodes)

    with ProgressReporter("Writing outputs"):
        df_nodes.write_parquet(context.output(OUTPUT_COPYPASTA_NODES).parquet_path)
        df_edges.write_parquet(context.output(OUTPUT_COPYPASTA_EDGES).parquet_path)

        if df_nodes.height > 0:
            cluster_sizes = (
                df_nodes.group_by(COL_CLUSTER_ID)
                .agg(pl.len().alias(_COL_CLUSTER_SIZE))
            )
            df_summary = pl.DataFrame(
                {
                    COL_TOTAL_CLUSTERS: [df_nodes[COL_CLUSTER_ID].n_unique()],
                    COL_TOTAL_REPEATED_MESSAGES: [df_nodes.height],
                    COL_UNIQUE_AUTHORS: [df_nodes[COL_AUTHOR_ID].n_unique()],
                    COL_LARGEST_CLUSTER_SIZE: [
                        cluster_sizes[_COL_CLUSTER_SIZE].max()
                    ],
                }
            )
        else:
            df_summary = pl.DataFrame(
                {
                    COL_TOTAL_CLUSTERS: [0],
                    COL_TOTAL_REPEATED_MESSAGES: [0],
                    COL_UNIQUE_AUTHORS: [0],
                    COL_LARGEST_CLUSTER_SIZE: [0],
                }
            )

        df_summary.write_parquet(
            context.output(OUTPUT_COPYPASTA_SUMMARY).parquet_path
        )
