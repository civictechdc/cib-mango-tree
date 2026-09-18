"""Tests for the hashtags dashboard: chart payload format and click-handler indexing."""

from datetime import datetime, timedelta
from unittest.mock import AsyncMock, MagicMock, patch

import polars as pl
from nicegui import ui
from nicegui.testing import User

from cibmangotree.analyzer_interface.params import TimeBinningValue
from cibmangotree.analyzers.hashtags.hashtags_base.interface import (
    OUTPUT_COL_GINI,
    OUTPUT_COL_HASHTAGS,
    OUTPUT_COL_TIMESPAN,
    OUTPUT_COL_USERS,
    PARAM_TIME_WINDOW,
    PRIMARY_OUTPUT_DATETIME_FORMAT,
)
from cibmangotree.gui.dashboards.hashtags.dashboard import HashtagsDashboardPage
from cibmangotree.gui.dashboards.hashtags.plots import plot_gini_echart
from cibmangotree.gui.session import GuiSession


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


def test_get_time_step_falls_back_to_configured_bin_size_with_one_row(
    gui_session_with_project: MagicMock,
) -> None:
    """
    Regression test: with only one row in the primary output, there's no
    second row to infer a bucket duration from, so _get_time_step must fall
    back to the analysis's actually configured time-window parameter instead
    of returning None - otherwise a dataset whose activity all falls into a
    single time bucket could never show tweets for any user.
    """
    page = HashtagsDashboardPage(session=gui_session_with_project)
    page._df_primary = pl.DataFrame(
        {
            OUTPUT_COL_TIMESPAN: [datetime(2024, 1, 15, 1, 0, 0)],
            OUTPUT_COL_GINI: [0.42],
        }
    )
    gui_session_with_project.current_analysis = MagicMock(
        param_values={PARAM_TIME_WINDOW: TimeBinningValue(unit="hour", amount=3)}
    )

    assert page._get_time_step() == timedelta(hours=3)


def test_extract_users_for_hashtag_returns_user_ids_as_strings() -> None:
    """
    Regression test: a numeric user id (e.g. a Twitter/X-style snowflake id)
    can exceed JavaScript's 2^53 safe integer range and get silently rounded
    to a different value when it round-trips through the browser as a JSON
    number. Casting to string before it ever reaches the grid avoids that.
    """
    from cibmangotree.analyzers.hashtags.hashtags_base.interface import (
        SECONDARY_COL_USERS_ALL,
    )
    from cibmangotree.gui.dashboards.hashtags.data import extract_users_for_hashtag

    large_user_id = 1461585538532708356  # exceeds 2**53
    df_secondary = pl.DataFrame(
        {
            OUTPUT_COL_HASHTAGS: ["#travel"],
            SECONDARY_COL_USERS_ALL: [[large_user_id, large_user_id]],
        }
    )

    result = extract_users_for_hashtag(df_secondary, "#travel")

    assert result["User"].dtype == pl.Utf8
    assert result["User"].to_list() == [str(large_user_id)]


def test_filter_tweets_matches_string_user_against_large_numeric_author_id() -> None:
    """
    Regression test: _filter_tweets receives `user` as a string (see
    extract_users_for_hashtag), but the raw author-id column may still be a
    large integer - the comparison must cast both sides to match, not fail
    silently and return zero rows.
    """
    from cibmangotree.analyzers.hashtags.hashtags_base.interface import (
        COL_AUTHOR_ID,
        COL_POST,
        COL_TIME,
    )

    large_user_id = 1461585538532708356
    df_raw = pl.DataFrame(
        {
            COL_AUTHOR_ID: [large_user_id],
            COL_TIME: [datetime(2024, 1, 15, 1, 5, 0)],
            COL_POST: ["hello #travel"],
        }
    )

    result = HashtagsDashboardPage._filter_tweets(
        df_raw,
        str(large_user_id),
        "#travel",
        datetime(2024, 1, 15, 1, 0, 0),
        datetime(2024, 1, 15, 2, 0, 0),
    )

    assert len(result) == 1


async def test_secondary_analysis_recovers_when_cpu_bound_returns_none(
    user: User, gui_session_with_project: GuiSession
) -> None:
    """
    Regression test: run.cpu_bound() returns None (rather than raising) if
    its task is cancelled or the app is shutting down. This is the step
    that populates the hashtag grid feeding the tweet explorer, so if it
    crashes on a None result, the whole drill-down (hashtag -> user ->
    tweets) breaks downstream of this point.
    """
    timewindow = datetime(2024, 1, 15, 1, 0, 0)
    primary_output = pl.DataFrame(
        {
            OUTPUT_COL_TIMESPAN: [timewindow],
            OUTPUT_COL_HASHTAGS: [["#travel", "#food"]],
            OUTPUT_COL_USERS: [["alice", "bob"]],
        }
    )

    holder = {}

    @ui.page("/ht-none")
    def page() -> None:
        dashboard = HashtagsDashboardPage(session=gui_session_with_project)
        holder["dashboard"] = dashboard
        dashboard.render()

    with patch(
        "cibmangotree.gui.dashboards.hashtags.dashboard.run.cpu_bound",
        new_callable=AsyncMock,
        return_value=None,
    ):
        await user.open("/ht-none")

        dashboard = holder["dashboard"]
        dashboard._df_primary = primary_output
        dashboard._selected_timewindow = timewindow
        await dashboard._run_secondary_analysis()

    assert dashboard._df_secondary is not None
    assert not dashboard._df_secondary.is_empty()
