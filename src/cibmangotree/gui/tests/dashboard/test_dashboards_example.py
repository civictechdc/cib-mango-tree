"""Behavior tests for gui.dashboards.example.ExampleDashboardPage."""

import asyncio
from unittest.mock import AsyncMock, patch

import polars as pl
from nicegui import ui
from nicegui.testing import User

from cibmangotree.gui.dashboards.base_dashboard import BaseDashboardPage
from cibmangotree.gui.dashboards.example import ExampleDashboardPage
from cibmangotree.gui.dashboards.example.plots import (
    plot_character_count_histogram_echart,
)
from cibmangotree.gui.session import GuiSession


def test_example_dashboard_extends_base_dashboard() -> None:
    assert issubclass(ExampleDashboardPage, BaseDashboardPage)


def test_plot_character_count_histogram_buckets_by_width() -> None:
    df = pl.DataFrame({"character_count": [5, 15, 25, 35, 22]})
    option = plot_character_count_histogram_echart(df)

    # bucket width is 20: [0-19]->{5,15}, [20-39]->{25,35,22}
    assert option["xAxis"]["data"] == ["0-19", "20-39"]
    assert option["series"][0]["data"] == [2, 3]


async def test_dashboard_recovers_when_cpu_bound_returns_none(
    user: User, gui_session_with_project: GuiSession
) -> None:
    """
    Regression test: run.cpu_bound() returns None (rather than raising) if
    its task is cancelled or the app is shutting down. The dashboard must
    fall back to computing the chart synchronously instead of crashing when
    it tries to use a None result.
    """
    df = pl.DataFrame(
        {
            "message_id": [1, 2],
            "character_count": [10, 30],
            "is_long": [False, False],
        }
    )
    gui_session_with_project.selected_analyzer_name = "Example Analyzer"
    gui_session_with_project.current_analysis = object()

    holder = {}

    @ui.page("/ex-none")
    def page() -> None:
        dashboard = ExampleDashboardPage(session=gui_session_with_project)
        holder["dashboard"] = dashboard
        dashboard.render()

    with (
        patch.object(ExampleDashboardPage, "_load_data", return_value=df),
        patch(
            "cibmangotree.gui.dashboards.example.dashboard.run.cpu_bound",
            new_callable=AsyncMock,
            return_value=None,
        ),
    ):
        await user.open("/ex-none")
        await asyncio.sleep(0.5)

    chart = holder["dashboard"]._chart
    assert chart is not None
    assert chart.options["title"]["text"] == "Message length distribution"
