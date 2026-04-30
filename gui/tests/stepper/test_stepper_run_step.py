"""Behavior tests for gui.components.stepper_steps.run_step.RunAnalysisStep."""

from unittest.mock import MagicMock

from nicegui import ui
from nicegui.testing import User

from gui.components.stepper_steps.run_step import RunAnalysisStep
from gui.session import GuiSession


async def test_run_step_prompts_when_no_analyzer(
    user: User, gui_session: GuiSession
) -> None:
    page = MagicMock()
    step = RunAnalysisStep(gui_session, page)

    @ui.page("/run-step")
    def page_render() -> None:
        step.render()

    await user.open("/run-step")
    await user.should_see("Please select an analyzer first")
