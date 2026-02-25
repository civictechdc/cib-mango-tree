from nicegui import ui

from gui.base import GuiPage, GuiSession, gui_routes

BUTTON_OPTIONS = {
    "dashboard": "Open results dashboard",
    "export": "Export raw output files",
    "open_folder": "Open results folder",
}


class PostAnalysisPage(GuiPage):

    def __init__(self, session: GuiSession):
        super().__init__(
            session=session,
            route=gui_routes.post_analysis,
            title=f"{session.current_project.display_name}: Configure Parameters",
            show_back_button=True,
            back_route=gui_routes.configure_analysis_dataset,
            show_footer=True,
        )

    def render_content(self):

        with (
            ui.column()
            .classes("items-center justify-center")
            .style("height: 80vh; width: 100%")
        ):
            # Prompt label
            ui.label("What would you like to do next?").classes("q-mb-lg").style(
                "font-size: 1.05rem"
            )

            # Action buttons row
            with ui.row().classes("gap-4"):

                for btn_label in BUTTON_OPTIONS.values():
                    ui.button(
                        btn_label,
                        on_click=ui.notify("Coming soon!"),
                        color="primary",
                    )
