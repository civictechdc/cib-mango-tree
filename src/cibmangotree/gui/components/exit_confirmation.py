from nicegui import ui

from cibmangotree.gui.theme import (
    CARD_DIALOG_NARROW,
    ROW_GAP_2,
    TEXT_CENTER_MB_4,
    gui_props,
)


class ExitConfirmationDialog(ui.dialog):
    """Reusable confirmation dialog for page exit navigation.

    Subclasses ui.dialog to match the pattern used by
    ImportOptionsDialog.

    Usage:
        dialog = ExitConfirmationDialog(
            message="You have unsaved changes. Leave anyway?",
            confirm_text="Leave",
            cancel_text="Stay"
        )
        confirmed = await dialog
        if confirmed:
            ui.navigate.to("/home")
    """

    def __init__(
        self,
        message: str = "Are you sure you want to leave?",
        confirm_text: str = "Leave",
        cancel_text: str = "Stay",
    ):
        super().__init__()
        with self, ui.card().classes(CARD_DIALOG_NARROW):
            ui.label(message).classes(TEXT_CENTER_MB_4)
            with ui.row().classes(ROW_GAP_2):
                ui.button(
                    cancel_text,
                    on_click=lambda: self.submit(False),
                    color="cancel",
                ).props(gui_props.flat)
                ui.button(
                    confirm_text,
                    on_click=lambda: self.submit(True),
                    color="negative",
                ).props(gui_props.flat)
