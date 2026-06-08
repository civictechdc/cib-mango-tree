import os

from nicegui import run, ui

from cibmangotree.app.analysis_context import AnalysisContext
from cibmangotree.gui.base import GuiPage
from cibmangotree.gui.components import ExportDialog
from cibmangotree.gui.routes import gui_routes
from cibmangotree.gui.session import GuiSession
from cibmangotree.gui.utils import open_directory_explorer


class PostAnalysisPage(GuiPage):
    def __init__(self, session: GuiSession):
        super().__init__(
            session=session,
            route=gui_routes.post_analysis,
            title=f"{session.current_project.display_name}: Configure Parameters",
            show_back_button=True,
            back_route=gui_routes.configure_analysis,
            show_footer=True,
        )

    def render_content(self):
        has_outputs = False

        if self.session.current_analysis and self.session.current_project:
            temp_ctx = AnalysisContext(
                model=self.session.current_analysis,
                project_context=self.session.current_project,
                app_context=self.session.current_project.app_context,
            )
            has_outputs = bool(temp_ctx.get_all_exportable_outputs())

        async def _open_export():
            ctx = AnalysisContext(
                model=self.session.current_analysis,
                project_context=self.session.current_project,
                app_context=self.session.current_project.app_context,
            )
            dialog = ExportDialog(analysis_context=ctx)
            await dialog

        async def _open_results_folder():
            if self.session.current_analysis is None:
                self.notify_warning("No analysis to open. Run an analysis first.")
                return
            results_path = os.path.dirname(
                self.session.app.context.storage._get_project_primary_output_root_path(
                    self.session.current_analysis
                )
            )
            try:
                await run.io_bound(open_directory_explorer, results_path)
            except OSError as e:
                self.notify_error(f"Could not open results folder: {e}")

        with self.centered_content():
            ui.label("What would you like to do next?").classes("q-mb-lg").style(
                "font-size: 1.05rem"
            )

            with ui.row().classes("gap-4"):
                ui.button(
                    "Open results dashboard",
                    on_click=lambda: self.navigate_to(gui_routes.dashboard),
                    color="primary",
                )

                ui.button(
                    "Export raw output files",
                    on_click=_open_export,
                    color="primary",
                ).set_enabled(has_outputs)

                ui.button(
                    "Open results folder",
                    on_click=_open_results_folder,
                    color="primary",
                )
