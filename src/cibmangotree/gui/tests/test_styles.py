"""
Guard for the styling conventions in `gui.theme`.

Two things are checked:

1. **No retired spellings** in the files migrated to the shared constants. The
   scan is `gui._style_rules`, which walks `.classes()` / `.style()` call
   arguments in the AST rather than searching raw text, so `theme.py`
   legitimately *defining* a value does not trip it. That module also carries the
   rule tables and the `--fix` tool; this file is the pytest half of the same
   convention, and the only place the guarded file list lives.
2. **The migrated screens actually render with the constants.** The existing
   tests for both screens stop at an early return before any styled element is
   built, so they stay green even with the migration broken.

"""

from __future__ import annotations

import re
from datetime import datetime
from pathlib import Path
from unittest.mock import MagicMock

import polars as pl
from nicegui import ui
from nicegui.testing import User

from cibmangotree.analyzer_interface import AnalyzerParam, IntegerParam
from cibmangotree.analyzers.hashtags.hashtags_base.interface import (
    OUTPUT_COL_GINI,
    OUTPUT_COL_TIMESPAN,
)
from cibmangotree.analyzers.ngrams.ngrams_base.interface import (
    COL_NGRAM_ID,
    COL_NGRAM_LENGTH,
)
from cibmangotree.analyzers.ngrams.ngrams_stats.interface import (
    COL_NGRAM_DISTINCT_POSTER_COUNT,
    COL_NGRAM_TOTAL_REPS,
    COL_NGRAM_WORDS,
)
from cibmangotree.gui import theme
from cibmangotree.gui._style_rules import (
    BLOCKING,
    RETIRED_CLASS_TOKENS,
    in_scope,
    scan_source,
)
from cibmangotree.gui.components.analysis import AnalysisParamsCard
from cibmangotree.gui.dashboards.hashtags.plots import plot_gini_echart
from cibmangotree.gui.dashboards.ngrams.plots import plot_scatter_echart
from cibmangotree.gui.pages.analysis_workflow.run_step import RunAnalysisStep
from cibmangotree.gui.session import GuiSession
from cibmangotree.gui.theme import (
    CARD_CONTENT,
    CARD_PARAM,
    CHART_HIGHLIGHT,
    ICON_INFO,
    STYLE_CENTERED,
)

GUI_ROOT = Path(theme.__file__).parent
REPO_ROOT = GUI_ROOT.parents[2]

#: The sweep is finished, so this is the whole GUI package. `in_scope` drops
#: `gui/tests/` along with `theme.py` and `_style_rules.py`, which legitimately
#: contain the spellings the convention retires — one defines them, the other
#: names them.
GUARDED = [GUI_ROOT]


def guarded_files() -> list[Path]:
    """Expand `GUARDED` to the Python files the tool would actually look at."""
    return sorted(
        {
            found
            for path in GUARDED
            for found in ([path] if path.is_file() else path.rglob("*.py"))
            if in_scope(found)
        }
    )


def scan(paths: list[Path]) -> list[str]:
    """Report every convention violation reaching a `.classes()` / `.style()` call.

    Advice — "this literal already has a constant" — is deliberately not a
    violation, so a pull request about something else is never blocked by it.
    """
    return [
        finding.render(REPO_ROOT)
        for path in paths
        for finding in scan_source(path.read_text(encoding="utf-8"), path)
        if finding.level in BLOCKING
    ]


# --- The guard -----------------------------------------------------------


def test_the_whole_gui_contains_no_retired_spellings() -> None:
    """The end of the sweep: not a sample, the entire package."""
    assert scan(guarded_files()) == []


def test_the_guard_actually_reaches_every_gui_module() -> None:
    """An empty scan would also pass if `GUARDED` resolved to nothing."""
    covered = guarded_files()
    names = {path.name for path in covered}

    assert len(covered) > 40, f"only {len(covered)} files guarded"
    assert {"base.py", "run_step.py", "export_outputs.py"} <= names
    assert not {"theme.py", "_style_rules.py"} & names
    assert not any("tests" in path.parts for path in covered)


def test_the_guard_covers_what_the_hook_covers() -> None:
    """The hook's `files:` pattern and `GUARDED` widen together, or the two
    halves of the convention drift apart."""
    config = (REPO_ROOT / ".pre-commit-config.yaml").read_text()
    patterns = [
        line.split("files:", 1)[1].strip()
        for line in config.splitlines()
        if line.strip().startswith("files:")
    ]

    assert patterns, "the gui-styles hook has no files: pattern"
    covered = [
        path
        for path in guarded_files()
        if any(
            re.match(pattern, path.relative_to(REPO_ROOT).as_posix())
            for pattern in patterns
        )
    ]
    uncovered = set(guarded_files()) - set(covered)

    assert uncovered == set(), "pytest guards files the hook does not"


def test_scan_reports_a_reintroduced_spelling(tmp_path: Path) -> None:
    """A guard that cannot fail is worse than none."""
    offender = tmp_path / "regression.py"
    offender.write_text(
        'ui.label("x").classes("text-grey q-mb-md")\n'
        'ui.column().style("max-width: 960px; margin: 0 auto;")\n',
        encoding="utf-8",
    )

    problems = scan([offender])

    assert len(problems) == 3
    assert any("`text-grey` is retired" in p for p in problems)
    assert any("`q-mb-md` -> `mb-4`" in p for p in problems)
    assert any("`max-width: 960px` has a constant" in p for p in problems)


# --- The migrated screens actually render with the constants -------------


def _assert_styled(element, constant: str) -> None:
    """The constant's tokens are applied, and no *extra* retired token is.

    Tokens the constant itself owns are exempt: `ICON_INFO` is spelled
    `text-grey-7`, which is retired only as a hand-typed literal. Telling those
    apart is the AST scan's job, at the source level where it can.
    """
    expected = set(constant.split())
    applied = set(element.classes)
    assert expected <= applied, f"expected {constant!r}, got {sorted(applied)}"

    stray = (applied - expected) & RETIRED_CLASS_TOKENS.keys()
    assert not stray, f"retired tokens applied alongside {constant!r}: {sorted(stray)}"


async def test_populated_params_card_uses_shared_constants(user: User) -> None:
    params = [
        AnalyzerParam(
            id="window",
            human_readable_name="Window",
            description="How many rows to consider",
            type=IntegerParam(min=1, max=10),
        )
    ]

    @ui.page("/params-card-styles")
    def page() -> None:
        AnalysisParamsCard(params=params, default_values={"window": 3})

    await user.open("/params-card-styles")

    _assert_styled(next(iter(user.find(kind=ui.card).elements)), CARD_PARAM)
    _assert_styled(next(iter(user.find(kind=ui.icon).elements)), ICON_INFO)


async def test_valid_run_summary_uses_shared_constants(
    user: User, gui_session: GuiSession
) -> None:
    analyzer = MagicMock()
    analyzer.name = "Test Analyzer"
    gui_session.selected_analyzer = analyzer
    gui_session.column_mapping = {"user_id": "author"}
    gui_session.analysis_params = {}

    step = RunAnalysisStep(gui_session, MagicMock())

    @ui.page("/run-step-styles")
    def page() -> None:
        step.render()

    await user.open("/run-step-styles")

    _assert_styled(next(iter(user.find(kind=ui.card).elements)), CARD_CONTENT)

    expected = {
        part.split(":", 1)[0].strip(): part.split(":", 1)[1].strip()
        for part in STYLE_CENTERED.split(";")
        if part.strip()
    }
    assert any(
        expected.items() <= column.style.items()
        for column in user.find(kind=ui.column).elements
    ), "no column carries STYLE_CENTERED"


# --- Chart colours -------------------------------------------------------


def test_every_chart_highlight_is_the_same_constant() -> None:
    """One concept, one value — across both dashboards and every series."""
    gini = plot_gini_echart(
        pl.DataFrame(
            {
                OUTPUT_COL_TIMESPAN: [datetime(2024, 1, 1), datetime(2024, 1, 2)],
                OUTPUT_COL_GINI: [0.1, 0.9],
                "gini_smooth": [0.2, 0.8],
            }
        ),
        smooth=True,
    )
    scatter = plot_scatter_echart(
        pl.DataFrame(
            {
                COL_NGRAM_ID: [0, 1, 2],
                COL_NGRAM_LENGTH: [1, 2, 3],
                COL_NGRAM_DISTINCT_POSTER_COUNT: [5, 5, 5],
                COL_NGRAM_TOTAL_REPS: [10, 10, 10],
                COL_NGRAM_WORDS: ["w", "w", "w"],
            }
        )
    )

    emphasis = {
        series["emphasis"]["itemStyle"]["color"]
        for option in (gini, scatter)
        for series in option["series"]
    }
    assert emphasis == {CHART_HIGHLIGHT}
