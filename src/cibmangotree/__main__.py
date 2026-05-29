"""
Main entry point for CIB Mango Tree application.
Bootstraps core services and launches the GUI.
"""

import argparse
import logging
import sys
from multiprocessing import freeze_support
from pathlib import Path


def main() -> None:
    freeze_support()

    parser = argparse.ArgumentParser(description="CIB Mango Tree")
    parser.add_argument(
        "--noop", action="store_true", help="No-operation mode for testing"
    )
    args = parser.parse_args()

    # Import heavy modules
    from cibmangotree.analyzers import suite
    from cibmangotree.app import App, AppContext
    from cibmangotree.app.logger import setup_logging
    from cibmangotree.gui import gui_main
    from cibmangotree.meta import get_version
    from cibmangotree.storage import Storage

    if args.noop:
        print("No-op flag detected. All runtime imports loaded successfully.")
        sys.exit(0)

    # Initialize storage
    storage = Storage(app_name="MangoTango", app_author="Civic Tech DC")

    # Set up logging
    log_level = logging.INFO
    log_file_path = Path(storage.user_data_dir) / "logs" / "mangotango.log"
    app_version = get_version() or "development"
    setup_logging(log_file_path, log_level, app_version)

    # Get logger for main module
    logger = logging.getLogger(__name__)
    logger.info("Starting CIB Mango Tree application")

    # Create App instance
    app = App(context=AppContext(storage=storage, suite=suite))

    # Launch GUI
    gui_main(app=app)


if __name__ == "__main__":
    main()
