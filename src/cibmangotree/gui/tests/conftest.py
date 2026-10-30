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


def _release_analysis_workers() -> None:
    """Stop analysis worker processes so they release the test database.

    A finished run stays in NiceGUI's process pool. On Windows that keeps
    db.json open, and the temporary project directory cannot be removed.
    """
    from nicegui import run as nicegui_run

    pool = nicegui_run.process_pool
    if pool is None or not getattr(pool, "_processes", None):
        return
    pool.shutdown(wait=True, cancel_futures=True)
    nicegui_run.process_pool = None
    nicegui_run.setup()


@pytest.fixture
def ui_app(ui_data_dir: Path) -> App:
    """Real app pointed at ui_data_dir.

    The database is closed, and any analysis worker is stopped, before the
    directory is deleted. Windows cannot remove a TinyDB file that is still open.
    """
    storage = Storage(
        app_name="CIB Mango Tree",
        app_author="Civic Tech DC",
        data_dir=str(ui_data_dir / "data"),
        cache_dir=str(ui_data_dir / "cache"),
    )
    app = App(context=AppContext(storage=storage, suite=suite))
    yield app
    storage.close()
    _release_analysis_workers()
