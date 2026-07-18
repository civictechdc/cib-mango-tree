from nicegui import ui

from cibmangotree.gui.session import GuiSession


class NewProjectDialog(ui.dialog):
    """
    Inline dialog for creating a new project.

    Displays a project name input field with validation.
    On "Next", sets session.new_project_name and submits the dialog
    with the validated name.
    """

    def __init__(self, session: GuiSession) -> None:
        super().__init__()

        self.session = session

        with self, ui.card().classes("w-96"):
            ui.label("Create New Project").classes("text-h6 q-mb-md")

            self.name_input = ui.input(
                label="Project Name",
                placeholder="e.g. Twitter-2018-dataset",
                validation={
                    "Name is required": lambda value: bool(value and value.strip()),
                },
            ).classes("w-full")

            with ui.row().classes("w-full justify-end gap-2 mt-4"):
                ui.button(
                    "Cancel",
                    on_click=self._handle_cancel,
                    color="cancel",
                ).props("outline")

                ui.button(
                    "Next",
                    on_click=self._handle_next,
                    icon="arrow_forward",
                    color="primary",
                )

    def _handle_cancel(self) -> None:
        self.submit(None)

    def _handle_next(self) -> None:
        name = self.name_input.value
        if not name or not name.strip():
            ui.notify("Please enter a project name", type="warning")
            return

        self.session.new_project_name = name.strip()
        self.submit(self.session.new_project_name)
