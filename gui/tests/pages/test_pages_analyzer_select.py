"""Behavior tests for gui.pages.analyzer_select.SelectAnalyzerForkPage."""

import pytest
from nicegui import ui
from nicegui.testing import User

from gui.pages.analyzer_select import SelectAnalyzerForkPage
from gui.session import GuiSession


@pytest.mark.asyncio
async def test_analyzer_fork_shows_choice_prompt(
    user: User, gui_session_with_project: GuiSession
) -> None:
    @ui.page("/fork")
    def page() -> None:
        SelectAnalyzerForkPage(session=gui_session_with_project).render()

    await user.open("/fork")
    await user.should_see("What do you want to do next?")
    await user.should_see("Start a New Test")
