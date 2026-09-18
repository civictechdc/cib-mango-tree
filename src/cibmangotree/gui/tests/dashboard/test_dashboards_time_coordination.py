"""Behavior tests for gui.dashboards.time_coordination.TimeCoordinationDashboardPage."""

import asyncio
from unittest.mock import AsyncMock, MagicMock, patch

import polars as pl
from nicegui import ui
from nicegui.testing import User

from cibmangotree.analyzers.time_coordination.interface import (
    OUTPUT_COL_FREQ,
    OUTPUT_COL_USER1,
    OUTPUT_COL_USER2,
)
from cibmangotree.gui.dashboards.base_dashboard import BaseDashboardPage
from cibmangotree.gui.dashboards.time_coordination import TimeCoordinationDashboardPage
from cibmangotree.gui.dashboards.time_coordination.data import load_coordinated_pairs
from cibmangotree.gui.dashboards.time_coordination.plots import plot_top_pairs_echart
from cibmangotree.gui.session import GuiSession


def test_time_coordination_dashboard_extends_base_dashboard() -> None:
    assert issubclass(TimeCoordinationDashboardPage, BaseDashboardPage)


def test_load_coordinated_pairs_drops_self_pairs_and_duplicate_direction(
    tmp_path,
) -> None:
    """
    The raw analyzer output includes a self-pair for every user and both
    directions of every real pair with the same count; only one row per
    real pair should survive.
    """
    raw = pl.DataFrame(
        {
            OUTPUT_COL_USER1: ["alice", "bob", "alice", "bob", "alice", "carol"],
            OUTPUT_COL_USER2: ["alice", "bob", "bob", "alice", "carol", "alice"],
            OUTPUT_COL_FREQ: [4, 2, 3, 3, 1, 1],
        }
    )
    path = tmp_path / "cooccurrence_frequency.parquet"
    raw.write_parquet(path)

    dashboard = MagicMock()
    dashboard.get_primary_output_parquet_path.return_value = str(path)

    result = load_coordinated_pairs(dashboard)

    assert result is not None
    pairs = set(
        result.select(OUTPUT_COL_USER1, OUTPUT_COL_USER2, OUTPUT_COL_FREQ).iter_rows()
    )
    assert pairs == {("alice", "bob", 3), ("alice", "carol", 1)}


def test_load_coordinated_pairs_returns_none_without_output() -> None:
    dashboard = MagicMock()
    dashboard.get_primary_output_parquet_path.return_value = None

    assert load_coordinated_pairs(dashboard) is None


def test_plot_top_pairs_orders_highest_count_last_for_horizontal_bar() -> None:
    df = pl.DataFrame(
        {
            OUTPUT_COL_USER1: ["alice", "bob"],
            OUTPUT_COL_USER2: ["carol", "dana"],
            OUTPUT_COL_FREQ: [10, 5],
        }
    )
    option = plot_top_pairs_echart(df)

    # Reversed so the highest count renders at the top of the chart.
    assert option["yAxis"]["data"] == ["bob & dana", "alice & carol"]
    assert option["series"][0]["data"] == [5, 10]


async def test_dashboard_recovers_when_cpu_bound_returns_none(
    user: User, gui_session_with_project: GuiSession, tmp_path
) -> None:
    """
    Regression test: run.cpu_bound() returns None (rather than raising) if
    its task is cancelled or the app is shutting down. The dashboard must
    fall back to computing the chart synchronously instead of crashing when
    it tries to use a None result.
    """
    df = pl.DataFrame(
        {
            OUTPUT_COL_USER1: ["alice"],
            OUTPUT_COL_USER2: ["bob"],
            OUTPUT_COL_FREQ: [3],
        }
    )
    path = tmp_path / "cooc.parquet"
    df.write_parquet(path)

    gui_session_with_project.selected_analyzer_name = "Time Coordination"
    gui_session_with_project.current_analysis = object()
    gui_session_with_project.app.context.storage.get_primary_output_parquet_path.return_value = str(
        path
    )

    holder = {}

    @ui.page("/tc-none")
    def page() -> None:
        dashboard = TimeCoordinationDashboardPage(session=gui_session_with_project)
        holder["dashboard"] = dashboard
        dashboard.render()

    with patch(
        "cibmangotree.gui.dashboards.time_coordination.dashboard.run.cpu_bound",
        new_callable=AsyncMock,
        return_value=None,
    ):
        await user.open("/tc-none")
        await asyncio.sleep(0.5)

    chart = holder["dashboard"]._chart
    assert chart is not None
    assert chart.options["title"]["text"] == "Most time-coordinated user pairs"
    assert chart.options["series"][0]["data"] == [3]


async def test_grid_caps_rows_sent_to_the_browser(
    user: User, gui_session_with_project: GuiSession, tmp_path
) -> None:
    """
    Regression test: a dataset with even a few thousand active users can
    produce tens of thousands of coordinated pairs. Sending all of them to
    the browser in one grid update is a multi-megabyte websocket payload
    that can stall or crash the client mid-render (this was the actual
    cause of the dashboard flashing content then reverting to "loading" -
    an uncaught client-side failure tears down the page mid-update).
    """
    from cibmangotree.gui.dashboards.time_coordination.dashboard import MAX_GRID_ROWS

    n_pairs = MAX_GRID_ROWS + 50
    df = pl.DataFrame(
        {
            OUTPUT_COL_USER1: [f"user_{i}" for i in range(n_pairs)],
            OUTPUT_COL_USER2: [f"user_{i}_b" for i in range(n_pairs)],
            OUTPUT_COL_FREQ: list(range(n_pairs, 0, -1)),
        }
    )
    path = tmp_path / "cooc.parquet"
    df.write_parquet(path)

    gui_session_with_project.selected_analyzer_name = "Time Coordination"
    gui_session_with_project.current_analysis = object()
    gui_session_with_project.app.context.storage.get_primary_output_parquet_path.return_value = str(
        path
    )

    holder = {}

    @ui.page("/tc-cap")
    def page() -> None:
        dashboard = TimeCoordinationDashboardPage(session=gui_session_with_project)
        holder["dashboard"] = dashboard
        dashboard.render()

    await user.open("/tc-cap")
    dashboard = holder["dashboard"]
    for _ in range(20):
        await asyncio.sleep(0.2)
        if dashboard._grid.options["rowData"]:
            break

    assert len(dashboard._grid.options["rowData"]) == MAX_GRID_ROWS
    assert dashboard._grid_note.text == (
        f"Showing the top {MAX_GRID_ROWS} of {n_pairs} coordinated pairs by "
        "co-occurrence count."
    )
