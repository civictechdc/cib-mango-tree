"""Check the migrated GUI modules without importing NiceGUI or changing files.

The hook and pytest use the same scanner. Widen GUARDED_PATHS and the hook's
files pattern together as more modules are migrated. Only direct string and
f-string arguments to .classes() and .style() are checked; variable values and
arbitrary Python expressions are not evaluated.
"""

from __future__ import annotations

import argparse
import ast
import re
from pathlib import Path
from typing import Iterator, NamedTuple

GUI_ROOT = Path(__file__).resolve().parent
REPO_ROOT = GUI_ROOT.parents[2]
GUARDED_PATHS = (
    "components/analysis.py",
    "components/exit_confirmation.py",
    "components/export_outputs.py",
    "components/import_options.py",
    "components/new_project_dialog.py",
    "pages/analysis_workflow/run_step.py",
)

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
    "text-grey-6": "TEXT_MUTED for text; ICON_INFO for info icons",
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


def guarded_files() -> tuple[Path, ...]:
    return tuple(GUI_ROOT / path for path in GUARDED_PATHS)


def style_constants() -> dict[str, str]:
    """Read STYLE_* literals from theme.py without its pydantic dependency."""
    constants = {}
    tree = ast.parse((GUI_ROOT / "theme.py").read_text(encoding="utf-8"))
    for node in tree.body:
        if not isinstance(node, ast.Assign) or not isinstance(node.value, ast.Constant):
            continue
        if not isinstance(node.value.value, str):
            continue
        for target in node.targets:
            if isinstance(target, ast.Name) and target.id.startswith("STYLE_"):
                constants[node.value.value.strip().rstrip(";")] = target.id
    return constants


def literal_parts(argument: ast.expr) -> Iterator[tuple[str, int, bool, bool]]:
    """Yield static text with flags for boundaries next to an interpolation."""
    if isinstance(argument, ast.Constant) and isinstance(argument.value, str):
        yield argument.value, argument.lineno, True, True
    elif isinstance(argument, ast.JoinedStr):
        for index, part in enumerate(argument.values):
            if isinstance(part, ast.Constant) and isinstance(part.value, str):
                yield (
                    part.value,
                    part.lineno,
                    index == 0,
                    index == len(argument.values) - 1,
                )


def scan_source(source: str, path: Path) -> list[Finding]:
    findings = []
    styles = style_constants()
    for node in ast.walk(ast.parse(source)):
        if not isinstance(node, ast.Call) or not isinstance(node.func, ast.Attribute):
            continue
        method = node.func.attr
        if method not in {"classes", "style"}:
            continue
        for argument in [*node.args, *(keyword.value for keyword in node.keywords)]:
            if method == "style":
                if isinstance(argument, ast.Constant) and isinstance(
                    argument.value, str
                ):
                    value = argument.value.strip().rstrip(";")
                    if value in styles:
                        findings.append(
                            Finding(path, argument.lineno, value, styles[value])
                        )
                continue
            for text, line, left_edge, right_edge in literal_parts(argument):
                for match in re.finditer(r"\S+", text):
                    if match.start() == 0 and not left_edge:
                        continue
                    if match.end() == len(text) and not right_edge:
                        continue
                    token = match.group()
                    if token in RETIRED_CLASS_TOKENS:
                        findings.append(
                            Finding(
                                path,
                                line + text[: match.start()].count("\n"),
                                token,
                                RETIRED_CLASS_TOKENS[token],
                            )
                        )
    return findings


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("paths", nargs="*", type=Path)
    args = parser.parse_args(argv)
    allowed = set(guarded_files())
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
