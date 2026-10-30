"""
Main entry point for CIB Mango Tree application.
Bootstraps core services and launches the GUI.
"""

import argparse
import logging
import multiprocessing
import sys
from multiprocessing import freeze_support
from pathlib import Path

import platformdirs


def main() -> None:
    freeze_support()

    multiprocessing.set_start_method("spawn", force=True)

    # clear Mark of the Web for Win .exe
    if sys.platform == "win32":
        from cibmangotree.gui.utils import _remove_motw

        _remove_motw()

    # Import heavy modules after loading message
    parser = argparse.ArgumentParser(description="CIB Mango Tree")
    parser.add_argument(
        "--noop", action="store_true", help="No-operation mode for testing"
    )
    args = parser.parse_args()

    # Import heavy modules
    from cibmangotree.analyzers import suite
    from cibmangotree.app import App, AppContext
    from cibmangotree.app.logger import setup_logging
    from cibmangotree.app.storage_migration import (
        StorageMigrationStatus,
        storage_directory_migration,
    )
    from cibmangotree.gui import gui_main
    from cibmangotree.meta import get_version
    from cibmangotree.storage import Storage

    if args.noop:
        print("No-op flag detected. All runtime imports loaded successfully.")
        sys.exit(0)

    # Check directory for old users
    old_directory = Path(platformdirs.user_data_dir("MangoTango", "Civic Tech DC"))
    newest_directory = Path(
        platformdirs.user_data_dir("CIB Mango Tree", "Civic Tech DC")
    )
    migration_result = storage_directory_migration(old_directory, newest_directory)
    if migration_result == StorageMigrationStatus.ERROR:
        name = "MangoTango"
    else:
        name = "CIB Mango Tree"

    # Initialize storage
    storage = Storage(app_name=name, app_author="Civic Tech DC")

    # Set up logging
    log_level = logging.INFO
    log_file_path = Path(storage.user_data_dir) / "logs" / "cib-mango-tree.log"
    app_version = get_version() or "development"
    setup_logging(log_file_path, log_level, app_version)

    # Get logger for main module
    logger = logging.getLogger(__name__)
    logger.info("Starting CIB Mango Tree application")

    # Log Migration Status
    logger.info(f"Storage migration result: {migration_result.name}")
    if migration_result in (
        StorageMigrationStatus.CONFLICT,
        StorageMigrationStatus.ERROR,
    ):
        logger.warning(
            f"Legacy data folder not migrated. Old: {old_directory}. New: {newest_directory}"
        )

    # Create App instance
    app = App(context=AppContext(storage=storage, suite=suite))

    # Launch GUI
    gui_main(app=app)


if __name__ == "__main__":
    main()
