"""Check migrated GUI modules without importing NiceGUI or changing files.

The hook and pytest use the same scanner. Widen FILES_TO_CHECK and the hook's
files pattern together as more modules are migrated.

Modules in FILES_TO_CHECK must not pass string or f-string literals to
.classes(), .style(), or .props(), and must not pass string literals to
color= — import named constants from theme.py instead (COLOR_*, PROPS_*,
CARD_*, …). Retired Quasar/layout tokens still get specific replacement hints
when they appear in a banned class literal.
"""

from __future__ import annotations

import argparse
import ast
import re
from pathlib import Path
from typing import NamedTuple

GUI_ROOT = Path(__file__).resolve().parent
REPO_ROOT = GUI_ROOT.parents[2]
FILES_TO_CHECK = (
    "base.py",
    "components/analysis.py",
    "components/choice_fork.py",
    "components/exit_confirmation.py",
    "components/export_outputs.py",
    "components/import_options.py",
    "components/manage_analyses.py",
    "components/new_project_dialog.py",
    "components/toggle.py",
    "components/upload/upload_button.py",
    "dashboards/base_dashboard.py",
    "dashboards/hashtags/dashboard.py",
    "dashboards/ngrams/dashboard.py",
    "dashboards/placeholder/dashboard.py",
    "dashboards/time_coordination/compare_page.py",
    "dashboards/time_coordination/dashboard.py",
    "pages/analysis_config_and_run.py",
    "pages/analysis_post.py",
    "pages/analysis_workflow/analyzer_step.py",
    "pages/analysis_workflow/column_mapping_step.py",
    "pages/analysis_workflow/params_step.py",
    "pages/analysis_workflow/run_step.py",
    "pages/analyzer_previous.py",
    "pages/dataset_preview.py",
    "pages/importer.py",
    "pages/start.py",
)

THEME_CONSTANT_HINT = "a named constant from cibmangotree.gui.theme"

RETIRED_CLASS_TOKENS = {
    "q-mb-xs": "mb-1",
    "q-mb-sm": "mb-2",
    "q-mb-md": "mb-4",
    "q-mb-lg": "mb-6",
    "q-mt-xs": "mt-1",
    "q-mt-sm": "mt-2",
    "q-mt-md": "mt-4",
    "q-pa-md": "p-4",
    "no-shadow": "shadow-none",
    "text-bold": "font-bold",
    "text-weight-bold": "font-bold",
    "text-weight-medium": "font-medium",
    "text-medium": "font-medium",
    "text-grey": "TEXT_MUTED",
    "text-grey-5": "TEXT_MUTED for text; a semantic constant for icons",
    "text-grey-6": "TEXT_MUTED for text; a semantic constant for icons",
    "text-grey-7": "TEXT_MUTED for text; ICON_INFO for info icons",
    "text-gray-500": "TEXT_MUTED",
    "text-gray-600": "TEXT_MUTED",
}


class Finding(NamedTuple):
    path: Path
    line: int
    literal: str
    replacement: str

    def render(self) -> str:
        path = self.path.resolve()
        where = path.relative_to(REPO_ROOT) if path.is_relative_to(REPO_ROOT) else path
        return f"{where}:{self.line}: replace {self.literal!r} with {self.replacement}"


def files_to_check() -> tuple[Path, ...]:
    return tuple(GUI_ROOT / path for path in FILES_TO_CHECK)


def _replacement_for_class_literal(value: str) -> str:
    tokens = re.findall(r"\S+", value)
    retired = [
        RETIRED_CLASS_TOKENS[token] for token in tokens if token in RETIRED_CLASS_TOKENS
    ]
    if retired:
        return "; ".join(retired)
    return THEME_CONSTANT_HINT


def _replacement_for_style_literal(value: str) -> str:
    stripped = value.strip().rstrip(";")
    if not stripped:
        return "STYLE_CLEAR"
    return THEME_CONSTANT_HINT


def _flag_string_arg(argument: ast.expr, path: Path, findings: list[Finding]) -> None:
    if isinstance(argument, ast.Constant) and isinstance(argument.value, str):
        findings.append(
            Finding(path, argument.lineno, argument.value, THEME_CONSTANT_HINT)
        )
    elif isinstance(argument, ast.JoinedStr):
        findings.append(
            Finding(path, argument.lineno, "<f-string>", THEME_CONSTANT_HINT)
        )


def scan_source(source: str, path: Path) -> list[Finding]:
    findings: list[Finding] = []
    for node in ast.walk(ast.parse(source)):
        if not isinstance(node, ast.Call):
            continue

        for keyword in node.keywords:
            if keyword.arg == "color":
                if isinstance(keyword.value, ast.Constant) and isinstance(
                    keyword.value.value, str
                ):
                    findings.append(
                        Finding(
                            path,
                            keyword.value.lineno,
                            keyword.value.value,
                            THEME_CONSTANT_HINT,
                        )
                    )
                elif isinstance(keyword.value, ast.JoinedStr):
                    findings.append(
                        Finding(
                            path,
                            keyword.value.lineno,
                            "<f-string>",
                            THEME_CONSTANT_HINT,
                        )
                    )

        if not isinstance(node.func, ast.Attribute):
            continue
        method = node.func.attr
        if method not in {"classes", "style", "props"}:
            continue
        for argument in [*node.args, *(keyword.value for keyword in node.keywords)]:
            if (
                method == "classes"
                and isinstance(argument, ast.Constant)
                and isinstance(argument.value, str)
            ):
                findings.append(
                    Finding(
                        path,
                        argument.lineno,
                        argument.value,
                        _replacement_for_class_literal(argument.value),
                    )
                )
            elif (
                method == "style"
                and isinstance(argument, ast.Constant)
                and isinstance(argument.value, str)
            ):
                findings.append(
                    Finding(
                        path,
                        argument.lineno,
                        argument.value,
                        _replacement_for_style_literal(argument.value),
                    )
                )
            elif method == "props":
                _flag_string_arg(argument, path, findings)
            elif isinstance(argument, ast.JoinedStr) and method in {
                "classes",
                "style",
            }:
                findings.append(
                    Finding(
                        path,
                        argument.lineno,
                        "<f-string>",
                        THEME_CONSTANT_HINT,
                    )
                )
    return findings


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("paths", nargs="*", type=Path)
    args = parser.parse_args(argv)
    allowed = set(files_to_check())
    paths = sorted({path.resolve() for path in args.paths} if args.paths else allowed)
    failed = False
    for path in paths:
        if path not in allowed:
            continue
        try:
            findings = scan_source(path.read_text(encoding="utf-8-sig"), path)
        except (OSError, SyntaxError, UnicodeError) as error:
            print(f"{path}: cannot check styling: {error}")
            failed = True
            continue
        for finding in findings:
            print(finding.render())
        failed |= bool(findings)
    return int(failed)


if __name__ == "__main__":
    raise SystemExit(main())
