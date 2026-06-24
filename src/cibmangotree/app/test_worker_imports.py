"""Guards the worker-process import boundary (#338, #339).

``AnalysisContext.run_worker`` is dispatched with ``nicegui.run.cpu_bound``,
which starts a child process using the ``spawn`` start method. The child
re-imports the modules that ``run_worker`` loads lazily
(``analysis_context.py:123-126``), so an import that only resolves because of the
development ``sys.path`` passes every in-process test and then fails in the
packaged app. That is what shipped as #338.

This test imports those modules in a fresh interpreter and checks for a clean
exit, which reproduces the child's import conditions without starting NiceGUI.
"""

import subprocess
import sys

# The modules AnalysisContext.run_worker imports lazily, kept in sync with
# src/cibmangotree/app/analysis_context.py:123-126.
WORKER_IMPORT_SOURCE = (
    "from cibmangotree.analyzers import suite\n"
    "from cibmangotree.preprocessing.series_semantic import all_semantics\n"
    "from cibmangotree.app.gui_progress_reporter import GUIProgressReporter\n"
)


def test_run_worker_imports_resolve_in_a_fresh_process():
    result = subprocess.run(
        [sys.executable, "-c", WORKER_IMPORT_SOURCE],
        capture_output=True,
        text=True,
        timeout=60,
    )
    assert result.returncode == 0, result.stderr
