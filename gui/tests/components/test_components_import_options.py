"""Behavior tests for gui.components.import_options.ImportOptionsDialog."""

from io import BytesIO

import pytest
from nicegui import ui

from gui.components.import_options import ImportOptionsDialog
from importing.csv import CsvImportSession


@pytest.mark.asyncio
async def test_import_options_dialog_builds_csv_controls(user) -> None:
    session = CsvImportSession(
        input_file=BytesIO(b"a,b\n1,2"),
        separator=",",
        quote_char='"',
    )

    @ui.page("/iod")
    def page() -> None:
        ImportOptionsDialog(
            import_session=session,
            selected_file=BytesIO(b"a,b\n1,2"),
            on_retry=lambda _s: None,
        )

    await user.open("/iod")
    await user.should_see("Import Configuration")
    await user.should_see("Column separator:")
