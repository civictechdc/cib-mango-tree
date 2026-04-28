"""Behavior tests for gui.main_workflow dashboard wiring."""

import pytest
from nicegui import ui
from nicegui.testing import User

from gui.dashboards.ngrams import NgramsDashboardPage
from gui.main_workflow import _DASHBOARD_REGISTRY, _render_dashboard_placeholder
from gui.session import GuiSession


def test_dashboard_registry_maps_ngrams_to_dashboard_page() -> None:
    assert _DASHBOARD_REGISTRY.get("ngrams") is NgramsDashboardPage


@pytest.mark.asyncio
async def test_placeholder_dashboard_shows_coming_soon(
    user: User, gui_session: GuiSession
) -> None:
    @ui.page("/placeholder-dash")
    def page() -> None:
        _render_dashboard_placeholder(gui_session)

    await user.open("/placeholder-dash")
    await user.should_see("Dashboard coming soon")
