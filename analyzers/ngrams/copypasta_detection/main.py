import polars as pl

from analyzer_interface.context import SecondaryAnalyzerContext
from terminal_tools import ProgressReporter

from ..ngrams_base.interface import (
    COL_AUTHOR_ID,
    COL_MESSAGE_SURROGATE_ID,
    COL_MESSAGE_TEXT,
    COL_NGRAM_ID,
    OUTPUT_MESSAGE,
    OUTPUT_MESSAGE_NGRAMS,
)
from .interface import (
    COL_AUTHOR_ID_A,
    COL_AUTHOR_ID_B,
    COL_AVG_SIMILARITY,
    COL_CLUSTER_ID,
    COL_JACCARD_SIMILARITY,
    COL_MESSAGE_SURROGATE_ID_A,
    COL_MESSAGE_SURROGATE_ID_B,
    COL_SHARED_NGRAM_COUNT,
    COL_TEXT_A,
    COL_TEXT_B,
    COL_TOTAL_PAIRS,
    COL_UNIQUE_AUTHORS,
    COL_UNIQUE_MESSAGES,
    OUTPUT_COPYPASTA_CLUSTERS,
    OUTPUT_COPYPASTA_PAIRS,
    OUTPUT_COPYPASTA_SUMMARY,
    PARAM_CROSS_AUTHOR_ONLY,
    PARAM_SIMILARITY_THRESHOLD,
    interface,
)


def _get_param_default(param_id: str):
    """Get the default value for a parameter from the interface definition."""
    for param in interface.params:
        if param.id == param_id:
            return param.default
    return None


def _compute_jaccard_pairs(
    df_msg_ngrams: pl.DataFrame,
    threshold: float,
    progress_callback=None,
) -> pl.DataFrame:
    """
    Compute Jaccard similarity between all message pairs that share at least one n-gram.

    Uses a self-join on ngram_id to find candidate pairs, then computes exact
    Jaccard similarity for each pair.

    Args:
        df_msg_ngrams: DataFrame with message_surrogate_id and ngram_id columns
        threshold: Minimum Jaccard similarity to include in results
        progress_callback: Optional progress callback

    Returns:
        DataFrame with message_surrogate_id_a, message_surrogate_id_b,
        shared_ngram_count, jaccard_similarity
    """
    if progress_callback:
        progress_callback(0.1)

    # Compute n-gram set sizes per message
    msg_ngram_counts = df_msg_ngrams.group_by(COL_MESSAGE_SURROGATE_ID).agg(
        pl.col(COL_NGRAM_ID).n_unique().alias("ngram_count")
    )

    if progress_callback:
        progress_callback(0.2)

    # Self-join to find message pairs sharing at least one n-gram
    # Filter: message_a < message_b to avoid duplicates and self-pairs
    df_pairs = (
        df_msg_ngrams.join(df_msg_ngrams, on=COL_NGRAM_ID, suffix="_b")
        .filter(
            pl.col(COL_MESSAGE_SURROGATE_ID) < pl.col(f"{COL_MESSAGE_SURROGATE_ID}_b")
        )
        .group_by([COL_MESSAGE_SURROGATE_ID, f"{COL_MESSAGE_SURROGATE_ID}_b"])
        .agg(pl.col(COL_NGRAM_ID).n_unique().alias(COL_SHARED_NGRAM_COUNT))
    )

    if progress_callback:
        progress_callback(0.5)

    if df_pairs.height == 0:
        return pl.DataFrame(
            schema={
                COL_MESSAGE_SURROGATE_ID_A: pl.Int64,
                COL_MESSAGE_SURROGATE_ID_B: pl.Int64,
                COL_SHARED_NGRAM_COUNT: pl.UInt32,
                COL_JACCARD_SIMILARITY: pl.Float64,
            }
        )

    # Join n-gram counts for both messages in the pair
    df_pairs = df_pairs.join(
        msg_ngram_counts,
        on=COL_MESSAGE_SURROGATE_ID,
    ).join(
        msg_ngram_counts,
        left_on=f"{COL_MESSAGE_SURROGATE_ID}_b",
        right_on=COL_MESSAGE_SURROGATE_ID,
        suffix="_b",
    )

    if progress_callback:
        progress_callback(0.7)

    # Compute Jaccard: shared / (count_a + count_b - shared)
    df_pairs = (
        df_pairs.with_columns(
            (
                pl.col(COL_SHARED_NGRAM_COUNT).cast(pl.Float64)
                / (
                    pl.col("ngram_count").cast(pl.Float64)
                    + pl.col("ngram_count_b").cast(pl.Float64)
                    - pl.col(COL_SHARED_NGRAM_COUNT).cast(pl.Float64)
                )
            ).alias(COL_JACCARD_SIMILARITY)
        )
        .filter(pl.col(COL_JACCARD_SIMILARITY) >= threshold)
        .select(
            pl.col(COL_MESSAGE_SURROGATE_ID).alias(COL_MESSAGE_SURROGATE_ID_A),
            pl.col(f"{COL_MESSAGE_SURROGATE_ID}_b").alias(COL_MESSAGE_SURROGATE_ID_B),
            COL_SHARED_NGRAM_COUNT,
            COL_JACCARD_SIMILARITY,
        )
    )

    if progress_callback:
        progress_callback(0.9)

    return df_pairs


def _assign_clusters(df_pairs: pl.DataFrame) -> pl.DataFrame:
    """
    Assign cluster IDs to messages using union-find on the pair graph.

    Connected components of the pair graph form copypasta clusters.

    Args:
        df_pairs: DataFrame with message_surrogate_id_a and message_surrogate_id_b

    Returns:
        DataFrame with cluster_id and message_surrogate_id columns
    """
    if df_pairs.height == 0:
        return pl.DataFrame(
            schema={
                COL_CLUSTER_ID: pl.Int64,
                COL_MESSAGE_SURROGATE_ID: pl.Int64,
            }
        )

    # Union-Find implementation
    parent: dict[int, int] = {}

    def find(x: int) -> int:
        while parent.get(x, x) != x:
            parent[x] = parent.get(parent[x], parent[x])
            x = parent[x]
        return x

    def union(a: int, b: int):
        ra, rb = find(a), find(b)
        if ra != rb:
            parent[ra] = rb

    # Build connected components
    for row in df_pairs.select(
        COL_MESSAGE_SURROGATE_ID_A, COL_MESSAGE_SURROGATE_ID_B
    ).iter_rows():
        msg_a, msg_b = row
        parent.setdefault(msg_a, msg_a)
        parent.setdefault(msg_b, msg_b)
        union(msg_a, msg_b)

    # Assign cluster IDs
    cluster_map: dict[int, int] = {}
    next_cluster = 0
    results = []
    for msg_id in sorted(parent.keys()):
        root = find(msg_id)
        if root not in cluster_map:
            cluster_map[root] = next_cluster
            next_cluster += 1
        results.append(
            {COL_CLUSTER_ID: cluster_map[root], COL_MESSAGE_SURROGATE_ID: msg_id}
        )

    return pl.DataFrame(results)


def main(context: SecondaryAnalyzerContext):
    # Get parameters with defaults from interface definition
    threshold_pct = _get_param_default(PARAM_SIMILARITY_THRESHOLD) or 50
    cross_author_only = _get_param_default(PARAM_CROSS_AUTHOR_ONLY)
    if cross_author_only is None:
        cross_author_only = True
    threshold = threshold_pct / 100

    # Load primary analyzer outputs
    df_msg_ngrams = pl.read_parquet(
        context.base.table(OUTPUT_MESSAGE_NGRAMS).parquet_path
    )
    df_messages = pl.read_parquet(context.base.table(OUTPUT_MESSAGE).parquet_path)

    with ProgressReporter("Computing pairwise similarity") as progress:
        df_pairs = _compute_jaccard_pairs(df_msg_ngrams, threshold, progress.update)

    if cross_author_only and df_pairs.height > 0:
        with ProgressReporter("Filtering cross-author pairs"):
            # Join author info for both messages
            author_lookup = df_messages.select(COL_MESSAGE_SURROGATE_ID, COL_AUTHOR_ID)
            df_pairs = (
                df_pairs.join(
                    author_lookup,
                    left_on=COL_MESSAGE_SURROGATE_ID_A,
                    right_on=COL_MESSAGE_SURROGATE_ID,
                )
                .rename({COL_AUTHOR_ID: COL_AUTHOR_ID_A})
                .join(
                    author_lookup,
                    left_on=COL_MESSAGE_SURROGATE_ID_B,
                    right_on=COL_MESSAGE_SURROGATE_ID,
                )
                .rename({COL_AUTHOR_ID: COL_AUTHOR_ID_B})
                .filter(pl.col(COL_AUTHOR_ID_A) != pl.col(COL_AUTHOR_ID_B))
            )
    elif df_pairs.height > 0:
        # Still need author columns for the output
        author_lookup = df_messages.select(COL_MESSAGE_SURROGATE_ID, COL_AUTHOR_ID)
        df_pairs = (
            df_pairs.join(
                author_lookup,
                left_on=COL_MESSAGE_SURROGATE_ID_A,
                right_on=COL_MESSAGE_SURROGATE_ID,
            )
            .rename({COL_AUTHOR_ID: COL_AUTHOR_ID_A})
            .join(
                author_lookup,
                left_on=COL_MESSAGE_SURROGATE_ID_B,
                right_on=COL_MESSAGE_SURROGATE_ID,
            )
            .rename({COL_AUTHOR_ID: COL_AUTHOR_ID_B})
        )

    # Add text columns for the pairs output
    with ProgressReporter("Writing copypasta pairs"):
        text_lookup = df_messages.select(COL_MESSAGE_SURROGATE_ID, COL_MESSAGE_TEXT)
        if df_pairs.height > 0:
            df_pairs_output = (
                df_pairs.join(
                    text_lookup,
                    left_on=COL_MESSAGE_SURROGATE_ID_A,
                    right_on=COL_MESSAGE_SURROGATE_ID,
                )
                .rename({COL_MESSAGE_TEXT: COL_TEXT_A})
                .join(
                    text_lookup,
                    left_on=COL_MESSAGE_SURROGATE_ID_B,
                    right_on=COL_MESSAGE_SURROGATE_ID,
                )
                .rename({COL_MESSAGE_TEXT: COL_TEXT_B})
                .select(
                    COL_MESSAGE_SURROGATE_ID_A,
                    COL_MESSAGE_SURROGATE_ID_B,
                    COL_AUTHOR_ID_A,
                    COL_AUTHOR_ID_B,
                    COL_JACCARD_SIMILARITY,
                    COL_SHARED_NGRAM_COUNT,
                    COL_TEXT_A,
                    COL_TEXT_B,
                )
                .sort(COL_JACCARD_SIMILARITY, descending=True)
            )
        else:
            df_pairs_output = pl.DataFrame(
                schema={
                    COL_MESSAGE_SURROGATE_ID_A: pl.Int64,
                    COL_MESSAGE_SURROGATE_ID_B: pl.Int64,
                    COL_AUTHOR_ID_A: pl.Utf8,
                    COL_AUTHOR_ID_B: pl.Utf8,
                    COL_JACCARD_SIMILARITY: pl.Float64,
                    COL_SHARED_NGRAM_COUNT: pl.UInt32,
                    COL_TEXT_A: pl.Utf8,
                    COL_TEXT_B: pl.Utf8,
                }
            )
        df_pairs_output.write_parquet(
            context.output(OUTPUT_COPYPASTA_PAIRS).parquet_path
        )

    # Compute clusters
    with ProgressReporter("Computing copypasta clusters"):
        df_clusters = _assign_clusters(df_pairs)
        if df_clusters.height > 0:
            df_clusters_output = df_clusters.join(
                df_messages.select(
                    COL_MESSAGE_SURROGATE_ID, COL_AUTHOR_ID, COL_MESSAGE_TEXT
                ),
                on=COL_MESSAGE_SURROGATE_ID,
            ).select(
                COL_CLUSTER_ID,
                COL_MESSAGE_SURROGATE_ID,
                COL_AUTHOR_ID,
                COL_MESSAGE_TEXT,
            )
        else:
            df_clusters_output = pl.DataFrame(
                schema={
                    COL_CLUSTER_ID: pl.Int64,
                    COL_MESSAGE_SURROGATE_ID: pl.Int64,
                    COL_AUTHOR_ID: pl.Utf8,
                    COL_MESSAGE_TEXT: pl.Utf8,
                }
            )
        df_clusters_output.write_parquet(
            context.output(OUTPUT_COPYPASTA_CLUSTERS).parquet_path
        )

    # Compute summary statistics
    with ProgressReporter("Writing copypasta summary"):
        if df_pairs.height > 0:
            all_msg_ids = pl.concat(
                [
                    df_pairs.select(pl.col(COL_MESSAGE_SURROGATE_ID_A).alias("msg_id")),
                    df_pairs.select(pl.col(COL_MESSAGE_SURROGATE_ID_B).alias("msg_id")),
                ]
            )
            all_author_ids = pl.concat(
                [
                    df_pairs.select(pl.col(COL_AUTHOR_ID_A).alias("author_id")),
                    df_pairs.select(pl.col(COL_AUTHOR_ID_B).alias("author_id")),
                ]
            )
            df_summary = pl.DataFrame(
                {
                    COL_TOTAL_PAIRS: [df_pairs.height],
                    COL_UNIQUE_MESSAGES: [
                        all_msg_ids.select(pl.col("msg_id").n_unique()).item()
                    ],
                    COL_UNIQUE_AUTHORS: [
                        all_author_ids.select(pl.col("author_id").n_unique()).item()
                    ],
                    COL_AVG_SIMILARITY: [
                        df_pairs.select(pl.col(COL_JACCARD_SIMILARITY).mean()).item()
                    ],
                }
            )
        else:
            df_summary = pl.DataFrame(
                {
                    COL_TOTAL_PAIRS: [0],
                    COL_UNIQUE_MESSAGES: [0],
                    COL_UNIQUE_AUTHORS: [0],
                    COL_AVG_SIMILARITY: [0.0],
                }
            )
        df_summary.write_parquet(context.output(OUTPUT_COPYPASTA_SUMMARY).parquet_path)
