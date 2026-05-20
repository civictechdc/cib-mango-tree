---
name: GUI behavior test plan
overview: Create a small, behavior-documenting test set for `gui/` using NiceGUI’s pytest plugin, focusing on current app behavior and avoiding edge-case expansion.
todos:
  - id: inspect-gui-testable-behaviors
    content: Map every non-__init__ module in gui/ to one basic, current-behavior test.
    status: completed
  - id: add-session-and-routing-tests
    content: Add basic behavior tests for root gui modules (session, main_workflow, base, routes, context, theme).
    status: completed
  - id: add-basic-page-behavior-tests
    content: Add one small current-behavior test for each module in gui/pages, gui/components, gui/components/stepper_steps, and gui/dashboards.
    status: completed
  - id: run-targeted-gui-tests
    content: Execute gui/tests and confirm all new behavior-documentation tests pass.
    status: completed
isProject: false
---

# Plan: Small Behavior Tests for `gui/`

## Plan Location
- This plan is stored in `gui/.cursor/plans/`.

## NiceGUI official docs (testing & User simulation)

Primary guide: [NiceGUI — Testing](https://nicegui.io/documentation/section_testing). The snippets below match the **`test_app.py`** / **`pytest.ini`** examples on that page; upstream source: [`website/documentation/content/section_testing.py`](https://github.com/zauberzeug/nicegui/blob/main/website/documentation/content/section_testing.py).

### Canonical examples (`test_app.py` and `pytest.ini`)

The docs pair a minimal **`test_app.py`** with **`pytest.ini`**. Tests use **`async def`**, annotate **`user: User`**, **`await user.open`**, **`await user.should_see`**, and **`user.find(...).click()`** (click is synchronous).

**`test_app.py`** (from docs):

```python
from nicegui import ui
from nicegui.testing import User

async def test_click(user: User) -> None:
    await user.open("/")
    await user.should_see("Click me")
    user.find(ui.button).click()
    await user.should_see("Hello World!")
```

**`pytest.ini`** (from docs):

```ini
[pytest]
asyncio_mode = auto
main_file = app.py
addopts = -p nicegui.testing.user_plugin
```

Meaning of each **`pytest.ini`** line:

| Setting | Role |
|---------|------|
| **`asyncio_mode = auto`** | Lets pytest-asyncio run **`async def`** tests (required for **`user`**). See [User → async execution](https://nicegui.io/documentation/user#async_execution). |
| **`main_file = app.py`** | Entry script containing **`ui.run(...)`** (and app **`@ui.page`** registrations). The plugin **`runpy`**-loads this file before tests so routes exist. |
| **`addopts = -p nicegui.testing.user_plugin`** | Loads only the fast **`user`** fixture plugin; use **`-p nicegui.testing.plugin`** if you also need the **`screen`** (browser) fixture. |

**Set main file** (official three options):

1. Name the entry file **`main.py`** (default lookup).
2. Set **`main_file`** in **`pytest.ini`** (or **`pyproject.toml`** **`[tool.pytest.ini_options]`**).
3. Use **`@pytest.mark.nicegui_main_file("path/to/app.py")`** per test when multiple apps exist (NiceGUI ≥ 3.1).

You still need **`asyncio_mode`** and the chosen plugin registered (**`pytest.ini`** **`addopts`** or **`conftest.py`** **`pytest_plugins`**).

### How this repo maps (Mango Tree)

| Docs pattern | This project |
|--------------|----------------|
| **`pytest.ini` `[pytest]`** | **`[tool.pytest.ini_options]`** in **`pyproject.toml`** (same keys: **`asyncio_mode`**, **`main_file`**, etc.). |
| **`addopts = -p nicegui.testing.user_plugin`** | **`pytest_plugins`** in **`gui/tests/conftest.py`** loads **`nicegui.testing.general_fixtures`** + **`nicegui.testing.user_plugin`** (**`general_fixtures`** provides **`nicegui_reset_globals`** and ini hooks used by **`user_plugin`**). |
| **`main_file = app.py`** | **`main_file = ""`** so the **`user`** fixture runs **`prepare_simulation()`** + **`ui.run(...)`** without **`runpy`**-loading a single app file; each test registers **`@ui.page(...)`** before **`await user.open(...)`**. Alternative: point **`main_file`** at a small script that registers Mango Tree routes (e.g. wraps **`gui_main`**). |
| **`from nicegui.testing import User`** | Prefer on **`user`** parameters for typing (matches doc **`test_app.py`**). |

Further upstream examples: [chat_app](https://github.com/zauberzeug/nicegui/tree/main/examples/chat_app), [todo_list](https://github.com/zauberzeug/nicegui/tree/main/examples/todo_list/), [authentication](https://github.com/zauberzeug/nicegui/tree/main/examples/authentication), [pytest example](https://github.com/zauberzeug/nicegui/tree/main/examples/pytests).

### User fixture (quick reference)

- [NiceGUI: User](https://nicegui.io/documentation/user): **`await user.open(path)`**; **`await user.should_see` / `should_not_see`**; **`user.find`** + **`.click()`** / **`.type(...)`**; **`ui.notify`** captured; **`ui.navigate`** replaced in simulation.
- **`NICEGUI_USER_SIMULATION`** is set by the **`user`** fixture; do not set it manually in tests.

## Scope
- Add a minimal set of tests under [`gui/tests`](gui/tests) to document **current** observable behavior only.
- Store all new GUI tests only in `gui/tests/` (no new test files outside this directory).
- Store tests by domain-specific subfolder names:
  - pages tests in `gui/tests/pages/`
  - components tests in `gui/tests/components/`
  - stepper tests in `gui/tests/stepper/`
  - dashboard tests in `gui/tests/dashboard/`
- Ensure coverage intent: every non-`__init__.py` module inside `gui/` gets at least one basic behavior test.
- Keep tests basic and narrow; no edge-case matrix, no refactors, no behavior changes.
- Require NiceGUI `user` fixture for UI-facing behavior tests.

## Targeted Test Files
- [`gui/tests/test_session.py`](gui/tests/test_session.py) (for `gui/session.py`)
- [`gui/tests/test_main_workflow.py`](gui/tests/test_main_workflow.py) (for `gui/main_workflow.py`)
- [`gui/tests/test_base.py`](gui/tests/test_base.py) (for `gui/base.py`)
- [`gui/tests/test_routes.py`](gui/tests/test_routes.py) (for `gui/routes.py`)
- [`gui/tests/test_context.py`](gui/tests/test_context.py) (for `gui/context.py`)
- [`gui/tests/test_theme.py`](gui/tests/test_theme.py) (for `gui/theme.py`)
- [`gui/tests/pages/test_pages_start.py`](gui/tests/pages/test_pages_start.py) (for `gui/pages/start.py`)
- [`gui/tests/pages/test_pages_project_new.py`](gui/tests/pages/test_pages_project_new.py) (for `gui/pages/project_new.py`)
- [`gui/tests/pages/test_pages_importer.py`](gui/tests/pages/test_pages_importer.py) (for `gui/pages/importer.py`)
- [`gui/tests/pages/test_pages_dataset_preview.py`](gui/tests/pages/test_pages_dataset_preview.py) (for `gui/pages/dataset_preview.py`)
- [`gui/tests/pages/test_pages_analyzer_select.py`](gui/tests/pages/test_pages_analyzer_select.py) (for `gui/pages/analyzer_select.py`)
- [`gui/tests/pages/test_pages_analysis_config_and_run.py`](gui/tests/pages/test_pages_analysis_config_and_run.py) (for `gui/pages/analysis_config_and_run.py`)
- [`gui/tests/pages/test_pages_project_select.py`](gui/tests/pages/test_pages_project_select.py) (for `gui/pages/project_select.py`)
- [`gui/tests/pages/test_pages_analyzer_previous.py`](gui/tests/pages/test_pages_analyzer_previous.py) (for `gui/pages/analyzer_previous.py`)
- [`gui/tests/pages/test_pages_analysis_post.py`](gui/tests/pages/test_pages_analysis_post.py) (for `gui/pages/analysis_post.py`)
- [`gui/tests/components/test_components_analysis.py`](gui/tests/components/test_components_analysis.py) (for `gui/components/analysis.py`)
- [`gui/tests/components/test_components_analysis_utils.py`](gui/tests/components/test_components_analysis_utils.py) (for `gui/components/analysis_utils.py`)
- [`gui/tests/components/test_components_choice_fork.py`](gui/tests/components/test_components_choice_fork.py) (for `gui/components/choice_fork.py`)
- [`gui/tests/components/test_components_import_options.py`](gui/tests/components/test_components_import_options.py) (for `gui/components/import_options.py`)
- [`gui/tests/components/test_components_manage_analyses.py`](gui/tests/components/test_components_manage_analyses.py) (for `gui/components/manage_analyses.py`)
- [`gui/tests/components/test_components_manage_projects.py`](gui/tests/components/test_components_manage_projects.py) (for `gui/components/manage_projects.py`)
- [`gui/tests/components/test_components_toggle.py`](gui/tests/components/test_components_toggle.py) (for `gui/components/toggle.py`)
- [`gui/tests/components/test_components_upload_button.py`](gui/tests/components/test_components_upload_button.py) (for `gui/components/upload/upload_button.py`)
- [`gui/tests/stepper/test_stepper_analyzer_step.py`](gui/tests/stepper/test_stepper_analyzer_step.py) (for `gui/components/stepper_steps/analyzer_step.py`)
- [`gui/tests/stepper/test_stepper_column_mapping_step.py`](gui/tests/stepper/test_stepper_column_mapping_step.py) (for `gui/components/stepper_steps/column_mapping_step.py`)
- [`gui/tests/stepper/test_stepper_params_step.py`](gui/tests/stepper/test_stepper_params_step.py) (for `gui/components/stepper_steps/params_step.py`)
- [`gui/tests/stepper/test_stepper_run_step.py`](gui/tests/stepper/test_stepper_run_step.py) (for `gui/components/stepper_steps/run_step.py`)
- [`gui/tests/dashboard/test_dashboards_base_dashboard.py`](gui/tests/dashboard/test_dashboards_base_dashboard.py) (for `gui/dashboards/base_dashboard.py`)
- [`gui/tests/dashboard/test_dashboards_ngrams.py`](gui/tests/dashboard/test_dashboards_ngrams.py) (for `gui/dashboards/ngrams.py`)

## Behavior Set to Capture
- `GuiSession` reset/validation behavior in [`gui/session.py`](gui/session.py):
  - `reset_project_workflow()` clears project/import-related fields.
  - `reset_analysis_workflow()` clears analyzer/analysis-related fields.
  - Validation helpers (`validate_project_selected()`, `validate_file_selected()`, `validate_project_name_set()`) match current state (names in code may differ from older “has_*” wording).
- Route/dashboard dispatch behavior in [`gui/main_workflow.py`](gui/main_workflow.py):
  - Dashboard route maps analyzer id `ngrams` to the ngrams dashboard class (`_DASHBOARD_REGISTRY`); logic lives in the dashboard page handler, not necessarily a named `dashboard_view` function.
  - Unknown analyzer maps to fallback placeholder text (“Dashboard coming soon”, etc.).
- Start/new-project page intent in [`gui/pages/start.py`](gui/pages/start.py) and [`gui/pages/project_new.py`](gui/pages/project_new.py):
  - Start page renders expected action controls.
  - New project submission with non-empty name stores `session.new_project_name` and proceeds.
  - Empty-name submit path keeps user on validation/warning path.
- Importer/preview guard rails in [`gui/pages/importer.py`](gui/pages/importer.py):
  - Missing uploaded file path triggers notify + redirect behavior.
  - Unsupported/detection-failure path triggers notify + redirect behavior.
- Root/gui module behaviors get one basic assertion each:
  - `gui/base.py` helpers/rendering scaffold behavior.
  - `gui/routes.py` route constants and path composition behavior.
  - `gui/context.py` context object wiring/default access behavior.
  - `gui/theme.py` theme setup call behavior.
- Every module in `gui/pages/`, `gui/components/`, `gui/components/stepper_steps/`, and `gui/dashboards/` gets one lightweight smoke behavior test (render + one clear current behavior), without edge-case expansion.

## Test Style and Constraints
- Use pytest + NiceGUI plugin fixtures for UI interaction checks.
- Use NiceGUI `user` fixture for UI interaction tests (open page, interact with controls, assert visible behavior).
- Mock external dependencies (`session.app`, importer factories, project creation, navigation calls) so tests stay small and deterministic.
- Prefer one behavior assertion per test where practical.
- Keep each test focused on observable output/state changes, not implementation internals.

## Validation
- Run targeted tests first:
  - `pytest gui/tests/test_session.py gui/tests/test_main_workflow.py gui/tests/test_base.py gui/tests/test_routes.py gui/tests/pages/test_pages_start.py gui/tests/pages/test_pages_project_new.py gui/tests/pages/test_pages_importer.py`
- If clean, run broader sanity pass:
  - `pytest gui/tests/`
- Config: [`gui/tests/conftest.py`](../../tests/conftest.py) registers **`nicegui.testing.general_fixtures`** + **`nicegui.testing.user_plugin`**; [`pyproject.toml`](../../../pyproject.toml) sets **`main_file`** (empty), **`asyncio_mode`**, and **`pytest-asyncio`** (see [`requirements-dev.txt`](../../../requirements-dev.txt)).
- Full **`nicegui.testing.plugin`** requires Selenium for **`screen`** tests; this suite uses user simulation only.
