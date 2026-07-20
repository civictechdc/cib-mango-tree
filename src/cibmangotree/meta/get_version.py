import sys
from pathlib import Path


def get_version():
    """Return version string if running as a bundled app, else None.

    Bundled apps have a VERSION file at the root of the PyInstaller
    extraction directory (sys._MEIPASS). Development runs always
    return None so the GUI shows "dev".
    """
    if getattr(sys, "frozen", False):
        version_path = Path(sys._MEIPASS) / "VERSION"
        if version_path.exists():
            return version_path.read_text().strip()
    return None


def is_distributed():
    return get_version() is not None


def is_development():
    return not is_distributed()
