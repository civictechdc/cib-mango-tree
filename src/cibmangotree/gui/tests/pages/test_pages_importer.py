"""Behavior tests for gui.pages.importer.ImportDatasetPage."""

from nicegui import ui
from nicegui.testing import User

from cibmangotree.gui.pages.importer import ImportDatasetPage
from cibmangotree.gui.session import GuiSession


async def test_import_dataset_page_prompt(user: User, gui_session: GuiSession) -> None:
    @ui.page("/import_dataset")
    def page() -> None:
        ImportDatasetPage(session=gui_session).render()

    await user.open("/import_dataset")
    await user.should_see("Choose a dataset file.")
