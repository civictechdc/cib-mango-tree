"""
Generate synthetic test data for ngrams analyzer tests.

This script creates minimal, human-auditable test datasets that cover:
- Cross-post repetition statistics
- Multi-user coordination patterns
- Single-user behavior
- Within-message deduplication

Run this script to regenerate test data when schemas change as follows:

```
python _generate_test_data.py # writes 'ngrams_test_input.csv' in the same folder
```
"""

from pathlib import Path

import polars as pl

# Column names from the interface
TEST_COL_AUTHOR_ID = "user_id"
TEST_COL_MESSAGE_ID = "message_id"
TEST_COL_MESSAGE_TEXT = "message_text"
TEST_COL_MESSAGE_TIMESTAMP = "timestamp"

# Test data directory
TEST_DATA_DIR = Path(__file__).parent


def _generate_test_input_data():
    """Generate comprehensive test data for ngrams analyzer."""

    # Input dataset: 5 messages, 2 users
    # Designed to test:
    # - "go go go": 3-gram appearing across 2 distinct users
    # - "it's very bad:" 3-gram appearing across 2 distinct users and repeats within message once
    # - other 3-grams (e.g. "later it's very", "go it's very") only occur once and should be filtered out

    df_input = pl.DataFrame(
        {
            TEST_COL_AUTHOR_ID: [
                "alice",
                "bob",
                "alice",
            ],
            TEST_COL_MESSAGE_ID: [
                "msg_001",
                "msg_002",
                "msg_003",
            ],
            TEST_COL_MESSAGE_TEXT: [
                "go go go now",  # alice: "go go go" (appears 3x total)
                "go go go it's very bad",  # bob: "go go go"
                "go go go it's very bad it's very bad",  # alice: "go go go", "it's very bad", "it's very bad"
            ],
            TEST_COL_MESSAGE_TIMESTAMP: [
                "2024-01-01T10:00:00Z",
                "2024-01-01T10:05:00Z",
                "2024-01-01T10:10:00Z",
            ],
        }
    )

    return df_input


def _generate_expected_outputs() -> None:
    """
    Regenerate the expected output parquets by running the analyzers on the input.

    These files are the fixtures the analyzer tests compare against, so only
    regenerate them when the output contract has deliberately changed, and inspect
    the diff before committing.
    """
    # Imported here so generating the input CSV alone does not require the analyzers.
    from cibmangotree.analyzer_interface.context import InputTableReader
    from cibmangotree.preprocessing.series_semantic import (
        datetime_string,
        identifier,
        text_catch_all,
    )
    from cibmangotree.testing.context import (
        TestPrimaryAnalyzerContext,
        TestSecondaryAnalyzerContext,
    )

    from ..ngrams_base.interface import (
        OUTPUT_MESSAGE,
        OUTPUT_MESSAGE_NGRAMS,
        OUTPUT_NGRAM_DEFS,
    )
    from ..ngrams_base.main import main as primary_main
    from ..ngrams_stats.main import main as secondary_main

    semantics = {
        TEST_COL_AUTHOR_ID: identifier,
        TEST_COL_MESSAGE_ID: identifier,
        TEST_COL_MESSAGE_TEXT: text_catch_all,
        TEST_COL_MESSAGE_TIMESTAMP: datetime_string,
    }

    df_input = pl.read_csv(TEST_DATA_DIR / "ngrams_test_input.csv")
    input_parquet = TEST_DATA_DIR / "_input.parquet"
    df_input.select(
        [
            pl.col(name)
            .map_batches(sem.try_convert, return_dtype=sem.return_dtype)
            .alias(name)
            for name, sem in semantics.items()
        ]
    ).write_parquet(input_parquet)

    class _Reader(InputTableReader):
        def __init__(self, parquet_path: str):
            self._parquet_path = parquet_path

        @property
        def parquet_path(self) -> str:
            return self._parquet_path

        def preprocess(self, df: pl.DataFrame) -> pl.DataFrame:
            return df

    class _Ctx(TestPrimaryAnalyzerContext):
        def input(self) -> InputTableReader:
            return _Reader(self.input_parquet_path)

    primary_main(
        _Ctx(
            temp_dir=str(TEST_DATA_DIR),
            input_parquet_path=str(input_parquet),
            output_parquet_root_path=str(TEST_DATA_DIR),
            param_values={"min_n": 3, "max_n": 4},
        )
    )

    secondary_main(
        TestSecondaryAnalyzerContext(
            primary_output_parquet_paths={
                output: str(TEST_DATA_DIR / f"{output}.parquet")
                for output in (OUTPUT_MESSAGE_NGRAMS, OUTPUT_NGRAM_DEFS, OUTPUT_MESSAGE)
            },
            output_parquet_root_path=str(TEST_DATA_DIR),
            primary_param_values={"min_n": 3, "max_n": 4},
        )
    )

    input_parquet.unlink()


if __name__ == "__main__":

    df_input = _generate_test_input_data()

    # Save all files
    df_input.write_csv(TEST_DATA_DIR / "ngrams_test_input.csv")

    _generate_expected_outputs()
