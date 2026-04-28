"""Behavior tests for gui.components.stepper_steps.column_mapping_step.ColumnMappingStep."""

import pytest
from nicegui import ui
from nicegui.testing import User

from gui.components.stepper_steps.column_mapping_step import ColumnMappingStep
from gui.session import GuiSession


@pytest.mark.asyncio
async def test_column_mapping_prompts_when_no_analyzer(
    user: User, gui_session: GuiSession
) -> None:
    step = ColumnMappingStep(gui_session)

    @ui.page("/map-step")
    def page() -> None:
        step.render()

    await user.open("/map-step")
    await user.should_see("Please select an analyzer first")
