"""
NiceGUI pytest fixtures and shared GUI session mocks.
"""

from __future__ import annotations

import tempfile
from pathlib import Path
from unittest.mock import MagicMock

import pytest

from cibmangotree.analyzers import suite
from cibmangotree.app import App
from cibmangotree.app.app_context import AppContext
from cibmangotree.gui.context import GUIContext
from cibmangotree.gui.session import GuiSession
from cibmangotree.storage import Storage


@pytest.fixture
def mock_app() -> MagicMock:
    app = MagicMock(spec=App)
    app.list_projects.return_value = []
    suite = MagicMock()
    # Spelling matches analyzer_interface.suite.AnalyzerSuite.primary_anlyzers (production API).
    suite.primary_anlyzers = []
    suite.get_primary_analyzer.return_value = None
    ctx = MagicMock()
    ctx.suite = suite
    ctx.storage = MagicMock()
    app.context = ctx
    return app


@pytest.fixture
def gui_session(mock_app: MagicMock) -> GuiSession:
    return GuiSession(context=GUIContext(app=mock_app))


@pytest.fixture
def mock_project() -> MagicMock:
    proj = MagicMock()
    proj.display_name = "Test Project"
    proj.columns = []
    proj.column_dict = {}
    proj.list_analyses = MagicMock(return_value=[])
    return proj


@pytest.fixture
def gui_session_with_project(
    mock_app: MagicMock, mock_project: MagicMock
) -> GuiSession:
    session = GuiSession(context=GUIContext(app=mock_app))
    session.current_project = mock_project
    return session


@pytest.fixture
def ui_data_dir():
    """Temporary project storage for one UI test.

    Storage otherwise writes to the real platform data directory. This directory
    is removed when the test ends, so a create or delete cannot change projects
    on the machine running the suite. On CI the runner is discarded too; the
    per-test directory still keeps tests from sharing one project list.
    """
    with tempfile.TemporaryDirectory(prefix="cibmt-ui-") as directory:
        root = Path(directory)
        (root / "data").mkdir()
        (root / "cache").mkdir()
        yield root


@pytest.fixture
def ui_app(ui_data_dir: Path) -> App:
    """Real app pointed at ui_data_dir.

    The database is closed before the directory is deleted so Windows can
    remove the TinyDB file.
    """
    storage = Storage(
        app_name="MangoTango",
        app_author="Civic Tech DC",
        data_dir=str(ui_data_dir / "data"),
        cache_dir=str(ui_data_dir / "cache"),
    )
    app = App(context=AppContext(storage=storage, suite=suite))
    yield app
    storage.close()
