"""Behavior tests for gui.pages.dataset_preview.PreviewDatasetPage."""

from io import BytesIO
from pathlib import Path
from unittest.mock import patch

from nicegui import ui
from nicegui.testing import User

from cibmangotree.gui.pages.dataset_preview import PreviewDatasetPage
from cibmangotree.gui.session import GuiSession
from cibmangotree.importing.huggingface import HuggingFaceImportSession


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


async def test_preview_uses_preresolved_web_import_session(
    user: User, gui_session: GuiSession, tmp_path: Path
) -> None:
    """
    A session already resolved elsewhere (e.g. a Hugging Face URL import on
    ImportDatasetPage) should be previewed directly, without requiring
    uploaded file bytes or re-running importer auto-detection.
    """
    gui_session.import_session = HuggingFaceImportSession(
        repo_id="foo/bar", filename="data.csv"
    )

    source_csv = tmp_path / "data.csv"
    source_csv.write_text("a,b\n1,2\n3,4\n")

    @ui.page("/preview_dataset")
    def page() -> None:
        PreviewDatasetPage(session=gui_session).render()

    with patch(
        "cibmangotree.importing.huggingface._download", return_value=str(source_csv)
    ):
        await user.open("/preview_dataset")
        await user.should_see("Data Preview (first 5 rows)")
        # No local config to adjust for a Hugging Face import.
        await user.should_not_see("There's something wrong")
