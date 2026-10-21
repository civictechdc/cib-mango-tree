"""Root pytest hooks: NiceGUI plugins must load from top-level conftest (pytest policy)."""

import logging
import shutil
from collections.abc import Generator

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
    # The shell has no display. NiceGUI's local --use-gl=angle flag is for the
    # Chrome app and stalls this shell's renderer on the first page.
    chrome_options.add_argument("disable-gpu")
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


@pytest.fixture(scope="session")
def nicegui_driver(
    nicegui_chrome_options: webdriver.ChromeOptions,
) -> Generator[webdriver.Chrome, None, None]:
    """Start one chrome-headless-shell for the whole session.

    NiceGUI's driver gives the first page 4 seconds. The shell's first load
    can take longer than that, so this raises the limit.
    """
    from nicegui.testing.screen import Screen

    for executable_path in (None, shutil.which("chromedriver"), "chromedriver"):
        try:
            driver = webdriver.Chrome(
                service=Service(executable_path=executable_path),
                options=nicegui_chrome_options,
            )
            break
        except Exception:
            continue
    else:
        raise RuntimeError("Could not start chrome-headless-shell.")
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
