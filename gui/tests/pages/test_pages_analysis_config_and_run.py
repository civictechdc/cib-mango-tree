"""Behavior tests for gui.pages.analysis_config_and_run.AnalysisConfigAndRunPage."""

import pytest
from nicegui import ui

from gui.pages.analysis_config_and_run import AnalysisConfigAndRunPage
from gui.session import GuiSession


@pytest.mark.asyncio
async def test_analysis_config_requires_project(user, gui_session: GuiSession) -> None:
    @ui.page("/configure_analysis")
    def page() -> None:
        AnalysisConfigAndRunPage(session=gui_session).render()

    await user.open("/configure_analysis")
    await user.should_see("No project selected. Redirecting")
