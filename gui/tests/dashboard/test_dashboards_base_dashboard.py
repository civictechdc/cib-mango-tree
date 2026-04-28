"""Behavior tests for gui.dashboards.base_dashboard.BaseDashboardPage."""

import pytest
from nicegui import ui
from nicegui.testing import User

from gui.dashboards.base_dashboard import BaseDashboardPage
from gui.session import GuiSession


class _StubDashboard(BaseDashboardPage):
    def render_content(self) -> None:
        ui.label("stub-dashboard-body")


@pytest.mark.asyncio
async def test_base_dashboard_renders_content(
    user: User, gui_session_with_project: GuiSession
) -> None:
    gui_session_with_project.selected_analyzer_name = "Demo Analyzer"

    @ui.page("/dash")
    def page() -> None:
        _StubDashboard(session=gui_session_with_project).render()

    await user.open("/dash")
    await user.should_see("stub-dashboard-body")
