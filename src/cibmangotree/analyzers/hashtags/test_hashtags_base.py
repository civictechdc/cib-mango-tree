import os

import numpy as np
import polars as pl
from analyzer_interface.params import TimeBinningValue
from preprocessing.series_semantic import datetime_string, identifier, text_catch_all
from testing import CsvTestData, JsonTestData, test_primary_analyzer

from .hashtags_base.interface import (
    COL_AUTHOR_ID,
    COL_POST,
    COL_TIME,
    OUTPUT_COL_COUNT,
    OUTPUT_COL_USERS,
    OUTPUT_GINI,
    interface,
)
from .hashtags_base.main import gini, hashtag_analysis, main
from .test_data import test_data_dir

HASHTAGS = [
    "sunset",
    "nature",
    "food",
    "travel",
    "happy",
    "friends",
    "love",
    "family",
    "music",
    "art",
    "photography",
    "fun",
    "smile",
    "weekend",
    "coffee",
    "book",
    "reading",
    "running",
    "fitness",
    "health",
    "cat",
    "dog",
    "bird",
    "fish",
    "lizard",
]


def test_gini():
    test_cases = [
        # a single hashtags is detected
        {
            "data": ["same"] * 1000,
            "expected": 0.0,
            "description": "One single hashtag (no inequality possible)",
        },
        {
            "data": HASHTAGS,
            "expected": 0.0,
            "description": "Perfect equality (all unique)",
        },
        {
            "data": HASHTAGS * 5,
            "expected": 0.0,
            "description": "Perfect equality (all appear 5 times)",
        },
        {
            "data": ["trending"] * 9999 + HASHTAGS,
            "expected": 0.95,  # It goes towards 1
            "description": "Extreme inequality (9999 vs 1 occurrences)",
        },
    ]

    # caculcate gini and compare
    for test_case in test_cases:
        data_series = pl.Series(test_case["data"])

        # Calculate actual Gini coefficient
        actual = gini(data_series)

        assert np.allclose(
            [actual], [test_case["expected"]], rtol=1e-2, atol=1e-2
        ), f"Failed test case: {test_case['description']}"


def test_hashtag_analysis_handles_nulls():
    """Test that hashtag_analysis gracefully handles null timestamps and post content."""
    df = pl.DataFrame(
        {
            COL_AUTHOR_ID: ["user1", "user2", "user3", "user4"],
            COL_TIME: [
                "2025-01-01 00:00:00",
                None,
                "2025-01-01 01:00:00",
                "2025-01-01 02:00:00",
            ],
            COL_POST: ["#hello #world", None, "#hello", ""],
        }
    )

    result = hashtag_analysis(df, every="1h")

    all_users = result[OUTPUT_COL_USERS].explode().unique().to_list()
    assert "user1" in all_users
    assert "user3" in all_users
    assert "user2" not in all_users
    assert "user4" not in all_users

    assert result[OUTPUT_COL_COUNT].sum() == 3


def test_hashtag_analyzer():
    test_primary_analyzer(
        interface,
        main,  #  the analyzer's entry point.
        input=CsvTestData(
            os.path.join(test_data_dir, "hashtag_test_input.csv"),
            semantics={
                COL_AUTHOR_ID: identifier,
                COL_TIME: datetime_string,
                COL_POST: text_catch_all,
            },
        ),
        params={"time_window": TimeBinningValue(unit="hour", amount=12)},
        outputs={
            OUTPUT_GINI: JsonTestData(
                os.path.join(test_data_dir, "hashtag_test_output.json")
            )
        },
    )
