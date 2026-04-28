"""Behavior tests for gui.session.GuiSession."""

from io import BytesIO
from pathlib import Path
from unittest.mock import MagicMock

from gui.context import GUIContext
from gui.session import GuiSession


def test_reset_project_workflow_clears_project_import_fields(
    mock_app: MagicMock,
) -> None:
    session = GuiSession(context=GUIContext(app=mock_app))
    session.new_project_name = "p"
    session.selected_file_path = Path("/tmp/x.csv")
    session.import_session = MagicMock()

    session.reset_project_workflow()

    assert session.new_project_name is None
    assert session.selected_file_path is None
    assert session.import_session is None


def test_reset_analysis_workflow_clears_analysis_fields(mock_app: MagicMock) -> None:
    session = GuiSession(context=GUIContext(app=mock_app))
    session.selected_analyzer = MagicMock()
    session.selected_analyzer_name = "ngrams"
    session.column_mapping = {"a": "b"}
    session.current_analysis = MagicMock()

    session.reset_analysis_workflow()

    assert session.selected_analyzer is None
    assert session.selected_analyzer_name is None
    assert session.column_mapping is None
    assert session.current_analysis is None


def test_validate_project_selected_and_file_and_name(mock_app: MagicMock) -> None:
    session = GuiSession(context=GUIContext(app=mock_app))
    assert session.validate_project_selected() is False
    session.current_project = MagicMock()
    assert session.validate_project_selected() is True

    session2 = GuiSession(context=GUIContext(app=mock_app))
    assert session2.validate_file_selected() is False
    session2.selected_file = BytesIO(b"x")
    assert session2.validate_file_selected() is True

    session3 = GuiSession(context=GUIContext(app=mock_app))
    assert session3.validate_project_name_set() is False
    session3.new_project_name = "  "
    assert session3.validate_project_name_set() is False
    session3.new_project_name = "ok"
    assert session3.validate_project_name_set() is True
