from nicegui import ui

from cibmangotree.gui.session import GuiSession
from cibmangotree.gui.theme import (
    CARD_DIALOG_MD,
    COLOR_CANCEL,
    COLOR_MANGO_ORANGE,
    COLOR_PRIMARY,
    PROPS_OUTLINE,
    ROW_ACTIONS_MT_4,
    TEXT_SECTION_HEADING,
    WIDTH_FULL,
)


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

        with self, ui.card().classes(CARD_DIALOG_MD):
            ui.label("Create New Project").classes(TEXT_SECTION_HEADING)

            self.name_input = ui.input(
                label="Project Name",
                placeholder="e.g. Twitter-2018-dataset",
                validation={
                    "Name is required": lambda value: bool(value and value.strip()),
                },
            ).classes(WIDTH_FULL)

            with ui.row().classes(ROW_ACTIONS_MT_4):
                ui.button(
                    "Cancel",
                    on_click=self._handle_cancel,
                    color=COLOR_CANCEL,
                ).props(PROPS_OUTLINE)

                ui.button(
                    "Next",
                    on_click=self._handle_next,
                    icon="arrow_forward",
                    color=COLOR_PRIMARY,
                )

    def _handle_cancel(self) -> None:
        self.submit(None)

    def _handle_next(self) -> None:
        name = self.name_input.value
        if not name or not name.strip():
            ui.notify(
                "Please enter a project name", type="warning", color=COLOR_MANGO_ORANGE
            )
            return

        self.session.new_project_name = name.strip()
        self.submit(self.session.new_project_name)
