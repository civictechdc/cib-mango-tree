from datetime import time

import polars as pl

from cibmangotree.testing import PolarsTestData, test_primary_analyzer

from .temporal_base.interface import (
    INPUT_COL_TIMESTAMP,
    OUTPUT_COL_POST_COUNT,
    OUTPUT_COL_TIME_INTERVAL_END,
    OUTPUT_COL_TIME_INTERVAL_START,
    OUTPUT_TABLE_INTERVAL_COUNT,
    interface,
)
from .temporal_base.main import main


def test_temporal_analysis():
    test_primary_analyzer(
        interface,
        main,
        input=PolarsTestData(
            pl.DataFrame(
                {
                    INPUT_COL_TIMESTAMP: [
                        "2024-01-01T08:15:00",
                        "2024-01-01T08:45:00",
                        "2024-01-02T08:05:00",
                        "2024-01-01T14:30:00",
                    ]
                }
            ).with_columns(pl.col(INPUT_COL_TIMESTAMP).str.to_datetime())
        ),
        outputs={
            OUTPUT_TABLE_INTERVAL_COUNT: PolarsTestData(
                pl.DataFrame(
                    {
                        OUTPUT_COL_POST_COUNT: [3, 1],
                        OUTPUT_COL_TIME_INTERVAL_START: [
                            time(8, 0),
                            time(14, 0),
                        ],
                        OUTPUT_COL_TIME_INTERVAL_END: [
                            time(9, 0),
                            time(15, 0),
                        ],
                    }
                )
            )
        },
    )
