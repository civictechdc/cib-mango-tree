"""Behavior tests for gui.components.stepper_steps.analyzer_step.AnalyzerSelectionStep."""

from nicegui import ui
from nicegui.testing import User

from gui.components.stepper_steps.analyzer_step import AnalyzerSelectionStep
from gui.session import GuiSession


async def test_analyzer_selection_empty_suite_message(
    user: User, gui_session: GuiSession
) -> None:
    step = AnalyzerSelectionStep(gui_session)

    @ui.page("/analyzer-step")
    def page() -> None:
        step.render()

    await user.open("/analyzer-step")
    await user.should_see("No analyzers available")
