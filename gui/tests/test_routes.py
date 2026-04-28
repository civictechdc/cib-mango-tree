"""Behavior tests for gui.routes."""

from gui.routes import GuiRoutes, gui_routes


def test_gui_routes_default_paths() -> None:
    routes = GuiRoutes()
    assert routes.root == "/"
    assert routes.dashboard == "/dashboard"
    assert routes.configure_analysis == "/configure_analysis"


def test_gui_routes_singleton_matches_defaults() -> None:
    assert gui_routes.import_dataset == "/import_dataset"
    assert gui_routes.preview_dataset == "/preview_dataset"
