"""Root pytest hooks: NiceGUI plugins must load from top-level conftest (pytest policy)."""

import logging
import os
from collections.abc import Generator
from pathlib import Path

import pytest
from selenium import webdriver
from selenium.webdriver.chrome.service import Service

from cibmangotree.gui.tests.chrome_shell import chrome_headless_shell

# Plugins must be listed here. Pytest does not load pytest_plugins from nested conftest files.
# user_plugin drives Python UI actions in-process. screen_plugin is for actions that only
# exist in the page (file input, table rows, grids, charts). The browser starts only when
# a test requests the screen fixture. nicegui_chrome_options below replaces NiceGUI's
# fixture so that browser is chrome-headless-shell, which has no Dock icon.
pytest_plugins = (
    "nicegui.testing.general_fixtures",
    "nicegui.testing.user_plugin",
    "nicegui.testing.screen_plugin",
)


@pytest.fixture(scope="session")
def nicegui_chrome_options() -> webdriver.ChromeOptions:
    """Screen-test browser options aimed at chrome-headless-shell.

    The flags match NiceGUI's own fixture. The binary does not: Google Chrome
    remains a Dock app when launched with --headless.
    """
    from nicegui.testing.screen_plugin import DOWNLOAD_DIR

    assert DOWNLOAD_DIR is not None, "pytest_configure must run before this fixture"
    chrome_options = webdriver.ChromeOptions()
    chrome_options.add_argument("disable-dev-shm-usage")
    chrome_options.add_argument("disable-search-engine-choice-screen")
    chrome_options.add_argument("no-sandbox")
    chrome_options.add_argument("headless")
    # The shell has no display. --disable-gpu stops its GPU process, and the
    # first canvas page then never answers on Linux and Windows. Bare
    # --use-gl=angle stalls this shell, so the backend is SwiftShader.
    chrome_options.add_argument("use-gl=angle")
    chrome_options.add_argument("use-angle=swiftshader")
    chrome_options.add_argument("enable-unsafe-swiftshader")
    chrome_options.add_argument("window-size=600x600")
    chrome_options.add_experimental_option(
        "prefs",
        {
            "download.default_directory": str(DOWNLOAD_DIR),
            "download.prompt_for_download": False,
            "download.directory_upgrade": True,
        },
    )
    chrome_options.set_capability("goog:loggingPrefs", {"browser": "ALL"})
    chrome_options.binary_location = str(chrome_headless_shell())
    return chrome_options


def _path_without_chromedriver() -> str:
    """Drop PATH entries that contain chromedriver.

    Selenium Manager uses a chromedriver it finds on PATH. GitHub's macOS
    image ships an older one than the chrome-headless-shell these tests
    download, and that mismatch prevents the browser from starting.
    """
    name = "chromedriver.exe" if os.name == "nt" else "chromedriver"
    kept = [
        entry
        for entry in os.environ.get("PATH", "").split(os.pathsep)
        if entry and not (Path(entry) / name).is_file()
    ]
    return os.pathsep.join(kept)


@pytest.fixture(scope="session")
def nicegui_driver(
    nicegui_chrome_options: webdriver.ChromeOptions,
) -> Generator[webdriver.Chrome, None, None]:
    """Start one chrome-headless-shell for the whole session.

    NiceGUI's driver gives the first page 4 seconds. The shell's first load
    can take longer than that, so this raises the limit.
    """
    from nicegui.testing.screen import Screen

    env = os.environ.copy()
    env["PATH"] = _path_without_chromedriver()
    previous = os.environ.get("PATH")
    os.environ["PATH"] = env["PATH"]
    try:
        driver = webdriver.Chrome(
            service=Service(env=env),
            options=nicegui_chrome_options,
        )
    except Exception as exc:
        raise RuntimeError("Could not start chrome-headless-shell.") from exc
    finally:
        if previous is None:
            os.environ.pop("PATH", None)
        else:
            os.environ["PATH"] = previous
    # A stuck renderer never returns a WebDriver command. The waits in the
    # tests only run after that command returns, so each command is capped.
    driver.command_executor._client_config.timeout = 30
    driver.set_script_timeout(30)
    driver.implicitly_wait(Screen.IMPLICIT_WAIT)
    driver.set_page_load_timeout(20)
    yield driver
    driver.quit()


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
