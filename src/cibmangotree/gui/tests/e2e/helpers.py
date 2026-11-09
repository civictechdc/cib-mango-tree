"""Shared setup for GUI end-to-end tests.

Tests call open_app and then click through Python handlers.
"""

from __future__ import annotations

import os
from io import BytesIO
from pathlib import Path

import polars as pl
from nicegui import ui
from nicegui.testing import User
from nicegui.testing.user_interaction import UserInteraction

from cibmangotree.analyzers.time_coordination import time_coordination
from cibmangotree.analyzers.time_coordination.time_coordination_base.interface import (
    COL_MESSAGE_TEXT,
    COL_NORM_WEIGHT,
    COL_REL_TIMESTAMP,
    COL_TIMESTAMP,
    COL_USER_A,
    COL_USER_B,
    COL_USER_ID,
    COL_WEIGHT,
    OUTPUT_EDGES,
    OUTPUT_POSTS,
    PARAM_METHOD,
    PARAM_MIN_POSTS,
    PARAM_T_STEP,
    PARAM_WIN_SIZE,
)
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

TIME_COORDINATION_CSV = (
    Path(__file__).resolve().parents[3]
    / "analyzers"
    / "time_coordination"
    / "test_data"
    / "input.csv"
)


def open_app(app: App) -> GuiSession:
    return register_pages(app)


def seed_project(app: App, name: str):
    importer = CSVImporter().init_session(str(HASHTAG_CSV))
    return app.create_project(name, importer, dataset_name=HASHTAG_CSV.name)


def seed_time_coordination_project(app: App, name: str):
    importer = CSVImporter().init_session(str(TIME_COORDINATION_CSV))
    return app.create_project(name, importer, dataset_name=TIME_COORDINATION_CSV.name)


def seed_time_coordination_outputs(app: App, project) -> object:
    """Create a draft time_coordination run and write minimal posts/edges parquets."""
    analysis = app.context.storage.init_analysis(
        project_id=project.id,
        display_name="Time coordination e2e",
        primary_analyzer_id=time_coordination.id,
        column_mapping={
            COL_USER_ID: COL_USER_ID,
            COL_TIMESTAMP: COL_TIMESTAMP,
            COL_MESSAGE_TEXT: COL_MESSAGE_TEXT,
        },
        param_values={
            PARAM_METHOD: "time_overlap",
            PARAM_WIN_SIZE: 2,
            PARAM_T_STEP: 300,
            PARAM_MIN_POSTS: 1,
        },
    )
    root = app.context.storage.get_primary_output_parquet_path(analysis, OUTPUT_POSTS)
    os.makedirs(os.path.dirname(root), exist_ok=True)

    posts = pl.DataFrame(
        {
            COL_USER_ID: ["alice", "bob", "alice", "bob", "carol", "dave"],
            COL_TIMESTAMP: [
                "2024-01-01 00:00:00",
                "2024-01-01 00:00:10",
                "2024-01-01 00:00:20",
                "2024-01-01 00:00:25",
                "2024-01-01 00:05:00",
                "2024-01-01 00:05:05",
            ],
            COL_MESSAGE_TEXT: ["hello", "hi", "again", "there", "later", "also later"],
            COL_REL_TIMESTAMP: [0.0, 10.0, 20.0, 25.0, 300.0, 305.0],
        }
    )
    edges = pl.DataFrame(
        {
            COL_USER_A: ["alice", "carol"],
            COL_USER_B: ["bob", "dave"],
            COL_WEIGHT: [2.0, 1.0],
            COL_NORM_WEIGHT: [0.5, 0.25],
        }
    )
    posts.write_parquet(
        app.context.storage.get_primary_output_parquet_path(analysis, OUTPUT_POSTS)
    )
    edges.write_parquet(
        app.context.storage.get_primary_output_parquet_path(analysis, OUTPUT_EDGES)
    )
    return analysis


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
