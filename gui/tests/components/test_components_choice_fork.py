"""Behavior tests for gui.components.choice_fork."""

import pytest
from nicegui import ui
from nicegui.testing import User

from gui.components.choice_fork import two_button_choice_fork_content


@pytest.mark.asyncio
async def test_two_button_choice_fork_renders_prompt(user: User) -> None:
    @ui.page("/fork")
    def page() -> None:
        two_button_choice_fork_content(
            prompt="Pick one",
            left_button_label="Left",
            left_button_on_click=lambda: None,
            left_button_icon="computer",
            right_button_label="Right",
            right_button_on_click=lambda: None,
            right_button_icon="refresh",
        )

    await user.open("/fork")
    await user.should_see("Pick one")
    await user.should_see("Left")
