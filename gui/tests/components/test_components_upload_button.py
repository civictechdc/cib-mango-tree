"""Behavior tests for gui.components.upload.upload_button.UploadButton."""

from unittest.mock import AsyncMock

import pytest
from nicegui import ui

from gui.components.upload.upload_button import UploadButton


@pytest.mark.asyncio
async def test_upload_button_shows_label(user) -> None:
    @ui.page("/up")
    def page() -> None:
        UploadButton(AsyncMock(), "Browse Files", redirect_url="/preview_dataset")

    await user.open("/up")
    await user.should_see("Browse Files")
