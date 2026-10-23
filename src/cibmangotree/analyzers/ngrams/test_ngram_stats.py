from pathlib import Path

import polars as pl
import pytest

from cibmangotree.storage import Storage
from cibmangotree.testing import ParquetTestData, test_secondary_analyzer

from .ngrams_base.interface import (
    COL_MESSAGE_SURROGATE_ID,
    COL_MESSAGE_TEXT,
    OUTPUT_MESSAGE,
    OUTPUT_MESSAGE_NGRAMS,
    OUTPUT_NGRAM_DEFS,
)
from .ngrams_stats.interface import OUTPUT_NGRAM_FULL, OUTPUT_NGRAM_STATS, interface
from .ngrams_stats.main import _compute_ngram_statistics, main
from .test_data import test_data_dir


# Fixtures for unit testing
@pytest.fixture
def df_message_ngrams():
    """Load message_ngrams (output from ngrams_base)"""
    return pl.read_parquet(Path(test_data_dir, "message_ngrams.parquet"))


@pytest.fixture
def df_ngrams():
    """Load n-gram definitions (output from ngrams_base)"""
    return pl.read_parquet(Path(test_data_dir, "ngrams.parquet"))


@pytest.fixture
def df_messages():
    """Load message authors table (output from ngrams_base)"""
    return pl.read_parquet(Path(test_data_dir, "message_authors.parquet"))


# Unit tests for extracted functions
def test_compute_ngram_statistics(df_message_ngrams, df_messages, df_ngrams):
    """Test basic n-gram statistics computation"""
    result = _compute_ngram_statistics(df_message_ngrams, df_messages)

    # Check all n-grams have total_reps > 1
    assert result["total_reps"].min() > 1, "Single-occurrence n-grams not filtered"

    # The repeated 4-grams each occur in msg_002 and msg_003. Shorter subspans
    # of those phrases are not reported.
    assert result["total_reps"].max() == 2
    assert result["distinct_posters"].max() == 2, "Wrong number of distinct posters"
    assert df_ngrams.filter(pl.col("words") == "go go go").height == 0
    assert df_ngrams.filter(pl.col("words") == "it's very bad").height == 0

    # Verify we have the expected columns
    assert "ngram_id" in result.columns
    assert "total_reps" in result.columns
    assert "distinct_posters" in result.columns

    for words in ("go go go it's", "go go it's very", "go it's very bad"):
        ngram_id = df_ngrams.filter(pl.col("words") == words)[0, "ngram_id"]
        stats = result.filter(pl.col("ngram_id") == ngram_id)
        assert stats.height == 1, f"{words!r} should be in stats"
        assert stats[0, "total_reps"] == 2, f"{words!r} should appear in 2 messages"
        assert stats[0, "distinct_posters"] == 2


# Integration test
def test_ngram_stats():
    # You use this test function.
    test_secondary_analyzer(
        interface,
        main,
        primary_outputs={
            OUTPUT_MESSAGE_NGRAMS: ParquetTestData(
                filepath=str(Path(test_data_dir, OUTPUT_MESSAGE_NGRAMS + ".parquet"))
            ),
            OUTPUT_NGRAM_DEFS: ParquetTestData(
                filepath=str(Path(test_data_dir, OUTPUT_NGRAM_DEFS + ".parquet"))
            ),
            OUTPUT_MESSAGE: ParquetTestData(
                filepath=str(Path(test_data_dir, OUTPUT_MESSAGE + ".parquet"))
            ),
        },
        expected_outputs={
            OUTPUT_NGRAM_STATS: ParquetTestData(
                str(Path(test_data_dir, OUTPUT_NGRAM_STATS + ".parquet"))
            ),
            OUTPUT_NGRAM_FULL: ParquetTestData(
                str(Path(test_data_dir, OUTPUT_NGRAM_FULL + ".parquet"))
            ),
        },
    )


def test_ngram_full_omits_message_text():
    """The full report must not carry post text; it is re-joined on export."""
    df = pl.read_parquet(Path(test_data_dir, OUTPUT_NGRAM_FULL + ".parquet"))
    assert COL_MESSAGE_TEXT not in df.columns
    assert (
        COL_MESSAGE_SURROGATE_ID in df.columns
    ), "join key for denormalization is missing"


def test_ngram_full_denormalizes_message_text_for_export():
    """
    Exporting the full report must restore post text, in its declared position, with
    the value belonging to each row's message.
    """
    spec = next(o for o in interface.outputs if o.id == OUTPUT_NGRAM_FULL)
    assert spec.denormalize is not None, "ngram_full should declare its omitted columns"

    narrow = pl.scan_parquet(Path(test_data_dir, OUTPUT_NGRAM_FULL + ".parquet"))
    source_path = str(Path(test_data_dir, OUTPUT_MESSAGE + ".parquet"))
    denormalized = Storage._denormalize(narrow, spec, source_path).collect()

    assert COL_MESSAGE_TEXT in denormalized.columns
    assert (
        denormalized.height == narrow.collect().height
    ), "denormalization must not change row count"

    # placed immediately after the column it is declared to follow
    cols = denormalized.columns
    assert cols.index(COL_MESSAGE_TEXT) == cols.index(spec.denormalize.insert_after) + 1

    # every row carries the text of its own message
    messages = pl.read_parquet(source_path).select(
        COL_MESSAGE_SURROGATE_ID, COL_MESSAGE_TEXT
    )
    expected = denormalized.select(COL_MESSAGE_SURROGATE_ID).join(
        messages, on=COL_MESSAGE_SURROGATE_ID, how="left"
    )
    assert (
        denormalized[COL_MESSAGE_TEXT].to_list() == expected[COL_MESSAGE_TEXT].to_list()
    )


def test_denormalization_is_idempotent_and_degrades_safely():
    """Denormalizing an already-wide frame, or with no source available, is a no-op."""
    spec = next(o for o in interface.outputs if o.id == OUTPUT_NGRAM_FULL)
    narrow = pl.scan_parquet(Path(test_data_dir, OUTPUT_NGRAM_FULL + ".parquet"))
    source_path = str(Path(test_data_dir, OUTPUT_MESSAGE + ".parquet"))

    denormalized = Storage._denormalize(narrow, spec, source_path).collect()
    again = Storage._denormalize(denormalized.lazy(), spec, source_path).collect()
    assert again.equals(denormalized)

    # a missing source must leave the frame untouched rather than raise
    assert Storage._denormalize(narrow, spec, None).collect().equals(narrow.collect())
