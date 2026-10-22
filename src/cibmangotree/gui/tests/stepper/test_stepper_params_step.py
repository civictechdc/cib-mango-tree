"""Behavior tests for gui.pages.analysis_workflow.params_step.ParamsConfigStep."""

from unittest.mock import MagicMock

from nicegui import ui
from nicegui.testing import User

from cibmangotree.analyzers.hashtags.hashtags_base.interface import (
    interface as hashtags_interface,
)
from cibmangotree.analyzers.ngrams.ngrams_base.interface import (
    interface as ngrams_interface,
)
from cibmangotree.app import App
from cibmangotree.gui.context import GUIContext
from cibmangotree.gui.pages.analysis_workflow.params_step import ParamsConfigStep
from cibmangotree.gui.session import GuiSession
from cibmangotree.gui.tests.e2e.helpers import seed_project


def _window_count_text(user: User) -> str:
    labels = [
        element.text
        for element in user.find(kind=ui.label).elements
        if element.text.endswith("window") or element.text.endswith("windows")
    ]
    assert len(labels) == 1
    return labels[0]


async def test_params_step_no_params_message(
    user: User, gui_session: GuiSession
) -> None:
    analyzer = MagicMock()
    analyzer.params = []
    gui_session.selected_analyzer = analyzer

    step = ParamsConfigStep(gui_session)

    @ui.page("/params-step")
    def page() -> None:
        step.render()

    await user.open("/params-step")
    await user.should_see("This analyzer has no configurable parameters.")


async def test_hashtag_params_window_count_updates(user: User, ui_app: App) -> None:
    project = seed_project(ui_app, "Window preview")
    session = GuiSession(context=GUIContext(app=ui_app))
    session.current_project = project
    session.selected_analyzer = hashtags_interface
    session.column_mapping = {
        column.name: column.name for column in hashtags_interface.input.columns
    }
    step = ParamsConfigStep(session)

    @ui.page("/params-step-preview")
    def page() -> None:
        step.render()

    await user.open("/params-step-preview")
    await user.should_see("Post activity")
    await user.should_see(
        "The space between gray dashed lines is how big each window is."
    )
    before = _window_count_text(user)

    amount = next(iter(user.find(kind=ui.number).elements))
    unit = next(iter(user.find(kind=ui.select).elements))
    with user:
        amount.value = 12
        unit.value = "hour"

    after = _window_count_text(user)
    assert after != before
    assert after == "27 windows"
    await user.should_not_see("Too many windows to draw.")
    assert user.find(kind=ui.echart).elements


async def test_ngram_params_have_no_activity_chart(user: User, ui_app: App) -> None:
    project = seed_project(ui_app, "N-gram parameters")
    session = GuiSession(context=GUIContext(app=ui_app))
    session.current_project = project
    session.selected_analyzer = ngrams_interface
    session.column_mapping = {
        column.name: "Post Content" for column in ngrams_interface.input.columns
    }
    step = ParamsConfigStep(session)

    @ui.page("/params-step-ngrams")
    def page() -> None:
        step.render()

    await user.open("/params-step-ngrams")
    await user.should_see("Minimum N-gram Length")
    await user.should_not_see("Post activity")
    await user.should_not_see(kind=ui.echart)
