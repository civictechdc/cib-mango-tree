"""Unit tests for ExcelImporter happy path."""

from __future__ import annotations

from pathlib import Path

import polars as pl
import pytest
from xlsxwriter import Workbook

from cibmangotree.importing.excel import ExcelImporter


@pytest.fixture
def importer() -> ExcelImporter:
    return ExcelImporter()


def _write_single_sheet_xlsx(path: Path) -> Path:
    pl.DataFrame({"author": ["alice", "bob"], "text": ["hi", "yo"]}).write_excel(path)
    return path


def _write_multi_sheet_xlsx(path: Path) -> Path:
    with Workbook(path) as workbook:
        sheet_a = workbook.add_worksheet("First")
        sheet_a.write_row(0, 0, ["a", "b"])
        sheet_a.write_row(1, 0, [1, 2])
        sheet_b = workbook.add_worksheet("Second")
        sheet_b.write_row(0, 0, ["c", "d"])
        sheet_b.write_row(1, 0, [3, 4])
    return path


def test_suggest_recognizes_xlsx(importer: ExcelImporter) -> None:
    assert importer.suggest("dataset.xlsx")
    assert importer.suggest(
        "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )
    assert not importer.suggest("dataset.csv")


def test_single_sheet_session_preview_and_parquet(
    importer: ExcelImporter, tmp_path: Path
) -> None:
    xlsx_path = _write_single_sheet_xlsx(tmp_path / "single.xlsx")
    session = importer.init_session(str(xlsx_path))
    assert session is not None
    assert session.selected_sheet in session.sheet_names
    assert len(session.sheet_names) == 1

    preview = session.load_preview(10)
    assert list(preview.columns) == ["author", "text"]
    assert preview.height == 2
    assert preview.row(0) == ("alice", "hi")

    parquet_path = tmp_path / "out.parquet"
    session.import_as_parquet(str(parquet_path))
    imported = pl.read_parquet(parquet_path)
    assert imported.to_dict(as_series=False) == {
        "author": ["alice", "bob"],
        "text": ["hi", "yo"],
    }


def test_multi_sheet_requires_manual_selection(
    importer: ExcelImporter, tmp_path: Path
) -> None:
    xlsx_path = _write_multi_sheet_xlsx(tmp_path / "multi.xlsx")
    assert importer.init_session(str(xlsx_path)) is None
