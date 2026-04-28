"""Behavior tests for gui.pages.project_select.SelectProjectPage."""

import pytest
from nicegui import ui
from nicegui.testing import User

from gui.pages.project_select import SelectProjectPage
from gui.session import GuiSession


@pytest.mark.asyncio
async def test_project_select_empty_list_message(
    user: User, gui_session: GuiSession
) -> None:
    @ui.page("/select_project")
    def page() -> None:
        SelectProjectPage(session=gui_session).render()

    await user.open("/select_project")
    await user.should_see("No existing projects found.")
