"""Regression checks for the styling hook and its pilot screens."""

import re
from pathlib import Path
from unittest.mock import MagicMock

import pytest
import yaml
from nicegui import ui
from nicegui.testing import User

from cibmangotree.analyzer_interface import AnalyzerParam, IntegerParam
from cibmangotree.gui import _style_rules as rules
from cibmangotree.gui.components.analysis import AnalysisParamsCard
from cibmangotree.gui.pages.analysis_workflow.run_step import RunAnalysisStep
from cibmangotree.gui.session import GuiSession
from cibmangotree.gui.theme import (
    CARD_CONTENT,
    CARD_PARAM,
    COL_STEP_BODY,
    ICON_INFO,
    STYLE_CENTERED,
    gui_props,
)


def test_pilot_files_contain_no_hardcoded_styles() -> None:
    findings = [
        finding.render()
        for path in rules.files_to_check()
        for finding in rules.scan_source(path.read_text(encoding="utf-8"), path)
    ]
    assert findings == []


def test_hook_covers_exactly_the_files_to_check() -> None:
    config = yaml.safe_load((rules.REPO_ROOT / ".pre-commit-config.yaml").read_text())
    hook = next(
        hook
        for repo in config["repos"]
        for hook in repo["hooks"]
        if hook["id"] == "gui-styles"
    )
    covered = {
        path
        for path in rules.GUI_ROOT.rglob("*.py")
        if re.match(hook["files"], path.relative_to(rules.REPO_ROOT).as_posix())
    }
    assert covered == set(rules.files_to_check())
    assert all(path.is_file() for path in rules.files_to_check())
    assert hook["entry"] == "python src/cibmangotree/gui/_style_rules.py"


@pytest.mark.parametrize(
    "source, expected",
    [
        (
            'ui.label("x").classes("text-grey q-mb-md")',
            ["text-grey q-mb-md"],
        ),
        (
            'ui.label("x").classes(add="text-medium", remove="text-gray-600")',
            ["text-medium", "text-gray-600"],
        ),
        ('ui.label("x").classes("w-full gap-2")', ["w-full gap-2"]),
        ('ui.label("x").classes(f"{extra} mb-4")', ["<f-string>"]),
        ('ui.label("café").classes("text-grey")', ["text-grey"]),
        (
            'ui.label("x").style("max-width: 960px; margin: 0 auto;")',
            ["max-width: 960px; margin: 0 auto;"],
        ),
        ('ui.label("x").style("max-width: 960px;")', ["max-width: 960px;"]),
        ('ui.label("x").style("")', [""]),
        ('ui.button("x").props("outline")', ["outline"]),
    ],
)
def test_scan_rejects_style_string_literals(source: str, expected: list[str]) -> None:
    findings = rules.scan_source(source, Path("example.py"))
    assert [finding.literal for finding in findings] == expected
    assert all(finding.replacement for finding in findings)


def test_scan_retired_tokens_get_specific_hints() -> None:
    findings = rules.scan_source(
        'ui.label("x").classes("text-grey q-mb-md")', Path("example.py")
    )
    assert findings[0].replacement == "TEXT_MUTED; mb-4"


def test_scan_ignores_prose_and_named_constants() -> None:
    source = (
        '# ui.label("x").classes("text-grey")\n'
        'message = "text-grey q-mb-md"\n'
        "ui.label(message)\n"
        "ui.label(step).classes(ICON_INFO)\n"
        "ui.column().style(STYLE_CENTERED)\n"
        "ui.label(step).classes(add=TEXT_MUTED, remove=TEXT_WEIGHT_MEDIUM)\n"
        'ui.button(label, color="primary").props(gui_props.outline)\n'
    )
    assert rules.scan_source(source, Path("example.py")) == []


def test_cli_reports_a_regression_without_rewriting(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture
) -> None:
    offender = tmp_path / "regression.py"
    source = 'ui.label("x").classes("text-medium")\n'
    offender.write_text(source, encoding="utf-8")
    monkeypatch.setattr(rules, "files_to_check", lambda: (offender,))

    assert rules.main([str(offender)]) == 1
    assert "font-medium" in capsys.readouterr().out
    assert offender.read_text(encoding="utf-8") == source


def test_cli_skips_unmigrated_files(tmp_path: Path) -> None:
    unmigrated = tmp_path / "future_migration.py"
    unmigrated.write_text('ui.label("x").classes("text-grey")', encoding="utf-8")
    assert rules.main([str(unmigrated)]) == 0


@pytest.mark.parametrize("source", ['ui.label("x"', None])
def test_cli_fails_when_a_file_to_check_cannot_be_checked(
    source: str | None,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture,
) -> None:
    path = tmp_path / "broken.py"
    if source is not None:
        path.write_text(source, encoding="utf-8")
    monkeypatch.setattr(rules, "files_to_check", lambda: (path,))
    assert rules.main([]) == 1
    assert "cannot check styling" in capsys.readouterr().out


def _assert_styled(element, constant: str) -> None:
    expected = set(constant.split())
    applied = set(element.classes)
    assert expected <= applied, f"expected {constant!r}, got {sorted(applied)}"
    stray = (applied - expected) & rules.RETIRED_CLASS_TOKENS.keys()
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

    step_body_tokens = set(COL_STEP_BODY.split())
    assert any(
        step_body_tokens <= set(column.classes)
        for column in user.find(kind=ui.column).elements
    ), "no column carries COL_STEP_BODY"

    expected = {
        part.split(":", 1)[0].strip(): part.split(":", 1)[1].strip()
        for part in STYLE_CENTERED.split(";")
        if part.strip()
    }
    assert any(
        expected.items() <= column.style.items()
        for column in user.find(kind=ui.column).elements
    ), "no column carries STYLE_CENTERED"
