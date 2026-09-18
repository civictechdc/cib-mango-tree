"""Behavior tests for gui.pages.importer.ImportDatasetPage."""

from unittest.mock import patch

from nicegui import ui
from nicegui.testing import User

from cibmangotree.gui.pages.importer import ImportDatasetPage
from cibmangotree.gui.routes import gui_routes
from cibmangotree.gui.session import GuiSession
from cibmangotree.importing.huggingface import HuggingFaceImportSession


async def test_import_dataset_page_prompt(user: User, gui_session: GuiSession) -> None:
    @ui.page("/import_dataset")
    def page() -> None:
        ImportDatasetPage(session=gui_session).render()

    await user.open("/import_dataset")
    await user.should_see("Choose a dataset file.")


async def test_fetch_url_with_single_file_goes_to_preview(
    user: User, gui_session: GuiSession
) -> None:
    @ui.page("/import_dataset")
    def page() -> None:
        ImportDatasetPage(session=gui_session).render()

    @ui.page(gui_routes.preview_dataset)
    def preview_page() -> None:
        ui.label("preview page")

    with patch("cibmangotree.importing.huggingface.HfApi") as mock_hf_api:
        mock_hf_api.return_value.list_repo_files.return_value = ["data/train.parquet"]

        await user.open("/import_dataset")
        user.find(kind=ui.input).type("https://huggingface.co/datasets/foo/bar")
        user.find(content="Fetch").click()
        await user.should_see("preview page")

    assert gui_session.import_session == HuggingFaceImportSession(
        repo_id="foo/bar", filename="data/train.parquet"
    )
    assert gui_session.selected_file_name == "data/train.parquet"


async def test_fetch_url_with_multiple_files_shows_picker(
    user: User, gui_session: GuiSession
) -> None:
    @ui.page("/import_dataset")
    def page() -> None:
        ImportDatasetPage(session=gui_session).render()

    @ui.page(gui_routes.preview_dataset)
    def preview_page() -> None:
        ui.label("preview page")

    with patch("cibmangotree.importing.huggingface.HfApi") as mock_hf_api:
        mock_hf_api.return_value.list_repo_files.return_value = [
            "train.csv",
            "test.csv",
        ]

        await user.open("/import_dataset")
        user.find(kind=ui.input).type("https://huggingface.co/datasets/foo/bar")
        user.find(content="Fetch").click()
        await user.should_see("This dataset has multiple files. Pick one:")

        user.find(content="Continue").click()
        await user.should_see("preview page")

    assert gui_session.import_session is not None
    assert gui_session.import_session.repo_id == "foo/bar"


async def test_fetch_url_rejects_non_huggingface_url(
    user: User, gui_session: GuiSession
) -> None:
    @ui.page("/import_dataset")
    def page() -> None:
        ImportDatasetPage(session=gui_session).render()

    await user.open("/import_dataset")
    user.find(kind=ui.input).type("https://example.com/not-a-dataset")
    user.find(content="Fetch").click()
    await user.should_see("doesn't look like a Hugging Face dataset URL")

    assert gui_session.import_session is None
