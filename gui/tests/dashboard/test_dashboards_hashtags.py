"""Tests for the hashtags dashboard: chart payload format and click-handler indexing."""

from datetime import datetime
from unittest.mock import MagicMock

import polars as pl

from analyzers.hashtags.hashtags_base.interface import (
    OUTPUT_COL_GINI,
    OUTPUT_COL_TIMESPAN,
    PRIMARY_OUTPUT_DATETIME_FORMAT,
)
from gui.dashboards.hashtags.dashboard import HashtagsDashboardPage
from gui.dashboards.hashtags.plots import plot_gini_echart


def test_plot_gini_raw_ts_preserves_seconds() -> None:
    """raw_ts in chart payload must include seconds to match primary output format."""
    df = pl.DataFrame(
        {
            OUTPUT_COL_TIMESPAN: [datetime(2024, 1, 15, 1, 13, 39)],
            OUTPUT_COL_GINI: [0.42],
        }
    )
    option = plot_gini_echart(df)
    raw_ts = option["series"][0]["data"][0]["raw_ts"]
    assert raw_ts == "2024-01-15 01:13:39"


def test_plot_gini_raw_ts_roundtrip() -> None:
    """raw_ts must parse back to the exact same datetime (no precision loss)."""
    original = datetime(2024, 3, 20, 17, 45, 59)
    df = pl.DataFrame(
        {
            OUTPUT_COL_TIMESPAN: [original],
            OUTPUT_COL_GINI: [0.55],
        }
    )
    option = plot_gini_echart(df)
    raw_ts = option["series"][0]["data"][0]["raw_ts"]
    parsed = datetime.strptime(raw_ts, PRIMARY_OUTPUT_DATETIME_FORMAT)
    assert parsed == original


def test_get_raw_data_index_matches_non_round_timestamps(
    gui_session_with_project: MagicMock,
) -> None:
    """_get_raw_data_index must find correct index for datetimes with seconds."""
    page = HashtagsDashboardPage(session=gui_session_with_project)
    page._df_primary = pl.DataFrame(
        {
            OUTPUT_COL_TIMESPAN: [
                datetime(2024, 1, 15, 1, 13, 39),
                datetime(2024, 1, 15, 13, 27, 51),
                datetime(2024, 1, 16, 8, 0, 0),
            ],
            OUTPUT_COL_GINI: [0.42, 0.38, 0.51],
        }
    )
    raw_ts = "2024-01-15 01:13:39"
    assert page._get_raw_data_index(raw_ts) == 0

    raw_ts = "2024-01-15 13:27:51"
    assert page._get_raw_data_index(raw_ts) == 1

    raw_ts = "2024-01-16 08:00:00"
    assert page._get_raw_data_index(raw_ts) == 2


def test_get_raw_data_index_returns_none_for_mismatch(
    gui_session_with_project: MagicMock,
) -> None:
    """_get_raw_data_index must return None when raw_ts does not match any row."""
    page = HashtagsDashboardPage(session=gui_session_with_project)
    page._df_primary = pl.DataFrame(
        {
            OUTPUT_COL_TIMESPAN: [datetime(2024, 1, 15, 1, 13, 39)],
            OUTPUT_COL_GINI: [0.42],
        }
    )
    assert page._get_raw_data_index("2024-01-15 01:13:00") is None
    assert page._get_raw_data_index("2024-01-15 01:14:39") is None
    assert page._get_raw_data_index("2024-01-16 01:13:39") is None
