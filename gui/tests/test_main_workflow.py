"""Behavior tests for gui.main_workflow dashboard wiring."""

from nicegui import ui
from nicegui.testing import User

from gui.dashboards.ngrams import NgramsDashboardPage
from gui.dashboards import _DASHBOARD_REGISTRY, PlaceholderDashboard
from gui.session import GuiSession


def test_dashboard_registry_maps_ngrams_to_dashboard_page() -> None:
    assert _DASHBOARD_REGISTRY.get("ngrams") is NgramsDashboardPage


async def test_placeholder_dashboard_shows_coming_soon(
    user: User, gui_session: GuiSession
) -> None:
    @ui.page("/placeholder-dash")
    def page() -> None:
        PlaceholderDashboard(gui_session).render()

    await user.open("/placeholder-dash")
    await user.should_see("Dashboard coming soon")
