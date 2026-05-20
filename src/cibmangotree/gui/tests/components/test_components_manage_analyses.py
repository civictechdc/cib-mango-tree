"""Behavior tests for gui.components.manage_analyses.ManageAnalysisDialog."""

from gui.components.manage_analyses import ManageAnalysisDialog
from gui.session import GuiSession
from nicegui import ui
from nicegui.testing import User


async def test_manage_analyses_dialog_title(
    user: User, gui_session_with_project: GuiSession
) -> None:
    @ui.page("/ma")
    def page() -> None:
        ManageAnalysisDialog(gui_session_with_project)

    await user.open("/ma")
    await user.should_see("Manage Analyses")
