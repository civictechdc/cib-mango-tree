"""Tests for exit confirmation behavior with loaded-from-storage flags."""

from unittest.mock import MagicMock

from cibmangotree.app import App
from cibmangotree.gui.context import GUIContext
from cibmangotree.gui.pages.analysis_config_and_run import AnalysisConfigAndRunPage
from cibmangotree.gui.pages.importer import ImportDatasetPage
from cibmangotree.gui.session import GuiSession


def _make_session() -> GuiSession:
    app = MagicMock(spec=App)
    app.list_projects.return_value = []
    suite = MagicMock()
    suite.primary_anlyzers = []
    suite.get_primary_analyzer.return_value = None
    ctx = MagicMock()
    ctx.suite = suite
    ctx.storage = MagicMock()
    app.context = ctx
    return GuiSession(context=GUIContext(app=app))


def _make_session_with_project() -> GuiSession:
    project = MagicMock()
    project.display_name = "Test Project"

    session = _make_session()
    session.current_project = project
    return session


def test_import_no_confirmation_when_no_state() -> None:
    session = _make_session()
    page = ImportDatasetPage(session=session)
    assert page.requires_exit_confirmation() is False


def test_import_confirmation_when_file_selected() -> None:
    session = _make_session()
    session.selected_file = MagicMock()
    page = ImportDatasetPage(session=session)
    assert page.requires_exit_confirmation() is True


def test_import_no_confirmation_when_project_loaded_from_storage() -> None:
    session = _make_session_with_project()
    session.project_loaded_from_storage = True
    page = ImportDatasetPage(session=session)
    assert page.requires_exit_confirmation() is False


def test_import_confirmation_when_project_created_fresh() -> None:
    session = _make_session_with_project()
    session.project_loaded_from_storage = False
    page = ImportDatasetPage(session=session)
    assert page.requires_exit_confirmation() is True


def test_analysis_config_no_confirmation_when_no_state() -> None:
    session = _make_session()
    page = AnalysisConfigAndRunPage(session=session)
    assert page.requires_exit_confirmation() is False


def test_analysis_config_confirmation_when_analyzer_selected() -> None:
    session = _make_session()
    session.selected_analyzer = MagicMock()
    page = AnalysisConfigAndRunPage(session=session)
    assert page.requires_exit_confirmation() is True


def test_analysis_config_no_confirmation_when_loaded_from_storage() -> None:
    session = _make_session_with_project()
    session.selected_analyzer = MagicMock()
    session.analysis_loaded_from_storage = True
    page = AnalysisConfigAndRunPage(session=session)
    assert page.requires_exit_confirmation() is False


def test_analysis_config_confirmation_when_configured_fresh() -> None:
    session = _make_session_with_project()
    session.selected_analyzer = MagicMock()
    session.analysis_loaded_from_storage = False
    page = AnalysisConfigAndRunPage(session=session)
    assert page.requires_exit_confirmation() is True
