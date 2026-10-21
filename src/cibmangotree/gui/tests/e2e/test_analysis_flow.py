"""Analyzer choice, configuration, and results interactions.

The stepper's Next and Back buttons move in the browser, so the walk from
column mapping through Run is a Screen test. Here, Next is checked for the
Python result: the selected analyzer is stored, and missing choices are rejected.
Home records whether the leave dialog appears for each analysis session state.
"""

from nicegui import ui
from nicegui.testing import User

from cibmangotree.analyzers.hashtags.hashtags_base.interface import (
    interface as hashtags_interface,
)
from cibmangotree.analyzers.ngrams.ngrams_base.interface import (
    interface as ngrams_interface,
)
from cibmangotree.app import App
from cibmangotree.gui.tests.e2e.helpers import (
    click_button,
    click_icon,
    open_app,
    seed_project,
)


async def test_configure_without_a_project_returns_home(
    user: User, ui_app: App
) -> None:
    open_app(ui_app)
    await user.open("/configure_analysis")

    await user.should_see("No project selected. Redirecting", retries=20)
    await user.should_see("Projects", retries=20)


async def test_fork_starts_a_new_test(user: User, ui_app: App) -> None:
    project = seed_project(ui_app, "Fork project")
    session = open_app(ui_app)
    session.current_project = project
    session.project_loaded_from_storage = True
    await user.open("/select_analyzer_fork")

    await user.should_see("What do you want to do next?")
    user.find("Start a New Test").click()

    await user.should_see("Hashtag analysis", retries=20)
    await user.should_see("N-gram Analysis")


async def test_fork_reviews_previous_tests(user: User, ui_app: App) -> None:
    project = seed_project(ui_app, "Previous project")
    session = open_app(ui_app)
    session.current_project = project
    session.project_loaded_from_storage = True
    await user.open("/select_analyzer_fork")

    user.find("Review a Previous Test").click()

    await user.should_see("No previous tests have been found.", retries=20)
    user.find("Proceed").click()
    await user.should_see("No analyses available")


async def test_manage_analyses_opens_from_the_previous_page(
    user: User, ui_app: App
) -> None:
    project = seed_project(ui_app, "Managed project")
    session = open_app(ui_app)
    session.current_project = project
    session.project_loaded_from_storage = True
    await user.open("/select_previous_analyzer")

    user.find("Manage Analyses").click()
    await user.should_see("No analyses found", retries=20)
    click_button(user, "Close")
    await user.should_see("Review a Previous Analysis")


async def test_analyzer_next_requires_a_selection(user: User, ui_app: App) -> None:
    project = seed_project(ui_app, "Needs analyzer")
    session = open_app(ui_app)
    session.current_project = project
    await user.open("/configure_analysis")

    user.find("Next").click()

    await user.should_see("Please select an analyzer")
    assert session.selected_analyzer is None


async def test_selecting_an_analyzer_stores_the_choice(user: User, ui_app: App) -> None:
    project = seed_project(ui_app, "Mapped project")
    session = open_app(ui_app)
    session.current_project = project
    await user.open("/configure_analysis")

    click_button(user, "Hashtag analysis")
    await user.should_see("Analysis of hashtags", retries=20)
    click_button(user, "Next")

    assert session.selected_analyzer is not None
    assert session.selected_analyzer.id == "hashtags"


async def test_post_analysis_opens_the_placeholder_dashboard(
    user: User, ui_app: App
) -> None:
    project = seed_project(ui_app, "Results project")
    session = open_app(ui_app)
    session.current_project = project
    await user.open("/post_analysis")

    await user.should_see("What would you like to do next?")
    await user.should_see("Open results dashboard")
    user.find("Open results folder").click()
    await user.should_see("No analysis to open")

    user.find("Open results dashboard").click()
    await user.should_see("Dashboard coming soon", retries=20)


async def test_ngram_dashboard_search_is_available(user: User, ui_app: App) -> None:
    project = seed_project(ui_app, "Ngram project")
    session = open_app(ui_app)
    session.current_project = project
    session.selected_analyzer = ngrams_interface
    session.selected_analyzer_name = ngrams_interface.name
    await user.open("/dashboard")

    await user.should_see("Search N-gram", retries=20)
    user.find(kind=ui.input).type("paste")
    await user.should_see("No analysis found in the current session.", retries=20)


async def test_leaving_configuration_with_no_analyzer_goes_home(
    user: User, ui_app: App
) -> None:
    """Home leaves configuration directly when no analyzer has been chosen."""
    project = seed_project(ui_app, "Unconfigured project")
    session = open_app(ui_app)
    session.current_project = project
    await user.open("/configure_analysis")

    click_icon(user, "home")

    await user.should_see("Projects", retries=20)


async def test_leaving_after_selecting_an_analyzer_asks_for_confirmation(
    user: User, ui_app: App
) -> None:
    """Choosing an analyzer asks before Home leaves.

    Stay keeps the configuration screen. Leave returns to the project list.
    """
    project = seed_project(ui_app, "Chosen analyzer project")
    session = open_app(ui_app)
    session.current_project = project
    await user.open("/configure_analysis")

    click_button(user, "Hashtag analysis")
    await user.should_see("Analysis of hashtags", retries=20)
    click_button(user, "Next")
    click_icon(user, "home")

    await user.should_see(
        "Your analysis has not been saved yet. Leave anyway?", retries=20
    )
    click_button(user, "Stay")
    await user.should_see("Hashtag analysis", retries=20)

    click_icon(user, "home")
    await user.should_see(
        "Your analysis has not been saved yet. Leave anyway?", retries=20
    )
    click_button(user, "Leave")
    await user.should_see("Projects", retries=20)


async def test_leaving_an_analysis_loaded_from_storage_goes_home(
    user: User, ui_app: App
) -> None:
    """An analysis opened from storage can be left without a confirmation dialog."""
    project = seed_project(ui_app, "Stored analysis project")
    session = open_app(ui_app)
    session.current_project = project
    session.selected_analyzer = hashtags_interface
    session.selected_analyzer_name = hashtags_interface.name
    session.analysis_loaded_from_storage = True
    await user.open("/configure_analysis")

    click_icon(user, "home")

    await user.should_see("Projects", retries=20)


async def test_leaving_a_fresh_configuration_asks_for_confirmation(
    user: User, ui_app: App
) -> None:
    """A newly chosen analyzer asks before Home leaves configuration."""
    project = seed_project(ui_app, "Fresh configuration project")
    session = open_app(ui_app)
    session.current_project = project
    session.selected_analyzer = hashtags_interface
    session.selected_analyzer_name = hashtags_interface.name
    session.analysis_loaded_from_storage = False
    await user.open("/configure_analysis")

    click_icon(user, "home")

    await user.should_see(
        "Your analysis has not been saved yet. Leave anyway?", retries=20
    )
