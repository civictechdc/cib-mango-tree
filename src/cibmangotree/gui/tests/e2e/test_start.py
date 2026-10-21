"""Start-page interactions, driven by the User fixture.

These stay in-process: create, cancel, and the disabled open/delete buttons
are Python click handlers. Selecting a table row is covered by a Screen test.
"""

from pathlib import Path

from nicegui import ui
from nicegui.testing import User

from cibmangotree.app import App
from cibmangotree.gui.tests.e2e.helpers import click_button, open_app, seed_project


async def test_start_page_shows_project_actions(user: User, ui_app: App) -> None:
    open_app(ui_app)

    await user.open("/")

    await user.should_see("Create New")
    await user.should_see("Open Project")
    await user.should_see("Delete")
    assert ui_app.context.storage._data_dir is not None
    assert Path(ui_app.context.storage.user_data_dir).is_dir()


async def test_create_project_requires_a_name(user: User, ui_app: App) -> None:
    open_app(ui_app)
    await user.open("/")

    user.find("Create New").click()
    await user.should_see("Project Name")
    user.find("Next").click()

    await user.should_see("Please enter a project name")
    assert ui_app.list_projects() == []


async def test_create_project_cancel_stays_on_start(user: User, ui_app: App) -> None:
    session = open_app(ui_app)
    await user.open("/")

    user.find("Create New").click()
    await user.should_see("Create New Project", retries=20)
    click_button(user, "Cancel")

    await user.should_see("Projects")
    assert session.new_project_name is None


async def test_create_project_continues_to_import(user: User, ui_app: App) -> None:
    session = open_app(ui_app)
    await user.open("/")

    user.find("Create New").click()
    await user.should_see("Create New Project", retries=20)
    user.find(kind=ui.input).type("Baseline Project")
    click_button(user, "Next")

    await user.should_see("Choose a dataset file.", retries=20)
    assert session.new_project_name == "Baseline Project"


async def test_open_and_delete_do_nothing_without_a_selection(
    user: User, ui_app: App
) -> None:
    project = seed_project(ui_app, "Kept project")
    open_app(ui_app)
    await user.open("/")

    table = next(iter(user.find(kind=ui.table).elements))
    assert any(row["project_name"] == "Kept project" for row in table.rows)
    click_button(user, "Open Project")
    click_button(user, "Delete")

    await user.should_see("Projects")
    assert [item.display_name for item in ui_app.list_projects()] == [
        project.display_name
    ]
