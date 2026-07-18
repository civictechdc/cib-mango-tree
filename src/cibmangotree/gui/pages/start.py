from datetime import datetime

from nicegui import ui

from cibmangotree.gui.base import GuiPage
from cibmangotree.gui.components import NewProjectDialog
from cibmangotree.gui.routes import gui_routes
from cibmangotree.gui.session import GuiSession

_COLUMNS = [
    {
        "name": "project_name",
        "label": "Project name",
        "field": "project_name",
        "align": "left",
        "sortable": True,
    },
    {
        "name": "dataset",
        "label": "Dataset",
        "field": "dataset",
        "align": "left",
        "sortable": True,
    },
    {
        "name": "date_created",
        "label": "Date Created",
        "field": "date_created",
        "align": "left",
        "sortable": True,
        ":sort": "(a, b, rowA, rowB) => (rowA.date_created_ts ?? 0) - (rowB.date_created_ts ?? 0)",
    },
    {
        "name": "date_modified",
        "label": "Date Last Modified",
        "field": "date_modified",
        "align": "left",
        "sortable": True,
        ":sort": "(a, b, rowA, rowB) => (rowA.date_modified_ts ?? 0) - (rowB.date_modified_ts ?? 0)",
    },
]


class StartPage(GuiPage):
    """
    Main/home page of the application.

    Displays a project overview table with actions for creating,
    opening, and deleting projects.
    """

    def __init__(self, session: GuiSession):
        super().__init__(
            session=session,
            route="/",
            title="CIB Mango Tree",
            show_back_button=False,
            show_footer=True,
        )

        self._table: ui.table | None = None
        self._open_button: ui.button | None = None
        self._delete_button: ui.button | None = None

    def render_content(self) -> None:
        ui.add_head_html("""
            <style>
                .my-sticky-table {
                    height: 310px;
                }
                .my-sticky-table thead tr th {
                    position: sticky;
                    z-index: 1;
                    background-color: white;
                }
                .my-sticky-table thead tr:first-child th {
                    top: 0;
                }
                .my-sticky-table thead tr th,
                .my-sticky-table tbody tr td {
                    font-size: 0.85rem;
                }
            </style>
        """)

        with self.centered_content(height="auto", padding="2rem"):
            ui.html(self._load_svg_icon("cibmt_logo"), sanitize=False).classes(
                "size-24 q-mb-md"
            )

            with ui.column().classes("w-full") as container:
                container.style("max-width: 960px; margin: 0 auto;")

                with ui.row().classes("w-full items-center"):
                    ui.label("Projects").classes("text-h6 text-gray-600")
                    ui.space()
                    ui.button(
                        "Create New",
                        on_click=self._handle_create_new,
                        icon="add",
                        color="primary",
                    )

                self._build_table()

                with ui.row().classes("w-full gap-4 q-mt-md justify-end"):
                    self._delete_button = ui.button(
                        "Delete",
                        on_click=self._handle_delete_project,
                        icon="delete",
                        color="negative",
                    )
                    self._delete_button.props("disable")

                    self._open_button = ui.button(
                        "Open Project",
                        on_click=self._handle_open_project,
                        icon="folder_open",
                        color="primary",
                    )
                    self._open_button.props("disable")

    def _build_table(self) -> None:
        rows = self._build_rows()
        self._table = (
            ui.table(
                columns=_COLUMNS,
                rows=rows,
                row_key="project_id",
                selection="single",
            )
            .classes("w-full my-sticky-table")
            .props("flat bordered separator='horizontal' sticky-header")
        )

        self._table.on("selection", self._on_selection_change)

    def _build_rows(self) -> list[dict]:
        projects = self.session.app.list_projects()
        rows = []
        for proj in projects:
            rows.append(
                {
                    "project_id": proj.id,
                    "project_name": proj.display_name,
                    "dataset": proj.model.dataset_name or "—",
                    "date_created": self._format_timestamp(proj.model.create_timestamp),
                    "date_created_ts": proj.model.create_timestamp,
                    "date_modified": self._format_timestamp(
                        proj.model.modified_timestamp
                    ),
                    "date_modified_ts": proj.model.modified_timestamp,
                }
            )
        return rows

    @staticmethod
    def _format_timestamp(ts: float | None) -> str:
        if ts is not None:
            return datetime.fromtimestamp(ts).strftime("%Y-%m-%d %H:%M")
        return "Unknown"

    def _refresh_table(self) -> None:
        assert self._table is not None
        self._table.rows = self._build_rows()
        self._table.update()
        self._update_button_states()

    def _on_selection_change(self, event) -> None:
        self._update_button_states()

    def _update_button_states(self) -> None:
        assert self._table is not None
        assert self._open_button is not None
        assert self._delete_button is not None
        has_selection = bool(self._table.selected)
        if has_selection:
            self._open_button.props(remove="disable")
            self._delete_button.props(remove="disable")
        else:
            self._open_button.props("disable")
            self._delete_button.props("disable")

    async def _handle_create_new(self) -> None:
        dialog = NewProjectDialog(self.session)
        result = await dialog
        if result:
            self.navigate_to(gui_routes.import_dataset)

    async def _handle_open_project(self) -> None:
        assert self._table is not None
        if not self._table.selected:
            return
        selected = self._table.selected[0]
        project_id = selected["project_id"]
        self._open_project_by_id(project_id)

    def _open_project_by_id(self, project_id: str) -> None:
        projects = self.session.app.list_projects()
        project = next((p for p in projects if p.id == project_id), None)
        if project is None:
            self.notify_error("Project not found")
            self._refresh_table()
            return

        self.session.current_project = project
        self.session.project_loaded_from_storage = True
        self.navigate_to("/select_analyzer_fork")

    async def _handle_delete_project(self) -> None:
        assert self._table is not None
        if not self._table.selected:
            return
        selected = self._table.selected[0]
        project_id = selected["project_id"]
        project_name = selected["project_name"]

        with ui.dialog() as dialog, ui.card():
            ui.label(f"Delete project '{project_name}'?").classes("q-mb-md")
            ui.label("This action cannot be undone.").classes("text-warning q-mb-lg")
            with ui.row().classes("w-full justify-end gap-2"):
                ui.button(
                    "Cancel", on_click=lambda: dialog.submit(False), color="cancel"
                ).props("outline")
                ui.button(
                    "Delete", on_click=lambda: dialog.submit(True), color="negative"
                )

        confirmed = await dialog
        if not confirmed:
            return

        try:
            projects = self.session.app.list_projects()
            project = next((p for p in projects if p.id == project_id), None)
            if project is None:
                self.notify_error("Project not found")
                self._refresh_table()
                return
            project.delete()
            self.notify_success(f"Project '{project_name}' deleted")
            self._refresh_table()
        except Exception as e:
            self.notify_error(f"Error deleting project: {e}")
