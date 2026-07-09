"""Behavior tests for gui.components.new_project_dialog.NewProjectDialog."""

from nicegui import ui
from nicegui.testing import User

from cibmangotree.gui.components.new_project_dialog import NewProjectDialog
from cibmangotree.gui.session import GuiSession


async def test_new_project_dialog_valid_name_sets_session(
    user: User, gui_session: GuiSession
) -> None:
    @ui.page("/npd")
    def page() -> None:
        NewProjectDialog(gui_session)

    await user.open("/npd")
    await user.should_see("Create New Project")
    await user.should_see("Project Name")

    user.find(kind=ui.input).type("My Project")
    user.find(content="Next").click()

    assert gui_session.new_project_name == "My Project"
