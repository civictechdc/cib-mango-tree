"""Behavior tests for gui.context.GUIContext."""

from unittest.mock import MagicMock

from app import App
from gui.context import GUIContext


def test_gui_context_holds_app_reference() -> None:
    app = MagicMock(spec=App)
    ctx = GUIContext(app=app)
    assert ctx.app is app
