from datetime import datetime

from nicegui import ui

from app.analysis_context import AnalysisContext
from gui.base import GuiPage
from gui.components.analysis_utils import present_timestamp
from gui.components.manage_analyses import ManageAnalysisDialog
from gui.routes import gui_routes
from gui.session import GuiSession


class SelectPreviousAnalyzerPage(GuiPage):
    """
    Page for selecting a previous analysis to review.
    """

    grid: ui.aggrid | None = None
    analysis_contexts: list[AnalysisContext] = []

    def __init__(self, session: GuiSession):
        select_previous_title: str = "Select Previous Analysis"
        super().__init__(
            session=session,
            route=gui_routes.select_previous_analyzer,
            title=(
                f"{session.current_project.display_name}: {select_previous_title}"
                if session.current_project is not None
                else select_previous_title
            ),
            show_back_button=True,
            back_route=gui_routes.select_analyzer_fork,
            show_footer=True,
        )

    def render_content(self) -> None:
        """Render previous analysis selection interface."""
        # Ensure a project is selected
        if not self.require_project():
            return

        # Store analyses as instance state so the grid can be updated in place
        self.analysis_contexts = self.session.current_project.list_analyses()

        # Main content - centered
        with self.centered_content(max_width="800px"):
            ui.label("Review a Previous Analysis").classes("text-lg")

            if self.analysis_contexts:
                self._render_previous_analyses_grid()
            else:
                ui.label("No previous tests have been found.").classes("text-grey")

            async def _on_proceed():
                """Handle proceed button click."""
                if not self.analysis_contexts:
                    self.notify_warning("No analyses available")
                    return

                if self.grid is None:
                    return

                selected_rows = await self.grid.get_selected_rows()
                if not selected_rows:
                    self.notify_warning("Please select a previous analysis")
                    return

                selected_id = selected_rows[0].get("analysis_id")
                if not selected_id:
                    self.notify_error("Selected row is missing analysis ID")
                    return

                selected_context = next(
                    (ctx for ctx in self.analysis_contexts if ctx.id == selected_id),
                    None,
                )

                if selected_context is None:
                    self.notify_error(f"Analysis '{selected_id}' not found in project")
                    return

                if selected_context.is_draft:
                    self.notify_warning(
                        "This analysis is incomplete and cannot be viewed. "
                        "Please select a completed analysis."
                    )
                    return

                self.session.current_analysis = selected_context.model
                self.session.selected_analyzer = selected_context.analyzer_spec
                self.session.selected_analyzer_name = (
                    selected_context.analyzer_spec.name
                )
                self.session.column_mapping = selected_context.column_mapping
                self.session.analysis_params = selected_context.backfilled_param_values

                self.navigate_to(gui_routes.post_analysis)

            async def _on_manage_analyses():
                """Handle manage analyses button click."""
                dialog = ManageAnalysisDialog(session=self.session)
                deleted_ids: set = await dialog

                if not deleted_ids:
                    return

                # Remove deleted analyses from instance state
                self.analysis_contexts = [
                    ctx for ctx in self.analysis_contexts if ctx.id not in deleted_ids
                ]

                # Update the page grid in place — no page navigation needed
                if self.grid is not None:
                    now = datetime.now()
                    self.grid.options["rowData"] = [
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
                    ]
                    self.grid.update()

                count = len(deleted_ids)
                label = "analysis" if count == 1 else "analyses"
                self.notify_success(f"Deleted {count} {label}.")

            with ui.row().classes("gap-4"):
                ui.button(
                    "Manage Analyses",
                    icon="settings",
                    color="secondary",
                    on_click=_on_manage_analyses,
                )
                ui.button(
                    "Proceed",
                    icon="arrow_forward",
                    color="primary",
                    on_click=_on_proceed,
                )

    def _render_previous_analyses_grid(self) -> None:
        """Render grid of previous analyses."""
        now = datetime.now()

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
                "rowSelection": {"mode": "singleRow"},
            },
            theme="quartz",
        ).classes("w-full h-64")
