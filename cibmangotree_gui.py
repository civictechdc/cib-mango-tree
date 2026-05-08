"""
GUI entry point for CIB Mango Tree application.
This launches the NiceGUI interface in native window mode.
"""

import sys
from pathlib import Path

# Redirect stdout/stderr to a crash log for debugging frozen Windows builds.
# Must be set before any imports to catch pywebview/nicegui startup errors.
if getattr(sys, "frozen", False):
    _crash_log = Path(sys.executable).parent / "mango_crash.log"
    sys.stdout = open(_crash_log, "w", encoding="utf-8")
    sys.stderr = sys.stdout

import logging
from multiprocessing import freeze_support
from pathlib import Path

if __name__ == "__main__":
    freeze_support()

    # Import heavy modules after loading message
    from analyzers import suite
    from app import App, AppContext
    from app.logger import setup_logging
    from gui import gui_main
    from meta import get_version
    from storage import Storage

    # Initialize storage
    storage = Storage(app_name="MangoTango", app_author="Civic Tech DC")

    # Set up logging
    log_level = logging.INFO
    log_file_path = Path(storage.user_data_dir) / "logs" / "mangotango.log"
    app_version = get_version() or "development"
    setup_logging(log_file_path, log_level, app_version)

    # Get logger for main module
    logger = logging.getLogger(__name__)
    logger.info("Starting CIB Mango Tree GUI application")

    # Create App instance
    app = App(context=AppContext(storage=storage, suite=suite))

    # Launch GUI
    gui_main(app=app)
