"""Behavior tests for gui.context.GUIContext."""

from unittest.mock import MagicMock

from gui.context import GUIContext

from cibmangotree.app import App


def test_gui_context_holds_app_reference() -> None:
    app = MagicMock(spec=App)
    ctx = GUIContext(app=app)
    assert ctx.app is app
