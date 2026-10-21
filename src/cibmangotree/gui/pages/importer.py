from io import BytesIO

from fastapi import UploadFile
from nicegui import ui

from cibmangotree.gui.base import GuiPage
from cibmangotree.gui.components import UploadButton
from cibmangotree.gui.routes import gui_routes
from cibmangotree.gui.session import GuiSession


class ImportDatasetPage(GuiPage):
    """
    Dataset import page for selecting a file.

    Allows users to:
    1. Browse for CSV/Excel files
    2. View file information
    3. Proceed to data preview
    """

    def __init__(self, session: GuiSession):
        super().__init__(
            session=session,
            route=gui_routes.import_dataset,
            title="Import Dataset",
            show_back_button=True,
            back_route="/",
            show_footer=True,
        )

    def requires_exit_confirmation(self) -> bool:
        if self.session.project_loaded_from_storage:
            return False
        return (
            self.session.current_project is not None
            or self.session.selected_file is not None
        )

    def get_exit_confirmation_message(self) -> str:
        return "No project has been created yet. Leave anyway?"

    def on_exit(self) -> None:
        self.session.reset_project_workflow()

    def render_content(self) -> None:
        """Render file selection interface."""
        with self.centered_content(max_width="800px"):
            ui.label("Choose a dataset file.").classes("text-lg")

            async def handle_upload(upload: UploadFile) -> None:
                file_contents: bytes = await upload.read()
                self.session.selected_file_content_type = upload.content_type
                self.session.selected_file_name = upload.filename
                self.session.selected_file = BytesIO(file_contents)

            upload_button = UploadButton(
                handle_upload,
                "Browse Files",
                icon="folder_open",
                redirect_url=gui_routes.preview_dataset,
            )
