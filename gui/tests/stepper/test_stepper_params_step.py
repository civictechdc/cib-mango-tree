"""Behavior tests for gui.components.stepper_steps.params_step.ParamsConfigStep."""

from unittest.mock import MagicMock

import pytest
from nicegui import ui

from gui.components.stepper_steps.params_step import ParamsConfigStep
from gui.session import GuiSession


@pytest.mark.asyncio
async def test_params_step_no_params_message(user, gui_session: GuiSession) -> None:
    analyzer = MagicMock()
    analyzer.params = []
    gui_session.selected_analyzer = analyzer

    step = ParamsConfigStep(gui_session)

    @ui.page("/params-step")
    def page() -> None:
        step.render()

    await user.open("/params-step")
    await user.should_see("This analyzer has no configurable parameters.")
