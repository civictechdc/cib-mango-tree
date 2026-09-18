from io import BytesIO

from fastapi import UploadFile
from nicegui import run, ui

from cibmangotree.gui.base import GuiPage
from cibmangotree.gui.components import UploadButton
from cibmangotree.gui.routes import gui_routes
from cibmangotree.gui.session import GuiSession
from cibmangotree.importing.huggingface import (
    HuggingFaceImporter,
    HuggingFaceImportSession,
    parse_dataset_repo_id,
)


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
            or self.session.import_session is not None
        )

    def get_exit_confirmation_message(self) -> str:
        return "No project has been created yet. Leave anyway?"

    def on_exit(self) -> None:
        self.session.reset_project_workflow()

    def render_content(self) -> None:
        """Render file selection interface."""
        # Page state - store selected file path locally
        selected_file_path = None

        # Main content - centered vertically and horizontally
        with self.centered_content(max_width="800px"):
            ui.label("Choose a dataset file.").classes("text-lg")

            # File info card (initially hidden)
            file_info_card = ui.card().style("display: none;")
            with file_info_card:
                file_name_label = ui.label().classes("text-sm")
                file_path_label = ui.label().classes("text-sm")
                file_size_label = ui.label().classes("text-sm")
                file_modified_label = ui.label().classes("text-sm")

                with ui.row().classes("w-full justify-end gap-2 mt-4"):
                    change_file_btn = ui.button(
                        "Pick a different file",
                        icon="edit",
                        color="secondary",
                        on_click=lambda: None,
                    ).props("outline")
                    preview_btn = ui.button(
                        "Next: Preview Data", icon="arrow_forward", color="primary"
                    )

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

            ui.separator().classes("my-2")
            ui.label("Or import from a URL").classes("text-sm text-grey-7")

            with ui.row().classes("w-full items-center gap-2"):
                url_input = ui.input(
                    label="Hugging Face dataset URL",
                    placeholder="https://huggingface.co/datasets/<namespace>/<name>",
                ).classes("flex-grow")
                fetch_button = ui.button(
                    "Fetch", icon="cloud_download", color="primary"
                )

            file_picker_container = ui.column().classes("w-full gap-2")
            file_picker_container.set_visibility(False)

            def go_to_preview(web_session: HuggingFaceImportSession) -> None:
                self.session.import_session = web_session
                self.session.selected_file_name = web_session.filename
                self.navigate_to(gui_routes.preview_dataset)

            async def handle_fetch_click() -> None:
                source = (url_input.value or "").strip()
                if not source:
                    self.notify_warning("Enter a dataset URL first.")
                    return

                web_importer = HuggingFaceImporter()
                if not web_importer.suggest(source):
                    self.notify_error(
                        "That doesn't look like a Hugging Face dataset URL."
                    )
                    return

                fetch_button.props("loading")
                try:
                    web_session = await run.io_bound(web_importer.init_session, source)
                    if web_session is not None:
                        go_to_preview(web_session)
                        return

                    candidates = await run.io_bound(
                        HuggingFaceImporter.list_data_files, source
                    )
                except Exception as e:
                    self.notify_error(f"Could not reach this dataset: {e}")
                    return
                finally:
                    fetch_button.props(remove="loading")

                if not candidates:
                    self.notify_error(
                        "No supported data files (CSV/TSV/JSON/Parquet) found "
                        "in this dataset."
                    )
                    return

                repo_id = parse_dataset_repo_id(source)
                assert repo_id is not None

                file_picker_container.clear()
                file_picker_container.set_visibility(True)
                with file_picker_container:
                    ui.label("This dataset has multiple files. Pick one:").classes(
                        "text-sm"
                    )
                    file_select = ui.select(candidates, value=candidates[0]).classes(
                        "w-full"
                    )
                    ui.button(
                        "Continue",
                        icon="arrow_forward",
                        color="primary",
                        on_click=lambda: go_to_preview(
                            HuggingFaceImportSession(
                                repo_id=repo_id, filename=file_select.value
                            )
                        ),
                    )

            fetch_button.on_click(handle_fetch_click)
