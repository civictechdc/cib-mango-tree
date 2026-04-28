"""Behavior tests for gui.components.manage_projects.ManageProjectsDialog."""

import pytest
from nicegui import ui
from nicegui.testing import User

from gui.components.manage_projects import ManageProjectsDialog
from gui.session import GuiSession


@pytest.mark.asyncio
async def test_manage_projects_empty_state(user: User, gui_session: GuiSession) -> None:
    @ui.page("/mp")
    def page() -> None:
        ManageProjectsDialog(gui_session)

    await user.open("/mp")
    await user.should_see("Manage Projects")
    await user.should_see("No projects found")
