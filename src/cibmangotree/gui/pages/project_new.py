from nicegui import ui

from cibmangotree.gui.base import GuiPage
from cibmangotree.gui.routes import gui_routes
from cibmangotree.gui.session import GuiSession


class NewProjectPage(GuiPage):
    def __init__(self, session: GuiSession):
        super().__init__(
            session=session,
            route="/new_project",
            title="New Project",
            show_back_button=True,
            back_route="/",
            show_footer=True,
        )

    def on_exit(self) -> None:
        self.session.reset_project_workflow()

    def render_content(self) -> None:
        with self.centered_content(max_width="600px"):
            ui.label(
                "First, name your project so you can come back to it later."
            ).style("color: gray; font-size: 1.5rem")

            new_project_name_input = ui.input(
                label="New Project Name",
                placeholder="e.g. Twitter-2018-dataset",
            )

            def _on_next():
                self.session.new_project_name = new_project_name_input.value
                self.navigate_to(gui_routes.import_dataset)

            next_button = ui.button(
                text="NEXT: SELECT DATASET",
                icon="arrow_forward",
                on_click=_on_next,
                color="primary",
            )
            next_button.set_enabled(False)

            def _on_input_change():
                next_button.set_enabled(
                    bool(new_project_name_input.value and new_project_name_input.value.strip())
                )

            new_project_name_input.on("update:model-value", _on_input_change)
