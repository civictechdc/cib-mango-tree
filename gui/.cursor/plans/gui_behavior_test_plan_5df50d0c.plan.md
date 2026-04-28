---
name: GUI behavior test plan
overview: Create a small, behavior-documenting test set for `gui/` using NiceGUI’s pytest plugin, focusing on current app behavior and avoiding edge-case expansion.
todos:
  - id: inspect-gui-testable-behaviors
    content: Map every non-__init__ module in gui/ to one basic, current-behavior test.
    status: pending
  - id: add-session-and-routing-tests
    content: Add basic behavior tests for root gui modules (session, main_workflow, base, routes, context, theme).
    status: pending
  - id: add-basic-page-behavior-tests
    content: Add one small current-behavior test for each module in gui/pages, gui/components, gui/components/stepper_steps, and gui/dashboards.
    status: pending
  - id: run-targeted-gui-tests
    content: Execute gui/tests and confirm all new behavior-documentation tests pass.
    status: pending
isProject: false
---

# Plan: Small Behavior Tests for `gui/`

## Plan Location
- This plan is stored in `gui/.cursor/plans/`.

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
  - `has_project_name()`, `has_selected_file()`, `has_project()` return expected booleans from current state.
- Route/dashboard dispatch behavior in [`gui/main_workflow.py`](gui/main_workflow.py):
  - `dashboard_view` chooses ngrams dashboard for analyzer id `ngrams`.
  - Non-ngrams path renders fallback placeholder text.
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
- If NiceGUI plugin fixture import fails, add the minimal pytest plugin registration in test config as a follow-up (no other scope expansion).
