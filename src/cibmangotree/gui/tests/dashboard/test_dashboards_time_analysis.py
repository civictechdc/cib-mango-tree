"""Smoke tests for the time_analysis dashboard registration and click payload."""

from types import SimpleNamespace

from cibmangotree.gui.dashboards import get_dashboard
from cibmangotree.gui.dashboards.base_dashboard import BaseDashboardPage
from cibmangotree.gui.dashboards.time_analysis import (
    TimeAnalysisComparePage,
    TimeAnalysisDashboardPage,
)
from cibmangotree.gui.dashboards.time_analysis.chart_utils import (
    EDGE_COLOR_LEGEND,
    users_from_edge_payload,
)
from cibmangotree.gui.dashboards.time_analysis.compare import format_post_body
from cibmangotree.gui.routes import gui_routes


def test_time_analysis_dashboard_extends_base_dashboard() -> None:
    assert issubclass(TimeAnalysisDashboardPage, BaseDashboardPage)
    assert issubclass(TimeAnalysisComparePage, BaseDashboardPage)


def test_time_analysis_dashboard_is_registered() -> None:
    assert get_dashboard("time_analysis") is TimeAnalysisDashboardPage


def test_time_analysis_compare_route() -> None:
    assert gui_routes.dashboard_time_analysis_compare == (
        "/dashboard/time_analysis/compare"
    )


def test_edge_legend_includes_colors() -> None:
    assert all(color.startswith("#") for _key, color, _label in EDGE_COLOR_LEGEND)


def test_format_post_body_splits_date_and_time() -> None:
    body = format_post_body("hello world", "2024-01-01 12:34:56")
    assert "2024-01-01" in body
    assert "12:34:56" in body
    assert "hello world" in body


def test_users_from_edge_click_payload() -> None:
    pair = users_from_edge_payload(
        {"dataType": "edge", "source": "alice", "target": "bob", "name": "alice > bob"}
    )
    assert pair == ("alice", "bob")


def test_chart_click_handler_selects_pair(gui_session_with_project) -> None:
    page = TimeAnalysisDashboardPage(session=gui_session_with_project)
    page._cut_graph = SimpleNamespace(nodes=lambda: ["alice", "bob"])
    page._selected = {"user0": None, "user1": None}
    page._selection_label = SimpleNamespace(set_text=lambda _t: None)
    page._inspect_button = SimpleNamespace(
        enable=lambda: setattr(page, "_enabled", True)
    )
    page._edge_select = SimpleNamespace(
        options={"alice\tbob": "alice  ↔  bob"},
        set_value=lambda v: setattr(page, "_select_value", v),
    )
    page._enabled = False

    page._on_chart_click(
        SimpleNamespace(args={"dataType": "edge", "source": "alice", "target": "bob"})
    )
    assert page._selected == {"user0": "alice", "user1": "bob"}
    assert page._enabled is True
    assert page._select_value == "alice\tbob"
