import os
import tempfile

import polars as pl

from cibmangotree.testing.context import (
    TestPrimaryAnalyzerContext as _TestPrimaryAnalyzerContext,
)

from .interface import (
    COL_TIMESTAMP,
    COL_USER_ID,
    OUTPUT_COL_FREQ,
    OUTPUT_COL_USER1,
    OUTPUT_COL_USER2,
    OUTPUT_TABLE,
)
from .main import main


def test_time_coordination_analysis():
    # alice and bob post 5 minutes apart, so they co-occur once in the
    # 15-minute sliding window; alice and carol post a minute apart, over
    # 35 minutes later, so they form a separate coordinated pair. A user
    # always co-occurs with themselves in their own windows too.
    #
    # The analyzer's group_by does not guarantee row order for ties, so this
    # compares rows as an order-independent set rather than using
    # `testing.test_primary_analyzer` (which requires exact row order).
    input_df = pl.DataFrame(
        {
            COL_USER_ID: ["alice", "bob", "alice", "carol"],
            COL_TIMESTAMP: [
                "2024-01-01T08:00:00",
                "2024-01-01T08:05:00",
                "2024-01-01T08:40:00",
                "2024-01-01T08:41:00",
            ],
        }
    ).with_columns(pl.col(COL_TIMESTAMP).str.to_datetime())

    with tempfile.TemporaryDirectory() as temp_dir:
        with tempfile.TemporaryDirectory() as input_dir:
            with tempfile.TemporaryDirectory() as output_dir:
                input_path = os.path.join(input_dir, "input.parquet")
                input_df.write_parquet(input_path)

                context = _TestPrimaryAnalyzerContext(
                    temp_dir=temp_dir,
                    input_parquet_path=input_path,
                    param_values={},
                    output_parquet_root_path=output_dir,
                )
                main(context)

                actual = pl.read_parquet(context.output_path(OUTPUT_TABLE))

    expected_pairs = {
        ("alice", "alice", 4),
        ("carol", "carol", 3),
        ("alice", "carol", 3),
        ("carol", "alice", 3),
        ("bob", "bob", 2),
        ("bob", "alice", 1),
        ("alice", "bob", 1),
    }
    actual_pairs = set(
        actual.select(OUTPUT_COL_USER1, OUTPUT_COL_USER2, OUTPUT_COL_FREQ).iter_rows()
    )

    assert actual_pairs == expected_pairs
