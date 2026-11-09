"""E2E coverage for the time_coordination analyzer path.

Covers select → params labels → dashboard empty/populated Explore UI.
Full run-worker timing is left to analyzer unit/contract tests.
"""

from nicegui import ui
from nicegui.testing import User

from cibmangotree.analyzers.time_coordination import time_coordination
from cibmangotree.analyzers.time_coordination.time_coordination_base.interface import (
    COL_MESSAGE_TEXT,
    COL_TIMESTAMP,
    COL_USER_ID,
)
from cibmangotree.app import App
from cibmangotree.gui.context import GUIContext
from cibmangotree.gui.pages.analysis_workflow.params_step import ParamsConfigStep
from cibmangotree.gui.session import GuiSession
from cibmangotree.gui.tests.e2e.helpers import (
    click_button,
    open_app,
    seed_time_coordination_outputs,
    seed_time_coordination_project,
)


async def test_time_coordination_appears_in_analyzer_list(
    user: User, ui_app: App
) -> None:
    project = seed_time_coordination_project(ui_app, "TA list")
    session = open_app(ui_app)
    session.current_project = project
    await user.open("/configure_analysis")

    await user.should_see("Time Coordination", retries=20)
    await user.should_see("Hashtag analysis", retries=20)


async def test_selecting_time_coordination_stores_the_choice(
    user: User, ui_app: App
) -> None:
    project = seed_time_coordination_project(ui_app, "TA select")
    session = open_app(ui_app)
    session.current_project = project
    await user.open("/configure_analysis")

    click_button(user, "Time Coordination")
    await user.should_see("Methods", retries=20)
    await user.should_see("Sliding Window", retries=20)
    await user.should_see("Action Driven Overlapping Window (ADO)", retries=20)
    await user.should_see("Time Overlap", retries=20)
    click_button(user, "Next")

    assert session.selected_analyzer is not None
    assert session.selected_analyzer.id == "time_coordination"


async def test_time_coordination_params_step_shows_method_controls(
    user: User, ui_app: App
) -> None:
    project = seed_time_coordination_project(ui_app, "TA params")
    session = GuiSession(context=GUIContext(app=ui_app))
    session.current_project = project
    session.selected_analyzer = time_coordination
    session.column_mapping = {
        COL_USER_ID: COL_USER_ID,
        COL_TIMESTAMP: COL_TIMESTAMP,
        COL_MESSAGE_TEXT: COL_MESSAGE_TEXT,
    }
    step = ParamsConfigStep(session)

    @ui.page("/params-step-time-coordination")
    def page() -> None:
        step.render()

    await user.open("/params-step-time-coordination")
    await user.should_see("Configure Time Coordination Parameters", retries=20)
    await user.should_see("Method")
    await user.should_see("Time Overlap")
    await user.should_see("Window size (steps)")
    await user.should_see("Time step (seconds)")
    await user.should_see("Min posts (Time Overlap)")
    await user.should_not_see("Post activity")
    assert user.find(kind=ui.select).elements
    assert len(user.find(kind=ui.number).elements) >= 3


async def test_time_coordination_dashboard_without_outputs_shows_message(
    user: User, ui_app: App
) -> None:
    project = seed_time_coordination_project(ui_app, "TA empty dash")
    session = open_app(ui_app)
    session.current_project = project
    session.selected_analyzer = time_coordination
    session.selected_analyzer_name = time_coordination.name
    await user.open("/dashboard")

    await user.should_see(
        "No time-coordination outputs found for this run.", retries=20
    )


async def test_time_coordination_dashboard_explore_ui_with_outputs(
    user: User, ui_app: App
) -> None:
    project = seed_time_coordination_project(ui_app, "TA explore")
    analysis = seed_time_coordination_outputs(ui_app, project)
    session = open_app(ui_app)
    session.current_project = project
    session.current_analysis = analysis
    session.selected_analyzer = time_coordination
    session.selected_analyzer_name = time_coordination.name
    await user.open("/dashboard")

    await user.should_see("Explore network", retries=20)
    await user.should_see("Users Selected: —")
    await user.should_see("Select a pair of users")
    await user.should_see("Compare users")
    await user.should_see("1:1 pair")
    await user.should_see("Filter by group size.")
    assert user.find(kind=ui.echart).elements
    assert user.find(kind=ui.slider).elements
    assert user.find(kind=ui.checkbox).elements


async def test_time_coordination_dashboard_list_selection_enables_compare(
    user: User, ui_app: App
) -> None:
    project = seed_time_coordination_project(ui_app, "TA select pair")
    analysis = seed_time_coordination_outputs(ui_app, project)
    session = open_app(ui_app)
    session.current_project = project
    session.current_analysis = analysis
    session.selected_analyzer = time_coordination
    session.selected_analyzer_name = time_coordination.name
    await user.open("/dashboard")

    await user.should_see("Select a pair of users", retries=20)
    edge_select = next(iter(user.find(kind=ui.select).elements))
    with user:
        edge_select.set_value("alice\tbob")

    await user.should_see("Users Selected: alice and bob", retries=20)
    user.find("Compare users").click()
    await user.should_see("Time Coordination: Compare users", retries=20)
    await user.should_see("alice  ↔  bob", retries=20)
    await user.should_see("hello", retries=20)
    await user.should_see("alice: 2 overlapping", retries=20)
    assert user.find(kind=ui.chat_message).elements
    assert session.time_coordination_compare_user0 == "alice"
    assert session.time_coordination_compare_user1 == "bob"


async def test_post_analysis_opens_time_coordination_dashboard(
    user: User, ui_app: App
) -> None:
    """Registered dashboard is used instead of the placeholder."""
    project = seed_time_coordination_project(ui_app, "TA post")
    analysis = seed_time_coordination_outputs(ui_app, project)
    session = open_app(ui_app)
    session.current_project = project
    session.current_analysis = analysis
    session.selected_analyzer = time_coordination
    session.selected_analyzer_name = time_coordination.name
    await user.open("/post_analysis")

    await user.should_see("Open results dashboard", retries=20)
    user.find("Open results dashboard").click()
    await user.should_see("Explore network", retries=20)
    await user.should_not_see("Dashboard coming soon")
