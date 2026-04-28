"""Behavior tests for gui.base utilities and GuiPage scaffolding."""

from unittest.mock import MagicMock

import pytest
from nicegui import ui

from gui.base import GuiPage, format_file_size, present_separator
from gui.session import GuiSession


def test_format_file_size_kb_and_mb() -> None:
    assert format_file_size(1536).startswith("1.5")
    assert "KB" in format_file_size(1536)
    assert "MB" in format_file_size(1048576)


def test_present_separator_known_mappings() -> None:
    assert present_separator("\t") == "Tab"
    assert ", (Comma)" in present_separator(",")


class _StubPage(GuiPage):
    def render_content(self) -> None:
        ui.label("stub-body")


@pytest.mark.asyncio
async def test_gui_page_render_invokes_colors_header_content_footer(
    user, gui_session: GuiSession
) -> None:
    @ui.page("/stub-base")
    def page() -> None:
        _StubPage(session=gui_session).render()

    await user.open("/stub-base")
    await user.should_see("stub-body")
    await user.should_see("CIB Mango Tree")
