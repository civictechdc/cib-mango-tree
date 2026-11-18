"""Unit tests for project/analysis persistence and a single export format."""

from __future__ import annotations

from pathlib import Path

import polars as pl
import pytest

from cibmangotree.analyzer_interface.interface import AnalyzerOutput, OutputColumn
from cibmangotree.storage import Storage


@pytest.fixture
def storage(tmp_path: Path) -> Storage:
    store = Storage(
        app_name="CIB Mango Tree Test",
        app_author="Civic Tech DC",
        data_dir=str(tmp_path / "data"),
        cache_dir=str(tmp_path / "cache"),
    )
    yield store
    store.close()


def _temp_input_parquet(path: Path) -> Path:
    frame = pl.DataFrame({"author": ["a", "b"], "text": ["hello", "world"]})
    frame.write_parquet(path)
    return path


def test_project_crud_and_input_roundtrip(storage: Storage, tmp_path: Path) -> None:
    incoming = _temp_input_parquet(tmp_path / "incoming.parquet")
    project = storage.init_project(
        display_name="Demo Project",
        input_temp_file=str(incoming),
        dataset_name="demo.csv",
    )

    listed = storage.list_projects()
    assert [p.id for p in listed] == [project.id]
    assert listed[0].display_name == "Demo Project"
    assert listed[0].dataset_name == "demo.csv"

    loaded = storage.load_project_input(project.id)
    assert loaded.to_dict(as_series=False) == {
        "author": ["a", "b"],
        "text": ["hello", "world"],
    }

    storage.rename_project(project.id, "Renamed Project")
    assert storage.list_projects()[0].display_name == "Renamed Project"

    storage.delete_project(project.id)
    assert storage.list_projects() == []
    assert not Path(storage.user_data_dir, "projects", project.id).exists()


def test_analysis_crud(storage: Storage, tmp_path: Path) -> None:
    project = storage.init_project(
        display_name="Analysis Host",
        input_temp_file=str(_temp_input_parquet(tmp_path / "input.parquet")),
    )

    analysis = storage.init_analysis(
        project.id,
        "First run",
        "example",
        column_mapping={"text": "message"},
        param_values={"window": 3},
    )
    assert analysis.is_draft is True
    assert analysis.param_values == {"window": 3}

    listed = storage.list_project_analyses(project.id)
    assert len(listed) == 1
    assert listed[0].analysis_id == analysis.analysis_id

    analysis.is_draft = False
    analysis.display_name = "First run saved"
    storage.save_analysis(analysis)
    saved = storage.list_project_analyses(project.id)[0]
    assert saved.is_draft is False
    assert saved.display_name == "First run saved"

    storage.delete_analysis(analysis)
    assert storage.list_project_analyses(project.id) == []


def test_export_primary_output_as_csv(storage: Storage, tmp_path: Path) -> None:
    project = storage.init_project(
        display_name="Export Host",
        input_temp_file=str(_temp_input_parquet(tmp_path / "input.parquet")),
    )
    analysis = storage.init_analysis(
        project.id,
        "Export run",
        "example",
        column_mapping={},
        param_values={},
    )

    output_id = "summary"
    parquet_path = Path(storage.get_primary_output_parquet_path(analysis, output_id))
    parquet_path.parent.mkdir(parents=True, exist_ok=True)
    pl.DataFrame({"count": [1, 2], "label": ["x", "y"]}).write_parquet(parquet_path)

    spec = AnalyzerOutput(
        id=output_id,
        name="Summary",
        columns=[
            OutputColumn(
                name="count", data_type="integer", human_readable_name="Count"
            ),
            OutputColumn(name="label", data_type="text", human_readable_name="Label"),
        ],
    )

    export = storage.export_project_primary_output(
        analysis,
        output_id,
        extension="csv",
        spec=spec,
    )
    with pytest.raises(StopIteration) as finished:
        while True:
            next(export)
    exported = finished.value.value
    assert exported.endswith(".csv")
    assert Path(exported).is_file()

    exported_df = pl.read_csv(exported)
    assert list(exported_df.columns) == ["Count", "Label"]
    assert exported_df.to_dict(as_series=False) == {
        "Count": [1, 2],
        "Label": ["x", "y"],
    }
