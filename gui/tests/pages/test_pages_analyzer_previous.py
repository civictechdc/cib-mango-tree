"""Behavior tests for gui.pages.analyzer_previous.SelectPreviousAnalyzerPage."""

import pytest
from nicegui import ui

from gui.pages.analyzer_previous import SelectPreviousAnalyzerPage
from gui.session import GuiSession


@pytest.mark.asyncio
async def test_previous_analyzer_empty_state(
    user, gui_session_with_project: GuiSession
) -> None:
    @ui.page("/prev")
    def page() -> None:
        SelectPreviousAnalyzerPage(session=gui_session_with_project).render()

    await user.open("/prev")
    await user.should_see("No previous tests have been found.")
