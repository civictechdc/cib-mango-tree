"""
Import options dialog for modifying CSV/Excel import configuration.

Allows users to adjust import settings and retry preview with updated parameters.
"""

from io import BytesIO
from traceback import format_exc
from typing import Callable

from nicegui import ui

from cibmangotree.gui.theme import (
    CARD_DIALOG_PADDED,
    ICON_INFO,
    ROW_ACTIONS_MT_3,
    ROW_CENTERED_GAP,
    ROW_LAYOUT,
    STYLE_IMPORT_DIALOG,
    STYLE_LABEL_MIN_WIDTH,
    TEXT_BASE,
    TEXT_DIALOG_LEAD,
    TEXT_DIALOG_TITLE,
    TEXT_FIELD_LABEL,
    TEXT_MUTED_SM_MB_2,
    TEXT_MUTED_SM_MT_2,
    TEXT_TOOLTIP_BODY,
    WIDTH_SKIP_ROWS,
    WIDTH_TOOLTIP,
    gui_props,
)
from cibmangotree.importing.csv import CsvImportSession
from cibmangotree.importing.excel import ExcelImportSession


class ImportOptionsDialog(ui.dialog):
    """
    Dialog for configuring CSV/Excel import options.

    Displays interactive controls for modifying import parameters
    and allows retrying the import with updated settings.
    """

    def __init__(
        self,
        import_session: CsvImportSession | ExcelImportSession,
        selected_file: BytesIO,
        on_retry: Callable[[CsvImportSession | ExcelImportSession], None],
    ):
        """
        Initialize the import options dialog.

        Args:
            import_session: Current import session with detected settings
            selected_file: BytesIO buffer of the file being imported
            on_retry: Callback function called when user clicks "Retry Import"
                     with the updated import session as parameter
        """
        super().__init__()

        self.import_session = import_session
        self.selected_file = selected_file
        self.on_retry = on_retry

        # Build dialog UI
        with (
            self,
            ui.card().classes(CARD_DIALOG_PADDED).style(STYLE_IMPORT_DIALOG),
        ):
            ui.label("Fix Import Settings").classes(TEXT_DIALOG_TITLE)

            ui.label(
                "Sometimes the default settings don't suit your dataset. "
                "Adjust the settings below to import your data correctly."
            ).classes(TEXT_DIALOG_LEAD)

            if isinstance(import_session, CsvImportSession):
                self._build_csv_controls()
            elif isinstance(import_session, ExcelImportSession):
                self._build_excel_controls()

            # Action buttons
            with ui.row().classes(ROW_ACTIONS_MT_3):
                ui.button("Cancel", on_click=self.close, color="cancel").props(
                    gui_props.outline
                )
                ui.button(
                    "Retry Import",
                    icon="refresh",
                    on_click=self._handle_retry,
                    color="primary",
                )

    def _build_csv_controls(self):
        """Build CSV-specific configuration controls."""
        session = self.import_session

        # Row 1: Column Separator
        with ui.row().classes(ROW_LAYOUT):
            with ui.row().classes(ROW_CENTERED_GAP).style(STYLE_LABEL_MIN_WIDTH):
                ui.label("Column separator:").classes(TEXT_FIELD_LABEL)
                with ui.icon("info").classes(ICON_INFO):
                    with (
                        ui.tooltip()
                        .classes(WIDTH_TOOLTIP)
                        .props(gui_props.tooltip_offset)
                    ):
                        ui.label(
                            "Data files separate columns by commas, semicolons, pipes, or "
                            "tabs (empty space). Open your data file in a text editor to "
                            "visually determine what symbols are separating your columns."
                        ).classes(TEXT_TOOLTIP_BODY)
            self.separator_toggle = ui.toggle(
                {
                    ",": "Comma (,)",
                    ";": "Semicolon (;)",
                    "|": "Pipe (|)",
                    "\t": "Tab",
                },
                value=session.separator,
            )

        # Row 2: Quote Character
        with ui.row().classes(ROW_LAYOUT):
            with ui.row().classes(ROW_CENTERED_GAP).style(STYLE_LABEL_MIN_WIDTH):
                ui.label("Quote character:").classes(TEXT_FIELD_LABEL)
                with ui.icon("info").classes(ICON_INFO):
                    with (
                        ui.tooltip()
                        .classes(WIDTH_TOOLTIP)
                        .props(gui_props.tooltip_offset)
                    ):
                        ui.label(
                            "A quote character is used to enclose text so that our software "
                            "can recognize it as a continuous block of text, even if it "
                            "contains a comma or a line break. The default quote character "
                            'is a double quote ("), but your dataset might use a single '
                            "quote (')."
                        ).classes(TEXT_TOOLTIP_BODY)
            self.quote_toggle = ui.toggle(
                {
                    '"': 'Double quote (")',
                    "'": "Single quote (')",
                },
                value=session.quote_char,
            )

        # Row 3: Has Header
        with ui.row().classes(ROW_LAYOUT):
            with ui.row().classes(ROW_CENTERED_GAP).style(STYLE_LABEL_MIN_WIDTH):
                ui.label("Has header:").classes(TEXT_FIELD_LABEL)
                with ui.icon("info").classes(ICON_INFO):
                    with (
                        ui.tooltip()
                        .classes(WIDTH_TOOLTIP)
                        .props(gui_props.tooltip_offset)
                    ):
                        ui.label(
                            "Some datasets feature a header row with the title of the "
                            "dataset, which does not contain data in individual columns. "
                            'If your dataset has this, click "yes" here, and vice versa.'
                        ).classes(TEXT_TOOLTIP_BODY)
            self.header_toggle = ui.toggle(
                {True: "Yes", False: "No"},
                value=session.has_header,
            )

        # Row 4: Skip Rows
        with ui.row().classes(ROW_LAYOUT):
            with ui.row().classes(ROW_CENTERED_GAP).style(STYLE_LABEL_MIN_WIDTH):
                ui.label("Skip rows:").classes(TEXT_FIELD_LABEL)
                with ui.icon("info").classes(ICON_INFO):
                    with (
                        ui.tooltip()
                        .classes(WIDTH_TOOLTIP)
                        .props(gui_props.tooltip_offset)
                    ):
                        ui.label(
                            "Some datasets begin with multiple rows that contain titles, "
                            "blurbs, or other irrelevant information. Count the number of "
                            "these rows and enter the corresponding number to skip them"
                        ).classes(TEXT_TOOLTIP_BODY)
            self.skip_rows_input = ui.number(
                label="Number of rows to skip at start",
                value=session.skip_rows,
                min=0,
                max=100,
                step=1,
                precision=0,
                validation={
                    "Must be non-negative": lambda v: v >= 0,
                    "Cannot exceed 100": lambda v: v <= 100,
                },
            ).classes(WIDTH_SKIP_ROWS)

    def _build_excel_controls(self):
        """Build Excel-specific configuration controls."""
        session = self.import_session

        ui.label("Excel Import Options").classes(TEXT_MUTED_SM_MB_2)
        ui.label(f"Sheet: {session.selected_sheet}").classes(TEXT_BASE)

        # Future enhancement: Add sheet selector dropdown
        ui.label("(Sheet selection coming soon)").classes(TEXT_MUTED_SM_MT_2)

    async def _handle_retry(self):
        """Handle retry import button click."""
        try:
            if isinstance(self.import_session, CsvImportSession):
                # Get updated values from controls
                new_separator = self.separator_toggle.value
                new_quote_char = self.quote_toggle.value
                new_has_header = self.header_toggle.value
                new_skip_rows = int(self.skip_rows_input.value)

                # Validate
                if new_skip_rows < 0 or new_skip_rows > 100:
                    ui.notify(
                        "Invalid skip rows value",
                        type="negative",
                        color="negative",
                    )
                    return

                # Create new session with updated config
                updated_session = CsvImportSession(
                    input_file=self.selected_file,
                    separator=new_separator,
                    quote_char=new_quote_char,
                    has_header=new_has_header,
                    skip_rows=new_skip_rows,
                )

                # Call retry callback with updated session
                await self.on_retry(updated_session)

                # Close dialog
                self.close()

            elif isinstance(self.import_session, ExcelImportSession):
                # For Excel, just use existing session (no changes yet)
                await self.on_retry(self.import_session)
                self.close()

        except Exception as e:
            ui.notify(
                f"Error updating configuration: {str(e)}",
                type="negative",
                color="negative",
            )
            print(f"Config update error:\n{format_exc()}")
