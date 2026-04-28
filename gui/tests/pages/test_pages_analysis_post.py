"""Behavior tests for gui.pages.analysis_post.PostAnalysisPage."""

import pytest
from nicegui import ui

from gui.pages.analysis_post import PostAnalysisPage
from gui.session import GuiSession


@pytest.mark.asyncio
async def test_post_analysis_shows_next_steps(
    user, gui_session_with_project: GuiSession
) -> None:
    @ui.page("/post_analysis")
    def page() -> None:
        PostAnalysisPage(session=gui_session_with_project).render()

    await user.open("/post_analysis")
    await user.should_see("What would you like to do next?")
    await user.should_see("Open results dashboard")
