"""
NiceGUI pytest fixtures and shared GUI session mocks.
"""

from __future__ import annotations

from unittest.mock import MagicMock

import pytest

from app import App
from gui.context import GUIContext
from gui.session import GuiSession


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
