"""Root pytest hooks: NiceGUI plugins must load from top-level conftest (pytest policy)."""

import logging

import pytest

pytest_plugins = (
    "nicegui.testing.general_fixtures",
    "nicegui.testing.user_plugin",
)


@pytest.fixture(autouse=True)
def cleanup_logging():
    """Close and remove all logging handlers after each test.

    Prevents Windows file-lock errors when TemporaryDirectory tries to delete
    log files that are still held open by RotatingFileHandler.
    """
    yield
    root_logger = logging.getLogger()
    for handler in root_logger.handlers[:]:
        handler.close()
        root_logger.removeHandler(handler)
    root_logger.setLevel(logging.WARNING)
