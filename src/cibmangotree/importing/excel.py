from io import BytesIO
from typing import cast

import polars as pl
from fastexcel import read_excel
from pydantic import BaseModel, ConfigDict

from .importer import Importer, ImporterSession


class ExcelImporter(Importer["ExcelImportSession"]):
    @property
    def name(self) -> str:
        return "Excel"

    def suggest(self, input_path: str) -> bool:
        return (
            input_path.endswith(".xlsx")
            or input_path
            == "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )

    def init_session(self, input_path: str | BytesIO):
        """
        Initialize Excel import session.

        For single-sheet files, automatically selects the sheet.
        For multi-sheet files, returns None (caller must provide sheet selection).
        """
        reader = read_excel(
            cast(str, input_path)
            if type(input_path) is not BytesIO
            else input_path.getvalue()
        )
        sheet_names = reader.sheet_names

        if not sheet_names or (len(sheet_names) == 0 or len(sheet_names) > 1):
            return None

        return ExcelImportSession(
            input_file=input_path,
            selected_sheet=sheet_names[0],
            sheet_names=sheet_names,
        )


class ExcelImportSession(ImporterSession, BaseModel):
    input_file: str | BytesIO
    selected_sheet: str
    sheet_names: list[str]

    model_config = ConfigDict(arbitrary_types_allowed=True)

    def load_preview(self, n_records: int) -> pl.DataFrame:
        return pl.read_excel(self.input_file, sheet_name=self.selected_sheet).head(
            n_records
        )

    def import_as_parquet(self, output_path: str) -> None:
        return pl.read_excel(
            self.input_file, sheet_name=self.selected_sheet
        ).write_parquet(output_path)
