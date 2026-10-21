"""Page-level interactions that run inside chrome-headless-shell.

That program has no window and no Dock icon. These tests cover the actions
that happen in the page itself: choosing a file, selecting a table row,
clicking a grid cell, moving the analysis stepper, searching n-grams, and
toggling the hashtag chart. They also delete a project, review a saved
hashtag analysis and a saved n-gram analysis, and run each analysis through
export.
The User tests cover the rest.
"""

import time

import pytest
from nicegui.testing import Screen
from selenium.common.exceptions import StaleElementReferenceException
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys

from cibmangotree.analyzers.hashtags.hashtags_base.interface import (
    interface as hashtags_interface,
)
from cibmangotree.analyzers.ngrams.ngrams_base.interface import (
    interface as ngrams_interface,
)
from cibmangotree.app import App
from cibmangotree.gui.tests.e2e.helpers import (
    HASHTAG_CSV,
    NGRAM_CSV,
    attach_csv,
    open_app,
    seed_completed_hashtag_analysis,
    seed_completed_ngram_analysis,
    seed_project,
)


def _prepare(screen: Screen) -> None:
    # The fixture's default window is 600x600, which leaves the footer over the
    # buttons. A taller window lets clicks land on the control itself.
    screen.selenium.set_window_size(1280, 900)


def _click(screen: Screen, text: str) -> None:
    # Scroll and click in the page so a sticky header or footer does not
    # intercept the click.
    element = screen.find(text)
    screen.selenium.execute_script(
        "arguments[0].scrollIntoView({block: 'center'});", element
    )
    screen.selenium.execute_script("arguments[0].click();", element)


def _click_visible_button(screen: Screen, text: str, *, last: bool = False) -> None:
    # Quasar uppercases button labels, and a click can rebuild the button list
    # before Selenium finishes reading it.
    wanted = text.casefold()
    deadline = time.time() + 5
    while time.time() < deadline:
        try:
            buttons = [
                element
                for element in screen.selenium.find_elements(
                    By.CSS_SELECTOR, "button.q-btn"
                )
                if wanted in element.text.casefold() and element.is_displayed()
            ]
        except StaleElementReferenceException:
            screen.wait(0.1)
            continue
        if not buttons:
            screen.wait(0.1)
            continue
        element = buttons[-1] if last else buttons[0]
        try:
            screen.selenium.execute_script(
                "arguments[0].scrollIntoView({block: 'center'});", element
            )
            screen.selenium.execute_script("arguments[0].click();", element)
        except StaleElementReferenceException:
            screen.wait(0.1)
            continue
        return
    raise AssertionError(f"No visible button {text!r}")


def _dialog_button_ids(screen: Screen) -> set[str]:
    # A closed dialog stays in the page and can still look visible. Its buttons
    # keep their ids, so a newly opened dialog is the one with new ids.
    try:
        return {
            element.get_attribute("id") or ""
            for element in screen.selenium.find_elements(
                By.CSS_SELECTOR, ".q-dialog button.q-btn"
            )
            if element.is_displayed()
        }
    except StaleElementReferenceException:
        return set()


def _click_dialog_button(screen: Screen, text: str, previous_ids: set[str]) -> None:
    wanted = text.casefold()
    deadline = time.time() + 5
    while time.time() < deadline:
        try:
            buttons = [
                element
                for element in screen.selenium.find_elements(
                    By.CSS_SELECTOR, ".q-dialog button.q-btn"
                )
                if " ".join((element.text or "").split()).casefold() == wanted
                and element.is_displayed()
                and (element.get_attribute("id") or "") not in previous_ids
            ]
        except StaleElementReferenceException:
            screen.wait(0.1)
            continue
        if not buttons:
            screen.wait(0.1)
            continue
        element = buttons[-1]
        try:
            screen.selenium.execute_script(
                "arguments[0].scrollIntoView({block: 'center'});", element
            )
            screen.selenium.execute_script("arguments[0].click();", element)
        except StaleElementReferenceException:
            screen.wait(0.1)
            continue
        return
    raise AssertionError(f"No visible dialog button {text!r}")


def _choose_toggle(screen: Screen, text: str) -> None:
    # The server learns the new value from the click. Retry Import can arrive
    # first and rerun with the previous separator, so wait until this option
    # is the selected one and the click has had time to be recorded.
    wanted = text.casefold()
    deadline = time.time() + 5
    while time.time() < deadline:
        try:
            buttons = [
                element
                for element in screen.selenium.find_elements(
                    By.CSS_SELECTOR, "button.q-btn"
                )
                if wanted in (element.text or "").casefold() and element.is_displayed()
            ]
        except StaleElementReferenceException:
            screen.wait(0.1)
            continue
        if not buttons:
            screen.wait(0.1)
            continue
        # A dialog that is still opening replaces its buttons. The latest match
        # is the one in the dialog that just opened.
        element = buttons[-1]
        try:
            selected = element.get_attribute("aria-pressed") == "true" or (
                "q-btn--active" in (element.get_attribute("class") or "")
            )
            if selected:
                screen.wait(0.5)
                return
            screen.selenium.execute_script(
                "arguments[0].scrollIntoView({block: 'center'});", element
            )
            screen.selenium.execute_script("arguments[0].click();", element)
        except StaleElementReferenceException:
            screen.wait(0.1)
            continue
        screen.wait(0.1)
    raise AssertionError(f"{text!r} did not become selected")


def _set_number(screen: Screen, value: str, *, index: int = -1) -> None:
    # Arrow keys change a number input without clearing it. Clearing the field
    # sends None through validation and NiceGUI records that as an error.
    fields = [
        element
        for element in screen.selenium.find_elements(
            By.CSS_SELECTOR, "input[type=number]"
        )
        if element.is_displayed()
    ]
    if not fields:
        raise AssertionError("No visible number input")
    field = fields[index]
    screen.selenium.execute_script(
        "arguments[0].scrollIntoView({block: 'center'});", field
    )
    field.click()
    current = int(float(field.get_attribute("value") or "0"))
    target = int(value)
    key = Keys.ARROW_UP if target >= current else Keys.ARROW_DOWN
    for _ in range(abs(target - current)):
        field.send_keys(key)
    field.send_keys(Keys.TAB)
    return field


def _click_first_chart_point(screen: Screen) -> None:
    # ECharts keeps the series click on the chart instance. Dispatching that
    # event records the same screen change as a click on a drawn point.
    clicked = screen.selenium.execute_script("""
        const host = document.querySelector('.nicegui-echart');
        const component = host && getElement(host);
        const chart = component && component.chart;
        if (!chart) return 'no-chart';
        const series = chart.getOption().series || [];
        for (let seriesIndex = 0; seriesIndex < series.length; seriesIndex++) {
            const data = series[seriesIndex].data || [];
            if (!data.length) continue;
            const row = data[0];
            chart.trigger('click', {
                componentType: 'series',
                seriesType: series[seriesIndex].type,
                seriesIndex: seriesIndex,
                seriesName: series[seriesIndex].name || '',
                name: row.name || '',
                dataIndex: 0,
                data: row,
                value: row.value || row,
            });
            return true;
        }
        return 'no-data';
        """)
    if clicked is not True:
        raise AssertionError(f"No chart point to click: {clicked}")


def _click_visible_cell(screen: Screen, predicate) -> str:
    deadline = time.time() + 10
    while time.time() < deadline:
        cells = [
            cell
            for cell in screen.selenium.find_elements(By.CSS_SELECTOR, ".ag-cell")
            if cell.is_displayed() and predicate(cell.text or "")
        ]
        if cells:
            text = cells[0].text
            screen.selenium.execute_script(
                "arguments[0].scrollIntoView({block: 'center'});", cells[0]
            )
            screen.selenium.execute_script("arguments[0].click();", cells[0])
            return text
        screen.wait(0.25)
    raise AssertionError("No matching grid cell")


def _visible_text(screen: Screen) -> str:
    try:
        return (
            screen.selenium.execute_script(
                "return document.body ? document.body.innerText : ''"
            )
            or ""
        )
    except StaleElementReferenceException:
        return ""


def _wait_for(screen: Screen, text: str, timeout: float = 15) -> None:
    deadline = time.time() + timeout
    last_error: Exception | None = None
    while time.time() < deadline:
        try:
            screen.should_contain(text)
            return
        except AssertionError as exc:
            last_error = exc
            screen.wait(0.25)
    raise AssertionError(f"Did not see {text!r}") from last_error


def test_choose_file_opens_the_preview(screen: Screen, ui_app: App) -> None:
    open_app(ui_app)
    screen.open("/import_dataset")
    _prepare(screen)
    _wait_for(screen, "Browse Files")

    file_input = screen.selenium.find_element(By.CSS_SELECTOR, "input[type=file]")
    file_input.send_keys(str(HASHTAG_CSV))

    _wait_for(screen, "Data Preview (first 5 rows)")
    screen.should_contain("Looks good, let's proceed")


def test_select_project_row_and_open_it(screen: Screen, ui_app: App) -> None:
    seed_project(ui_app, "Screen project")
    open_app(ui_app)
    screen.open("/")
    _prepare(screen)
    _wait_for(screen, "Screen project")

    row_box = screen.selenium.find_element(
        By.XPATH,
        "//td[contains(., 'Screen project')]/ancestor::tr"
        "//*[contains(@class, 'q-checkbox')]",
    )
    screen.selenium.execute_script(
        "arguments[0].scrollIntoView({block: 'center'});", row_box
    )
    screen.selenium.execute_script("arguments[0].click();", row_box)
    _click(screen, "Open Project")

    _wait_for(screen, "What do you want to do next?")


def test_preview_grid_cell_can_be_clicked(screen: Screen, ui_app: App) -> None:
    session = open_app(ui_app)
    attach_csv(session)
    screen.open("/preview_dataset")
    _prepare(screen)
    _wait_for(screen, "user05")

    _click(screen, "user05")
    screen.should_contain("Looks good, let's proceed")


def test_ngram_search_accepts_text(screen: Screen, ui_app: App) -> None:
    project = seed_project(ui_app, "Ngram screen project")
    session = open_app(ui_app)
    session.current_project = project
    session.selected_analyzer = ngrams_interface
    session.selected_analyzer_name = ngrams_interface.name
    screen.open("/dashboard")
    _prepare(screen)
    _wait_for(screen, "Search N-gram")

    field = screen.selenium.find_element(
        By.CSS_SELECTOR, "input[aria-label='Search N-gram']"
    )
    field.click()
    field.send_keys("paste")
    field.send_keys(Keys.ENTER)

    _wait_for(screen, "No analysis found in the current session.")
    screen.should_contain_input("paste")


def test_hashtag_stepper_reaches_run(screen: Screen, ui_app: App) -> None:
    project = seed_project(ui_app, "Stepper project")
    session = open_app(ui_app)
    session.current_project = project
    screen.open("/configure_analysis")
    _prepare(screen)
    _wait_for(screen, "Hashtag analysis")

    _click(screen, "Hashtag analysis")
    _click(screen, "Next")
    _wait_for(screen, "Map Your Data Columns")

    _click(screen, "Next")
    _wait_for(screen, "Configure Parameters")

    _click(screen, "Next")
    _wait_for(screen, "Run Analysis")
    _click(screen, "Back")
    _wait_for(screen, "Configure Parameters")


def test_hashtag_chart_area_shows_when_there_is_no_analysis(
    screen: Screen, ui_app: App
) -> None:
    project = seed_project(ui_app, "Hashtag screen project")
    session = open_app(ui_app)
    session.current_project = project
    session.selected_analyzer = hashtags_interface
    session.selected_analyzer_name = hashtags_interface.name
    screen.open("/dashboard")
    _prepare(screen)
    _wait_for(screen, "Show smoothed line")

    _click(screen, "Show smoothed line")
    screen.should_contain("Click a point on the chart above to explore hashtags.")


def test_delete_selected_project(screen: Screen, ui_app: App) -> None:
    """Selecting a project and confirming Delete removes it from storage.

    Cancel leaves the project in the list. Confirming the warning deletes it.
    """
    seed_project(ui_app, "Delete me")
    open_app(ui_app)
    screen.open("/")
    _prepare(screen)
    _wait_for(screen, "Delete me")

    row_box = screen.selenium.find_element(
        By.XPATH,
        "//td[contains(., 'Delete me')]/ancestor::tr"
        "//*[contains(@class, 'q-checkbox')]",
    )
    screen.selenium.execute_script("arguments[0].click();", row_box)
    _click_visible_button(screen, "Delete")
    _wait_for(screen, "This action cannot be undone.")
    _click_visible_button(screen, "Cancel")
    _wait_for(screen, "Delete me")
    assert [project.display_name for project in ui_app.list_projects()] == ["Delete me"]

    previous_ids = _dialog_button_ids(screen)
    _click_visible_button(screen, "Delete")
    _wait_for(screen, "This action cannot be undone.")
    _click_dialog_button(screen, "Delete", previous_ids)

    _wait_for(screen, "Project 'Delete me' deleted")
    assert ui_app.list_projects() == []


def test_review_existing_analysis_opens_the_dashboard(
    screen: Screen, ui_app: App
) -> None:
    """A finished hashtag analysis can be reopened from the project list.

    The test opens the saved project, chooses Review a Previous Test, selects
    the Hashtag analysis row, and continues to the results page. Open results
    dashboard then shows the hashtag chart for that stored analysis.
    """
    seed_completed_hashtag_analysis(ui_app, "Reviewed project")
    open_app(ui_app)
    screen.open("/")
    _prepare(screen)
    _wait_for(screen, "Reviewed project")

    row_box = screen.selenium.find_element(
        By.XPATH,
        "//td[contains(., 'Reviewed project')]/ancestor::tr"
        "//*[contains(@class, 'q-checkbox')]",
    )
    screen.selenium.execute_script("arguments[0].click();", row_box)
    _click(screen, "Open Project")
    _wait_for(screen, "Review a Previous Test")
    _click(screen, "Review a Previous Test")
    _wait_for(screen, "Hashtag analysis")

    checkbox = screen.selenium.find_element(
        By.CSS_SELECTOR, ".ag-row .ag-checkbox-input"
    )
    screen.selenium.execute_script("arguments[0].click();", checkbox)
    _click_visible_button(screen, "Proceed")
    _wait_for(screen, "What would you like to do next?")
    _click(screen, "Open results dashboard")
    _wait_for_hashtag_chart(screen)


def test_review_existing_ngram_analysis_opens_the_dashboard(
    screen: Screen, ui_app: App
) -> None:
    """A finished n-gram analysis can be reopened from the project list.

    The test opens the saved project, chooses Review a Previous Test, selects
    the N-gram Analysis row, and continues to the results page. Open results
    dashboard then shows the n-gram chart for that stored analysis.
    """
    seed_completed_ngram_analysis(ui_app, "Reviewed n-gram project")
    open_app(ui_app)
    screen.open("/")
    _prepare(screen)
    _wait_for(screen, "Reviewed n-gram project")

    row_box = screen.selenium.find_element(
        By.XPATH,
        "//td[contains(., 'Reviewed n-gram project')]/ancestor::tr"
        "//*[contains(@class, 'q-checkbox')]",
    )
    screen.selenium.execute_script("arguments[0].click();", row_box)
    _click(screen, "Open Project")
    _wait_for(screen, "Review a Previous Test")
    _click(screen, "Review a Previous Test")
    _wait_for(screen, "N-gram Analysis")

    checkbox = screen.selenium.find_element(
        By.CSS_SELECTOR, ".ag-row .ag-checkbox-input"
    )
    screen.selenium.execute_script("arguments[0].click();", checkbox)
    _click_visible_button(screen, "Proceed")
    _wait_for(screen, "What would you like to do next?")
    _click(screen, "Open results dashboard")
    _wait_for_ngram_chart(screen)


@pytest.mark.filterwarnings(r"ignore:`pl\.count\(\)` is deprecated:DeprecationWarning")
def test_hashtag_import_runs_and_exports(screen: Screen, ui_app: App) -> None:
    """One browser run covers import through the hashtag dashboard.

    The file is the hashtag sample CSV. Switching the separator to semicolon
    collapses the preview to one column, and switching back to comma restores
    three. Proceed creates the project. Hashtag analysis is selected, its
    three columns are mapped, and the time window is set to 2. Run Analysis
    finishes, the Gini output is exported, and the dashboard chart loads.
    A chart point, a hashtag, and a user are then opened.
    """
    session = open_app(ui_app)
    session.new_project_name = "Full run"
    screen.open("/import_dataset")
    _prepare(screen)
    _wait_for(screen, "Browse Files")

    file_input = screen.selenium.find_element(By.CSS_SELECTOR, "input[type=file]")
    file_input.send_keys(str(HASHTAG_CSV))
    _wait_for(screen, "No. detected columns: 3")

    _click(screen, "There's something wrong")
    _wait_for(screen, "Column separator:")
    _wait_for(screen, "Quote character:")
    _wait_for(screen, "Has header:")
    _wait_for(screen, "Skip rows:")
    _choose_toggle(screen, "Semicolon")
    _click_visible_button(screen, "Retry Import")
    _wait_for(screen, "No. detected columns: 1")
    _wait_for(screen, "Preview updated successfully!")

    _click(screen, "There's something wrong")
    _wait_for(screen, "Column separator:")
    _choose_toggle(screen, "Comma")
    _click_visible_button(screen, "Retry Import")
    _wait_for(screen, "No. detected columns: 3")
    _click(screen, "Looks good, let's proceed")

    _wait_for(screen, "Hashtag analysis")
    _click(screen, "Hashtag analysis")
    _click(screen, "Next")
    _wait_for(screen, "Map Your Data Columns")
    _click(screen, "Next")
    _wait_for(screen, "Time window of analysis")
    _set_number(screen, "2")
    # Earlier Next buttons stay in the page. The last one saves the parameters.
    _click_visible_button(screen, "Next", last=True)
    _wait_for(screen, "Columns: 3 mapped")
    _wait_for(screen, "Parameters: 1 configured")
    assert session.analysis_params["time_window"].amount == 2
    assert set(session.column_mapping) == {
        "Unique UserID",
        "Timestamp",
        "Post Content",
    }

    _click_visible_button(screen, "Run Analysis")
    _wait_for(screen, "Continue", timeout=180)
    _click_visible_button(screen, "Continue")
    _wait_for(screen, "Export raw output files")
    _click(screen, "Export raw output files")
    _wait_for(screen, "Gini coefficient over time (Base)")
    _click(screen, "Gini coefficient over time (Base)")
    _click_visible_button(screen, "Next")
    _wait_for(screen, "Start Export")
    _click_visible_button(screen, "Start Export")
    _wait_for(screen, "Export complete!", timeout=60)
    _wait_for(screen, "Open exports folder")
    _click_visible_button(screen, "Close")
    _click(screen, "Open results dashboard")
    _wait_for_hashtag_chart(screen)
    _explore_hashtag_chart(screen)


@pytest.mark.filterwarnings(
    "ignore:`is_in` with a collection of the same datatype is ambiguous and deprecated:DeprecationWarning"
)
def test_ngram_import_runs_and_exports(screen: Screen, ui_app: App) -> None:
    """One browser run records the n-gram screens from import through the dashboard.

    The file is the n-gram sample CSV. N-gram Analysis shows its description.
    The mapping step shows the four n-gram columns. Minimum and maximum length
    are on the parameter step, and the maximum is set to 4. Run Analysis
    finishes, both export choices are shown, the repetition statistics are
    exported, and the dashboard shows results. Searching and clicking a point
    opens the user viewer.
    """
    session = open_app(ui_app)
    session.new_project_name = "N-gram run"
    screen.open("/import_dataset")
    _prepare(screen)
    _wait_for(screen, "Browse Files")

    file_input = screen.selenium.find_element(By.CSS_SELECTOR, "input[type=file]")
    file_input.send_keys(str(NGRAM_CSV))
    _wait_for(screen, "No. detected columns: 4")
    _click(screen, "Looks good, let's proceed")

    _wait_for(screen, "N-gram Analysis")
    _click(screen, "N-gram Analysis")
    _wait_for(screen, "extracts n-grams")
    _click(screen, "Next")
    _wait_for(screen, "Map Your Data Columns")
    _wait_for(screen, "Unique User ID")
    _wait_for(screen, "Unique Post Number")
    _wait_for(screen, "Post Content")
    _wait_for(screen, "Timestamp")
    _click(screen, "Next")
    _wait_for(screen, "Minimum N-gram Length")
    _wait_for(screen, "Maximum N-gram Length")
    _set_number(screen, "4")
    field = screen.selenium.find_elements(By.CSS_SELECTOR, "input[type=number]")[-1]
    assert int(float(field.get_attribute("value") or "0")) == 4
    _click_visible_button(screen, "Next", last=True)
    _wait_for(screen, "Columns: 4 mapped")
    _wait_for(screen, "Parameters: 2 configured")

    _click_visible_button(screen, "Run Analysis")
    _wait_for(screen, "Continue", timeout=180)
    _click_visible_button(screen, "Continue")
    _wait_for(screen, "Export raw output files")
    _click(screen, "Export raw output files")
    _wait_for(screen, "N-gram repetition statistics (Copy-Pasta Detector)")
    _wait_for(screen, "N-gram full report (Copy-Pasta Detector)")
    _click(screen, "N-gram repetition statistics (Copy-Pasta Detector)")
    _click_visible_button(screen, "Next")
    _wait_for(screen, "Configure export")
    _wait_for(screen, "CSV")
    _click_visible_button(screen, "Start Export")
    _wait_for(screen, "Export complete!", timeout=60)
    _wait_for(screen, "Open exports folder")
    _click_visible_button(screen, "Close")
    _click(screen, "Open results dashboard")
    _wait_for_ngram_chart(screen)

    field = screen.selenium.find_element(
        By.CSS_SELECTOR, "input[aria-label='Search N-gram']"
    )
    field.click()
    field.send_keys("go")
    _wait_for(screen, "matches found")
    _click_first_chart_point(screen)
    _wait_for(screen, "total repetitions")
    _click_visible_cell(screen, lambda text: text == "alice")
    _wait_for(screen, "User Viewer - alice")
    _wait_for(screen, "Total Posts:")


def test_manage_analyses_lists_and_deletes_a_saved_analysis(
    screen: Screen, ui_app: App
) -> None:
    """Manage Analyses lists a saved hashtag analysis and deletes it.

    Cancel leaves the analysis in the list. Confirming the warning removes it.
    """
    project = seed_completed_hashtag_analysis(ui_app, "Managed screen project")
    session = open_app(ui_app)
    session.current_project = project
    session.project_loaded_from_storage = True
    screen.open("/select_previous_analyzer")
    _prepare(screen)
    _wait_for(screen, "Hashtag analysis")

    _click(screen, "Manage Analyses")
    _wait_for(screen, "Delete Selected")
    _wait_for(screen, "Hashtag analysis")
    checkbox = screen.selenium.find_elements(
        By.CSS_SELECTOR, ".ag-row .ag-checkbox-input"
    )[-1]
    screen.selenium.execute_script("arguments[0].click();", checkbox)
    _click_visible_button(screen, "Delete Selected")
    _wait_for(screen, "Are you sure you want to delete")
    _click_visible_button(screen, "Cancel")
    _wait_for(screen, "Hashtag analysis")
    _wait_for(screen, "Delete Selected")

    previous_ids = _dialog_button_ids(screen)
    _click_visible_button(screen, "Delete Selected")
    _wait_for(screen, "Are you sure you want to delete")
    _click_dialog_button(screen, "Delete", previous_ids)
    _wait_for(screen, "Deleted 1 analysis successfully.")


def _explore_hashtag_chart(screen: Screen) -> None:
    _click_first_chart_point(screen)
    _wait_for(screen, "hashtags found in window starting")
    _click_visible_cell(screen, lambda text: text.startswith("#"))
    _wait_for(screen, "users posted")
    _click_visible_cell(screen, lambda text: text.startswith("user"))
    _wait_for(screen, "posts found for account")


def _wait_for_hashtag_chart(screen: Screen, timeout: float = 30) -> None:
    deadline = time.time() + timeout
    last_text = ""
    while time.time() < deadline:
        last_text = _visible_text(screen)
        if (
            "Show smoothed line" in last_text
            and "Hashtags" in last_text
            and "Users" in last_text
            and "Tweet Explorer" in last_text
            and "Click a point on the chart above to explore hashtags." in last_text
            and "Click a hashtag above to see which users posted it." in last_text
            and "Click a user above to see their posts." in last_text
            and "Loading dashboard..." not in last_text
            and "No hashtag data available" not in last_text
            and "Could not load hashtag analysis" not in last_text
            and "Could not build chart" not in last_text
        ):
            return
        screen.wait(0.25)
    raise AssertionError("Hashtag chart did not finish loading.\n" + last_text)


def _wait_for_ngram_chart(screen: Screen, timeout: float = 30) -> None:
    deadline = time.time() + timeout
    last_text = ""
    while time.time() < deadline:
        last_text = _visible_text(screen)
        if (
            "Data viewer" in last_text
            and "Showing top 100 n-grams by frequency." in last_text
            and "Loading dashboard..." not in last_text
            and "No analysis found in the current session." not in last_text
            and "No n-gram data available." not in last_text
            and "Could not load n-gram results" not in last_text
        ):
            return
        screen.wait(0.25)
    raise AssertionError("N-gram chart did not finish loading.\n" + last_text)
