"""Shared setup for GUI end-to-end tests.

Tests call open_app and then click through Python handlers.
"""

from io import BytesIO
from pathlib import Path

from nicegui import ui
from nicegui.testing import User
from nicegui.testing.user_interaction import UserInteraction

from cibmangotree.app import App
from cibmangotree.gui.main_workflow import register_pages
from cibmangotree.gui.session import GuiSession
from cibmangotree.importing.csv import CSVImporter

HASHTAG_CSV = (
    Path(__file__).resolve().parents[3]
    / "analyzers"
    / "hashtags"
    / "test_data"
    / "hashtag_test_input.csv"
)


def open_app(app: App) -> GuiSession:
    return register_pages(app)


def seed_project(app: App, name: str):
    importer = CSVImporter().init_session(str(HASHTAG_CSV))
    return app.create_project(name, importer, dataset_name=HASHTAG_CSV.name)


def attach_csv(session: GuiSession) -> None:
    session.selected_file = BytesIO(HASHTAG_CSV.read_bytes())
    session.selected_file_name = HASHTAG_CSV.name
    session.selected_file_content_type = "text/csv"


def click_icon(user: User, icon: str) -> None:
    button = next(
        element
        for element in user.find(kind=ui.button).elements
        if element.props.get("icon") == icon
    )
    UserInteraction(user, {button}, None).click()


def click_button(user: User, label: str) -> None:
    matches = [
        element
        for element in user.find(kind=ui.button).elements
        if element.text == label
    ]
    button = min(matches, key=lambda element: element.id)
    UserInteraction(user, {button}, None).click()
