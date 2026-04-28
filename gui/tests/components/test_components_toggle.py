"""Behavior tests for gui.components.toggle.ToggleButtonGroup."""

import pytest
from nicegui import ui
from nicegui.testing import User

from gui.components.toggle import ToggleButtonGroup


@pytest.mark.asyncio
async def test_toggle_group_renders_buttons(user: User) -> None:
    @ui.page("/tg")
    def page() -> None:
        group = ToggleButtonGroup()
        group.add_button("Alpha")
        group.add_button("Beta")

    await user.open("/tg")
    await user.should_see("Alpha")
    await user.should_see("Beta")
