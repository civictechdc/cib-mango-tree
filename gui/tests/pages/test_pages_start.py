"""Behavior tests for gui.pages.start.StartPage."""

import pytest
from nicegui import ui

from gui.pages.start import StartPage
from gui.session import GuiSession


@pytest.mark.asyncio
async def test_start_page_shows_primary_actions(user, gui_session: GuiSession) -> None:
    @ui.page("/")
    def page() -> None:
        StartPage(session=gui_session).render()

    await user.open("/")
    await user.should_see("Let's get started!")
    await user.should_see("New Project")
    await user.should_see("Show Existing Projects")
