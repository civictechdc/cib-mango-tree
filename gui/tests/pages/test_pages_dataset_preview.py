"""Behavior tests for gui.pages.dataset_preview.PreviewDatasetPage."""

from io import BytesIO

from nicegui import ui
from nicegui.testing import User

from gui.pages.dataset_preview import PreviewDatasetPage
from gui.session import GuiSession


async def test_preview_redirects_when_no_file_selected(
    user: User, gui_session: GuiSession
) -> None:
    @ui.page("/preview_dataset")
    def page() -> None:
        PreviewDatasetPage(session=gui_session).render()

    await user.open("/preview_dataset")
    await user.should_see("No file selected. Redirecting")


async def test_preview_redirects_when_format_not_detected(
    user: User, gui_session: GuiSession
) -> None:
    gui_session.selected_file = BytesIO(b"x")
    gui_session.selected_file_name = "x.bin"
    gui_session.selected_file_content_type = "application/octet-stream"

    @ui.page("/preview_dataset")
    def page() -> None:
        PreviewDatasetPage(session=gui_session).render()

    await user.open("/preview_dataset")
    await user.should_see("Could not detect file format")
