"""Behavior tests for gui.pages.project_new.NewProjectPage."""

import pytest
from nicegui import ui

from gui.pages.project_new import NewProjectPage
from gui.session import GuiSession


@pytest.mark.asyncio
async def test_new_project_empty_name_shows_warning(
    user, gui_session: GuiSession
) -> None:
    @ui.page("/new_project")
    def page() -> None:
        NewProjectPage(session=gui_session).render()

    await user.open("/new_project")
    user.find(content="Next: Select Dataset").click()
    await user.should_see("Please enter a project name")


@pytest.mark.asyncio
async def test_new_project_sets_session_and_advances_name(
    user, gui_session: GuiSession
) -> None:
    @ui.page("/new_project")
    def page() -> None:
        NewProjectPage(session=gui_session).render()

    await user.open("/new_project")
    user.find(kind=ui.input).type("My Dataset")
    user.find(content="Next: Select Dataset").click()

    assert gui_session.new_project_name == "My Dataset"
