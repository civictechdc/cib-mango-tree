"""Shared setup for GUI end-to-end tests.

User tests call open_app and then click through Python handlers. Screen tests
use the same pages, then drive the hidden browser for actions the handlers
cannot perform on their own.
"""

from io import BytesIO
from multiprocessing import Manager
from pathlib import Path

from nicegui import ui
from nicegui.testing import User
from nicegui.testing.user_interaction import UserInteraction

from cibmangotree.analyzer_interface.params import TimeBinningValue
from cibmangotree.analyzers.hashtags.hashtags_base.interface import (
    interface as hashtags_interface,
)
from cibmangotree.analyzers.ngrams.ngrams_base.interface import (
    interface as ngrams_interface,
)
from cibmangotree.app import App
from cibmangotree.app.analysis_context import AnalysisContext
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
NGRAM_CSV = (
    Path(__file__).resolve().parents[3]
    / "analyzers"
    / "ngrams"
    / "test_data"
    / "ngrams_test_input.csv"
)


def open_app(app: App) -> GuiSession:
    return register_pages(app)


def seed_project(app: App, name: str):
    importer = CSVImporter().init_session(str(HASHTAG_CSV))
    return app.create_project(name, importer, dataset_name=HASHTAG_CSV.name)


def seed_completed_hashtag_analysis(app: App, name: str):
    return _seed_completed_analysis(
        app,
        name,
        hashtags_interface,
        HASHTAG_CSV,
        {"time_window": TimeBinningValue(unit="day", amount=1)},
    )


def seed_completed_ngram_analysis(app: App, name: str):
    return _seed_completed_analysis(
        app,
        name,
        ngrams_interface,
        NGRAM_CSV,
        {"min_n": 3, "max_n": 5},
    )


def _seed_completed_analysis(app: App, name: str, interface, csv_path: Path, params):
    importer = CSVImporter().init_session(str(csv_path))
    project = app.create_project(name, importer, dataset_name=csv_path.name)
    column_mapping = {
        column.name: column.name
        for column in interface.input.columns
        if column.name in project.column_dict
    }
    missing = [
        column.name
        for column in interface.input.columns
        if column.name not in column_mapping
    ]
    if missing:
        raise RuntimeError(f"{interface.name} columns were not imported: {missing}")

    analysis = project.create_analysis(interface.id, column_mapping, params)
    input_columns_data = {
        analyzer_column: (
            user_column,
            project.column_dict[user_column].semantic.semantic_name,
        )
        for analyzer_column, user_column in column_mapping.items()
    }
    secondary_ids = [
        spec.id
        for spec in app.context.suite.find_toposorted_secondary_analyzers(interface)
    ]
    manager = Manager()
    result = AnalysisContext.run_worker(
        analysis.model,
        interface.id,
        column_mapping,
        input_columns_data,
        secondary_ids,
        analysis.app_context.storage,
        manager.Queue(),
        manager.Event(),
    )
    analysis.model.is_draft = result.is_draft
    if result.is_draft:
        raise RuntimeError(f"{interface.name} did not finish")
    return project


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
