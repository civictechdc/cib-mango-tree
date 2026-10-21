"""Import and preview interactions, driven by the User fixture.

The file is attached on the session. These tests cover the confirmation
dialog, import settings, and creating the project. Home records whether the
leave dialog appears for each import session state.
"""

from io import BytesIO

from nicegui.testing import User

from cibmangotree.app import App
from cibmangotree.gui.tests.e2e.helpers import (
    HASHTAG_CSV,
    attach_csv,
    click_button,
    click_icon,
    open_app,
    seed_project,
)


async def test_import_page_prompts_for_a_file(user: User, ui_app: App) -> None:
    open_app(ui_app)
    await user.open("/import_dataset")

    await user.should_see("Choose a dataset file.")
    await user.should_see("Browse Files")


async def test_leaving_import_after_a_file_asks_for_confirmation(
    user: User, ui_app: App
) -> None:
    session = open_app(ui_app)
    session.selected_file = BytesIO(HASHTAG_CSV.read_bytes())
    session.selected_file_name = HASHTAG_CSV.name
    await user.open("/import_dataset")

    click_icon(user, "home")
    await user.should_see("Leave anyway?", retries=20)

    click_button(user, "Stay")
    await user.should_see("Choose a dataset file.")


async def test_confirming_leave_returns_home(user: User, ui_app: App) -> None:
    session = open_app(ui_app)
    session.selected_file = BytesIO(b"a,b\n1,2\n")
    session.selected_file_name = "notes.csv"
    await user.open("/import_dataset")

    click_icon(user, "home")
    await user.should_see("Leave anyway?", retries=20)
    click_button(user, "Leave")

    await user.should_see("Projects", retries=20)


async def test_preview_offers_fix_and_proceed(user: User, ui_app: App) -> None:
    session = open_app(ui_app)
    attach_csv(session)
    await user.open("/preview_dataset")

    await user.should_see("Looks good, let's proceed", retries=20)
    user.find("There's something wrong").click()
    await user.should_see("Column separator:")
    user.find("Cancel").click()
    await user.should_see("Data Preview (first 5 rows)")


async def test_preview_proceed_creates_the_project(user: User, ui_app: App) -> None:
    session = open_app(ui_app)
    session.new_project_name = "Imported project"
    attach_csv(session)
    await user.open("/preview_dataset")

    user.find("Looks good, let's proceed").click()

    await user.should_see("Hashtag analysis", retries=30)
    assert ui_app.list_projects()[0].display_name == "Imported project"
    assert session.current_project is not None


async def test_preview_redirects_when_no_file_selected(user: User, ui_app: App) -> None:
    """Opening the preview with no file selected sends the user back.

    The page shows "No file selected. Redirecting" instead of a data grid.
    """
    open_app(ui_app)
    await user.open("/preview_dataset")

    await user.should_see("No file selected. Redirecting", retries=20)


async def test_preview_redirects_when_format_not_detected(
    user: User, ui_app: App
) -> None:
    """A file whose type is not CSV or Excel cannot be previewed.

    The session holds a non-CSV payload named x.bin. The page reports
    "Could not detect file format" and does not build a grid.
    """
    session = open_app(ui_app)
    session.selected_file = BytesIO(b"x")
    session.selected_file_name = "x.bin"
    session.selected_file_content_type = "application/octet-stream"
    await user.open("/preview_dataset")

    await user.should_see("Could not detect file format", retries=20)


async def test_leaving_import_with_nothing_chosen_goes_home(
    user: User, ui_app: App
) -> None:
    """Home leaves import directly when no file and no project are chosen."""
    open_app(ui_app)
    await user.open("/import_dataset")

    click_icon(user, "home")

    await user.should_see("Projects", retries=20)


async def test_leaving_import_of_a_stored_project_goes_home(
    user: User, ui_app: App
) -> None:
    """A project opened from storage can be left without a confirmation dialog."""
    project = seed_project(ui_app, "Stored import project")
    session = open_app(ui_app)
    session.current_project = project
    session.project_loaded_from_storage = True
    await user.open("/import_dataset")

    click_icon(user, "home")

    await user.should_see("Projects", retries=20)


async def test_leaving_a_fresh_project_on_import_asks_for_confirmation(
    user: User, ui_app: App
) -> None:
    """A project created in this session asks before Home leaves import."""
    project = seed_project(ui_app, "Fresh import project")
    session = open_app(ui_app)
    session.current_project = project
    session.project_loaded_from_storage = False
    await user.open("/import_dataset")

    click_icon(user, "home")

    await user.should_see("No project has been created yet. Leave anyway?", retries=20)
