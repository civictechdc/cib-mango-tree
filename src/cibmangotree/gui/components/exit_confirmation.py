from nicegui import ui


class ExitConfirmationDialog(ui.dialog):
    """Reusable confirmation dialog for page exit navigation.

    Subclasses ui.dialog to match the pattern used by
    ManageProjectsDialog and ImportOptionsDialog.

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
        with self, ui.card().classes("w-80 items-center"):
            ui.label(message).classes("text-center q-mb-md")
            with ui.row().classes("gap-2"):
                ui.button(
                    cancel_text,
                    on_click=lambda: self.submit(False),
                ).props("flat")
                ui.button(
                    confirm_text,
                    on_click=lambda: self.submit(True),
                    color="negative",
                ).props("flat")
