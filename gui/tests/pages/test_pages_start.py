"""Behavior tests for gui.pages.start.StartPage."""

from nicegui import ui
from nicegui.testing import User

from gui.pages.start import StartPage
from gui.session import GuiSession


async def test_start_page_shows_primary_actions(
    user: User, gui_session: GuiSession
) -> None:
    @ui.page("/")
    def page() -> None:
        StartPage(session=gui_session).render()

    await user.open("/")
    await user.should_see("Let's get started!")
    await user.should_see("New Project")
    await user.should_see("Show Existing Projects")
