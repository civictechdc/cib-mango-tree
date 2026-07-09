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
                project_name = new_project_name_input.value
                if not project_name or not project_name.strip():
                    self.notify_warning("Please enter a project name")
                    return
                self.session.new_project_name = project_name
                self.navigate_to(gui_routes.import_dataset)

            next_button = ui.button(
                text="Next: Select Dataset",
                icon="arrow_forward",
                on_click=_on_next,
                color="primary",
            )
            next_button.bind_enabled_from(
                new_project_name_input,
                "value",
                backward=lambda v: bool(v and v.strip() if v else False),
            )
