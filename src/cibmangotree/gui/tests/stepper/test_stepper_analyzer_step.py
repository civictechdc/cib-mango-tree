"""Behavior tests for gui.pages.analysis_workflow.analyzer_step.AnalyzerSelectionStep."""

from nicegui import ui
from nicegui.testing import User

from cibmangotree.gui.pages.analysis_workflow.analyzer_step import (
    AnalyzerSelectionStep,
)
from cibmangotree.gui.session import GuiSession


async def test_analyzer_selection_empty_suite_message(
    user: User, gui_session: GuiSession
) -> None:
    step = AnalyzerSelectionStep(gui_session)

    @ui.page("/analyzer-step")
    def page() -> None:
        step.render()

    await user.open("/analyzer-step")
    await user.should_see("No analyzers available")
