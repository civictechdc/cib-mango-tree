from datetime import datetime

from nicegui import ui

from app.analysis_context import AnalysisContext
from components.select_analysis import present_timestamp
from gui.base import GuiSession


class ManageAnalysisDialog(ui.dialog):
    """
    Dialog for managing analyses (view and delete).

    Displays a list of analyses for the current project in a grid and allows
    users to select and delete one or more analyses.
    """

    def __init__(self, session: GuiSession) -> None:
        """
        Initialize the Manage Analysis dialog.

        Args:
            session: GUI session containing app context and state
        """
        super().__init__()

        self.session = session
        now = datetime.now()
        self.analysis_contexts: list[AnalysisContext] = (
            session.current_project.list_analyses()
            if session.current_project is not None
            else []
        )
        # Track IDs of analyses deleted during this dialog session
        self.deleted_ids: set = set()

        # Build dialog UI
        with self, ui.card().classes("w-full"):
            # Dialog title
            ui.label("Manage Analyses").classes("text-h6 q-mb-md")

            # Check if there are analyses to display
            if not self.analysis_contexts:
                ui.label("No analyses found").classes("text-grey q-mb-md")
            else:
                # Analyses grid — multiRow selection enabled
                self.grid = ui.aggrid(
                    {
                        "columnDefs": [
                            {"headerName": "Analyzer Name", "field": "name"},
                            {"headerName": "Date Created", "field": "date"},
                            {"headerName": "ID", "field": "analysis_id", "hide": True},
                        ],
                        "rowData": [
                            {
                                "name": ctx.display_name,
                                "date": (
                                    present_timestamp(ctx.create_time, now)
                                    if ctx.create_time
                                    else "Unknown"
                                ),
                                "analysis_id": ctx.id,
                            }
                            for ctx in self.analysis_contexts
                        ],
                        "rowSelection": {"mode": "multiRow"},
                    },
                    theme="quartz",
                ).classes("w-full h-96")

            # Action buttons
            with ui.row().classes("w-full justify-end gap-2 mt-4"):
                ui.button(
                    "Close",
                    on_click=self._handle_close,
                    color="secondary",
                ).props("outline")

                ui.button(
                    "Delete Selected", on_click=self._handle_delete, color="negative"
                )

    async def _handle_delete(self) -> None:
        """Handle delete button click — confirm then delete all selected analyses."""
        selected_rows = await self.grid.get_selected_rows()

        if not selected_rows:
            ui.notify("Please select one or more analyses to delete", type="warning")
            return

        count = len(selected_rows)

        # Show a single confirmation for all selected rows
        confirmed = await self._show_delete_confirmation(count, selected_rows)
        if not confirmed:
            return

        errors: list[str] = []
        newly_deleted: list[str] = []

        for row in selected_rows:
            analysis_id = row["analysis_id"]
            analysis_name = row["name"]

            analysis_context = next(
                (a for a in self.analysis_contexts if a.id == analysis_id), None
            )

            if not analysis_context:
                errors.append(f"'{analysis_name}' not found")
                continue

            try:
                analysis_context.delete()
                if analysis_context.is_deleted:
                    self.deleted_ids.add(analysis_id)
                    newly_deleted.append(analysis_id)
            except Exception as e:
                errors.append(f"'{analysis_name}': {e}")

        # Update the dialog grid in place — remove deleted rows
        if newly_deleted:
            self.grid.options["rowData"] = [
                row
                for row in self.grid.options["rowData"]
                if row["analysis_id"] not in newly_deleted
            ]
            self.grid.update()

        if errors:
            ui.notify(f"Some deletions failed: {'; '.join(errors)}", type="negative")
        elif newly_deleted:
            label = "analysis" if len(newly_deleted) == 1 else "analyses"
            ui.notify(
                f"Deleted {len(newly_deleted)} {label} successfully.", type="positive"
            )

    async def _show_delete_confirmation(self, count: int, rows: list[dict]) -> bool:
        """
        Show confirmation dialog before deleting analyses.

        Args:
            count: Number of analyses selected for deletion
            rows: Selected row data dicts

        Returns:
            True if user confirmed deletion, False otherwise
        """
        if count == 1:
            description = f"analysis '{rows[0]['name']}'"
        else:
            description = f"{count} analyses"

        with ui.dialog() as dialog, ui.card():
            ui.label(f"Are you sure you want to delete {description}?").classes(
                "q-mb-md"
            )
            ui.label("This action cannot be undone.").classes("text-warning q-mb-lg")

            with ui.row().classes("w-full justify-end gap-2"):
                ui.button(
                    "Cancel",
                    on_click=lambda: dialog.submit(False),
                    color="secondary",
                ).props("outline")

                ui.button(
                    "Delete", on_click=lambda: dialog.submit(True), color="negative"
                )

        return await dialog

    def _handle_close(self) -> None:
        """Close the dialog, returning the set of deleted analysis IDs to the caller."""
        self.submit(self.deleted_ids)
