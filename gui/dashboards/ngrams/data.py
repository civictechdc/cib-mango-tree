"""
Data loading and transformation helpers for the n-grams dashboard.

Provides functions to:
- Build summary and detail column definitions for AG-Grid
- Filter n-gram stats by text search
"""

import polars as pl

from analyzers.ngrams.ngrams_stats.interface import (
    COL_AUTHOR_ID,
    COL_MESSAGE_TEXT,
    COL_MESSAGE_TIMESTAMP,
    COL_NGRAM_DISTINCT_POSTER_COUNT,
    COL_NGRAM_TOTAL_REPS,
    COL_NGRAM_WORDS,
)

_SUMMARY_RENAME = {
    COL_NGRAM_WORDS: "N-gram content",
    COL_NGRAM_TOTAL_REPS: "Total repetitions",
    COL_NGRAM_DISTINCT_POSTER_COUNT: "Unique posters",
}

_DETAIL_RENAME = {
    COL_AUTHOR_ID: "User ID",
    COL_NGRAM_WORDS: "N-gram content",
    COL_MESSAGE_TEXT: "Post content",
    COL_MESSAGE_TIMESTAMP: "Timestamp",
}


def make_summary_columns(df: pl.DataFrame) -> pl.DataFrame:
    return (
        df.select(
            [
                COL_NGRAM_WORDS,
                COL_NGRAM_TOTAL_REPS,
                COL_NGRAM_DISTINCT_POSTER_COUNT,
            ]
        )
        .sort(COL_NGRAM_TOTAL_REPS, descending=True)
        .rename(_SUMMARY_RENAME)
    )


def make_detail_columns(df: pl.DataFrame) -> pl.DataFrame:
    return (
        df.select(
            [
                COL_AUTHOR_ID,
                COL_NGRAM_WORDS,
                COL_MESSAGE_TEXT,
                COL_MESSAGE_TIMESTAMP,
            ]
        )
        .with_columns(pl.col(COL_MESSAGE_TIMESTAMP).dt.strftime("%B %d, %Y %I:%M %p"))
        .rename(_DETAIL_RENAME)
    )


def filter_ngrams_by_text(df: pl.DataFrame, text: str) -> pl.DataFrame:
    return df.filter(pl.col(COL_NGRAM_WORDS).str.contains(f"(?i){text}"))
