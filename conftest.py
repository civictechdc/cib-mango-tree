"""Root pytest hooks: NiceGUI plugins must load from top-level conftest (pytest policy)."""

pytest_plugins = (
    "nicegui.testing.general_fixtures",
    "nicegui.testing.user_plugin",
)
