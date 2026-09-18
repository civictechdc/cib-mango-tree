"""Behavior tests for gui.dashboards.base_dashboard.BaseDashboardPage."""

from nicegui import ui
from nicegui.testing import User

from cibmangotree.gui.dashboards.base_dashboard import BaseDashboardPage
from cibmangotree.gui.session import GuiSession


class _StubDashboard(BaseDashboardPage):
    def render_content(self) -> None:
        ui.label("stub-dashboard-body")


async def test_base_dashboard_renders_content(
    user: User, gui_session_with_project: GuiSession
) -> None:
    gui_session_with_project.selected_analyzer_name = "Demo Analyzer"

    @ui.page("/dash")
    def page() -> None:
        _StubDashboard(session=gui_session_with_project).render()

    await user.open("/dash")
    await user.should_see("stub-dashboard-body")


async def test_show_content_lets_container_grow_to_fit_its_content(
    user: User, gui_session_with_project: GuiSession
) -> None:
    """
    content_container starts with a fixed height sized only for the loading
    spinner (see _create_loading_container). Real content is often taller
    (e.g. a chart stacked above a table), so _show_content must switch it to
    "auto" - otherwise the extra content is clipped/overlaps whatever
    follows instead of being fully visible.
    """
    holder = {}

    @ui.page("/dash2")
    def page() -> None:
        dashboard = _StubDashboard(session=gui_session_with_project)
        holder["dashboard"] = dashboard
        holder["containers"] = dashboard._create_loading_container("500px")

    await user.open("/dash2")

    loading_container, content_container = holder["containers"]
    assert content_container.style["height"] == "500px"

    holder["dashboard"]._show_content(loading_container, content_container)

    assert content_container.style["height"] == "auto"
    assert content_container.style["display"] == "block"
