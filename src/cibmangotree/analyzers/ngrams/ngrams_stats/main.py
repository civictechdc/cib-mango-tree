import polars as pl
import pyarrow as pa
import pyarrow.parquet as pq

from cibmangotree.analyzer_interface.context import (
    NullProgressReporter,
    SecondaryAnalyzerContext,
)

from ..ngrams_base.interface import (
    COL_AUTHOR_ID,
    COL_MESSAGE_SURROGATE_ID,
    COL_MESSAGE_TEXT,
    COL_MESSAGE_TIMESTAMP,
    COL_NGRAM_ID,
    COL_NGRAM_LENGTH,
    COL_NGRAM_WORDS,
    OUTPUT_MESSAGE,
    OUTPUT_MESSAGE_NGRAMS,
    OUTPUT_NGRAM_DEFS,
)
from .interface import (
    COL_NGRAM_DISTINCT_POSTER_COUNT,
    COL_NGRAM_REPS_PER_USER,
    COL_NGRAM_TOTAL_REPS,
    OUTPUT_NGRAM_FULL,
    OUTPUT_NGRAM_STATS,
)


def _compute_ngram_statistics(
    df_message_ngrams: pl.DataFrame, df_messages: pl.DataFrame
) -> pl.DataFrame:
    """
    Compute basic statistics for each n-gram.

    Args:
        df_message_ngrams: DataFrame with message_surrogate_id and ngram_id
        df_messages: DataFrame with message_surrogate_id and user_id

    Returns:
        DataFrame with columns [ngram_id, ngram_total_reps, ngram_distinct_poster_count]
        Filters out n-grams with only 1 repetition.
    """
    dict_authors_by_message = {
        row[COL_MESSAGE_SURROGATE_ID]: row[COL_AUTHOR_ID]
        for row in df_messages.iter_rows(named=True)
    }

    return (
        df_message_ngrams.group_by(COL_NGRAM_ID)
        .agg(
            pl.len().alias(COL_NGRAM_TOTAL_REPS),  # count nr. times ngram detected
            pl.col(COL_MESSAGE_SURROGATE_ID)
            .replace_strict(dict_authors_by_message)
            .n_unique()
            .alias(COL_NGRAM_DISTINCT_POSTER_COUNT),
        )
        .filter(pl.col(COL_NGRAM_TOTAL_REPS) > 1)
    )


def _create_summary_table(
    df_ngrams: pl.DataFrame, df_ngram_stats: pl.DataFrame
) -> pl.DataFrame:
    """
    Join n-gram definitions with statistics and sort by frequency.

    Args:
        df_ngrams: DataFrame with ngram_id, ngram_words, ngram_length
        df_ngram_stats: DataFrame with ngram_id, ngram_total_reps, ngram_distinct_poster_count

    Returns:
        Joined and sorted DataFrame
    """
    # `words` is the final sort key purely as a tiebreaker: the three statistical keys
    # tie frequently, and without a total ordering the row order of this output (and
    # so of the parquet written from it) varies between runs on identical input.
    return df_ngrams.join(df_ngram_stats, on=COL_NGRAM_ID, how="inner").sort(
        [
            COL_NGRAM_LENGTH,
            COL_NGRAM_TOTAL_REPS,
            COL_NGRAM_DISTINCT_POSTER_COUNT,
            COL_NGRAM_WORDS,
        ],
        descending=[True, True, True, False],
    )


def _create_full_report_slice(
    df_ngram_summary_slice: pl.DataFrame,
    df_message_ngrams: pl.DataFrame,
    df_messages: pl.DataFrame,
) -> pl.DataFrame:
    """
    Create detailed report for a slice of n-grams with message details.

    Args:
        df_ngram_summary_slice: Slice of summary DataFrame
        df_message_ngrams: DataFrame with message_surrogate_id and ngram_id
        df_messages: DataFrame with message details

    Returns:
        Detailed report DataFrame with per-user repetition counts, sorted
    """
    # The report does not carry message_text, so drop before the join rather
    # than fanning out and duplicating across many rows
    df_messages_meta = (
        df_messages.drop(COL_MESSAGE_TEXT)
        if COL_MESSAGE_TEXT in df_messages.columns
        else df_messages
    )

    return (
        (
            df_ngram_summary_slice.join(df_message_ngrams, on=COL_NGRAM_ID).join(
                df_messages_meta, on=COL_MESSAGE_SURROGATE_ID
            )
        )
        # count how many times a user posted distint ngrams
        .with_columns(
            pl.len()
            .over([COL_NGRAM_ID, COL_AUTHOR_ID])
            .alias(COL_NGRAM_REPS_PER_USER)
            .cast(pl.Int32)
        )
        .select(
            [
                COL_NGRAM_ID,
                COL_NGRAM_LENGTH,
                COL_NGRAM_WORDS,
                COL_NGRAM_TOTAL_REPS,
                COL_NGRAM_DISTINCT_POSTER_COUNT,
                COL_AUTHOR_ID,
                COL_NGRAM_REPS_PER_USER,
                COL_MESSAGE_SURROGATE_ID,
                COL_MESSAGE_TIMESTAMP,
            ]
        )
        .sort(
            [
                COL_NGRAM_LENGTH,
                COL_NGRAM_TOTAL_REPS,
                COL_NGRAM_DISTINCT_POSTER_COUNT,
                COL_NGRAM_WORDS,
                COL_NGRAM_REPS_PER_USER,
                COL_AUTHOR_ID,
                COL_MESSAGE_SURROGATE_ID,
            ],
            descending=[True, True, True, False, True, False, False],
        )
    )


# Target number of report rows to materialize at once. Each n-gram contributes
# exactly `total_reps` rows, and every row carries a full copy of its message text,
# so this is the knob that bounds peak memory while writing the full report.

# How many rows we aim to materialize at once. Bounds peak memory when writing the report
REPORT_ROWS_PER_SLICE = 100_000


def _report_slice_row_counts(df_ngram_summary: pl.DataFrame) -> list[int]:
    """
    Split the summary into consecutive slices of approx. REPORT_ROWS_PER_SLICE
    report rows, returning the number of n-grams in each slice.

    Sizing slices by n-gram *count* (rows // mean reps) has a pathological case
    on large datasets with large n-gram counts, as total_reps is power-law
    distributed and we can end up producing slices 100x larger than intended.
    By budgeting on the cumulative total_reps, we keep slice sizes much closer
    to target.

    An n-gram whose own total_reps exceeds the budget still gets its own slice,
    since we can't currently split it up further.
    """
    if df_ngram_summary.height == 0:
        return []

    return (
        df_ngram_summary.select(
            (
                (pl.col(COL_NGRAM_TOTAL_REPS).cum_sum() - 1) // REPORT_ROWS_PER_SLICE
            ).alias("_slice")
        )
        .group_by("_slice", maintain_order=True)
        .len()["len"]
        .to_list()
    )


def main(context: SecondaryAnalyzerContext):
    progress = context.progress_reporter or (lambda name: NullProgressReporter(name))

    df_message_ngrams = pl.read_parquet(
        context.base.table(OUTPUT_MESSAGE_NGRAMS).parquet_path
    )
    df_ngrams = pl.read_parquet(context.base.table(OUTPUT_NGRAM_DEFS).parquet_path)
    df_messages = pl.read_parquet(context.base.table(OUTPUT_MESSAGE).parquet_path)

    with progress("Computing ngram statistics"):
        df_ngram_stats = _compute_ngram_statistics(df_message_ngrams, df_messages)

    with progress("Creating the summary table"):
        df_ngram_summary = _create_summary_table(df_ngrams, df_ngram_stats)
        df_ngram_summary.write_parquet(context.output(OUTPUT_NGRAM_STATS).parquet_path)

    df_messages_schema = df_messages.to_arrow().schema
    df_message_ngrams_schema = df_message_ngrams.to_arrow().schema
    df_ngram_summary_schema = df_ngram_summary.to_arrow().schema

    report_slice_row_counts = _report_slice_row_counts(df_ngram_summary)

    with progress("Writing full report") as reporter:
        with pq.ParquetWriter(
            context.output(OUTPUT_NGRAM_FULL).parquet_path,
            schema=pa.schema(
                [
                    df_message_ngrams_schema.field(COL_NGRAM_ID),
                    df_ngram_summary_schema.field(COL_NGRAM_LENGTH),
                    df_ngram_summary_schema.field(COL_NGRAM_WORDS),
                    df_ngram_summary_schema.field(COL_NGRAM_TOTAL_REPS),
                    df_ngram_summary_schema.field(COL_NGRAM_DISTINCT_POSTER_COUNT),
                    df_messages_schema.field(COL_AUTHOR_ID),
                    pa.field(COL_NGRAM_REPS_PER_USER, pa.int32()),
                    df_messages_schema.field(COL_MESSAGE_SURROGATE_ID),
                    # message_text omitted on purpose and re-joined on export
                    df_messages_schema.field(COL_MESSAGE_TIMESTAMP),
                ]
            ),
            # unlike polars, which defaults to zstd, pyarrow defaults to snappy,
            # which isn't as effective at compression, switching it on manually,
            # since this is the largest file we produce and benefits from
            # superior compression
            compression="zstd",
        ) as writer:
            report_total_processed = 0
            for slice_height in report_slice_row_counts:
                df_ngram_summary_slice = df_ngram_summary.slice(
                    report_total_processed, slice_height
                )
                print(
                    f"Writing report "
                    f"{report_total_processed}/{df_ngram_summary.height}",
                    end="\r",
                )
                report_total_processed += slice_height

                df_output = _create_full_report_slice(
                    df_ngram_summary_slice, df_message_ngrams, df_messages
                )

                writer.write_table(df_output.to_arrow())
                reporter.update(report_total_processed / df_ngram_summary.height)
