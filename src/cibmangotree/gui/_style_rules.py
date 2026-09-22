from __future__ import annotations

import argparse
import ast
import io
import re
import tokenize
from collections import Counter
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, Iterator, NamedTuple

CLASS_TOKEN_SWAPS: dict[str, str] = {
    "q-mb-xs": "mb-1",  # 4px
    "q-mb-sm": "mb-2",  # 8px
    "q-mb-md": "mb-4",  # 16px
    "q-mb-lg": "mb-6",  # 24px
    "q-mt-xs": "mt-1",  # 4px
    "q-mt-sm": "mt-2",  # 8px
    "q-mt-md": "mt-4",  # 16px
    "q-pa-md": "p-4",  # 16px
    "no-shadow": "shadow-none",
    "text-bold": "font-bold",  # 700
    "text-weight-bold": "font-bold",  # 700
    "text-weight-medium": "font-medium",  # 500
}


class Report(NamedTuple):
    """A replacement a human has to choose, and the reason it is not automatic."""

    suggestion: str
    why: str


CLASS_TOKEN_REPORTS: dict[str, Report] = {
    "text-grey": Report(
        "TEXT_MUTED",
        "#9E9E9E is 2.68:1 on white and fails WCAG AA for normal text.",
    ),
    "text-grey-5": Report(
        "TEXT_MUTED",
        "#BDBDBD is 1.88:1 on white and fails WCAG AA for normal text.",
    ),
    "text-grey-6": Report(
        "TEXT_MUTED, or ICON_INFO on an info affordance",
        "#9E9E9E is 2.68:1 on white and fails WCAG AA for normal text.",
    ),
    "text-grey-7": Report(
        "TEXT_MUTED, or ICON_INFO on an info affordance",
        "#757575 is 4.61:1 — it passes, but sits on the 4.5:1 boundary.",
    ),
    "text-gray-500": Report(
        "TEXT_MUTED",
        "Tailwind v4 greys are cool-tinted against a green-and-orange brand.",
    ),
    "text-gray-600": Report(
        "TEXT_MUTED",
        "Tailwind v4 greys are cool-tinted against a green-and-orange brand.",
    ),
    "text-medium": Report(
        "font-medium",
        "dead CSS — neither Quasar nor Tailwind defines it, so it has always "
        "computed to 400. The swap CHANGES RENDERING (400 -> 500).",
    ),
}

# --- theme.py, read rather than imported ------------------------------------

#: The prefixes `docs/guides/contributing/styling.md` reserves for class strings.
#: Anything else in `theme.py` is a colour or a `STYLE_*` CSS declaration.
_CLASS_PREFIXES = ("CARD_", "ROW_", "COL_", "TEXT_", "ICON_")


def _resolve(node: ast.expr, known: dict[str, str]) -> str | None:
    """A plain string, or an f-string built only from constants already read."""
    if isinstance(node, ast.Constant) and isinstance(node.value, str):
        return node.value
    if not isinstance(node, ast.JoinedStr):
        return None
    out: list[str] = []
    for part in node.values:
        if isinstance(part, ast.Constant) and isinstance(part.value, str):
            out.append(part.value)
        elif isinstance(part, ast.FormattedValue) and isinstance(part.value, ast.Name):
            if part.value.id not in known:
                return None
            out.append(known[part.value.id])
        else:
            return None
    return "".join(out)


def read_theme_constants(path: Path | None = None) -> dict[str, str]:
    """Every string constant in `theme.py`, without importing it.

    Importing would pull in pydantic, and the pre-commit hook runs in CI where the
    project is deliberately not installed. Parsing keeps this module standard
    library only *and* removes the second copy of the constants that would
    otherwise drift out of step with `theme.py`.
    """
    path = path or Path(__file__).resolve().parent / "theme.py"
    constants: dict[str, str] = {}
    for node in ast.parse(path.read_text(encoding="utf-8")).body:
        if not isinstance(node, ast.Assign) or len(node.targets) != 1:
            continue
        target = node.targets[0]
        if not isinstance(target, ast.Name) or not target.id.isupper():
            continue
        value = _resolve(node.value, constants)
        if value is not None:
            constants[target.id] = value
    if not constants:
        raise RuntimeError(f"no constants found in {path} — has its shape changed?")
    return constants


_THEME = read_theme_constants()

#: CSS declarations inside `.style()` that now have a named constant, keyed by the
#: first declaration so `max-width: 960px; margin: 0 auto;` matches on its head.
STYLE_DECLARATION_REPORTS: dict[str, str] = {
    value.split(";")[0].strip(): name
    for name, value in _THEME.items()
    if name.startswith("STYLE_")
}

#: Class strings that already have a constant, keyed by token *set* so that order
#: drift (`"w-full items-center"` vs `"items-center w-full"`) still matches.
CONSTANT_BY_TOKEN_SET: dict[frozenset[str], str] = {
    frozenset(value.split()): name
    for name, value in _THEME.items()
    if name.startswith(_CLASS_PREFIXES)
}

#: Single tokens that *are* a semantic constant's whole value, and so should be
#: reached through the constant even inside a longer class string. Kept to the
#: one token where the indirection is the point; `text-h6` is a plain typography
#: class that composes into many strings, and flagging all 16 would be noise.
CONSTANT_BY_TOKEN: dict[str, str] = {"text-grey-8": "TEXT_MUTED"}

#: Quasar classes the convention keeps permanently. Tailwind has no typography
#: scale, and the brand colours are registered as Quasar names by `ui.colors()`
#: in `gui/base.py`. Listed so it is explicit that `text-body2` and
#: `text-subtitle2` are correct rather than merely unflagged.
QUASAR_KEPT: frozenset[str] = frozenset(
    {
        "text-h1", "text-h2", "text-h3", "text-h4", "text-h5", "text-h6",
        "text-subtitle1", "text-subtitle2",
        "text-body1", "text-body2",
        "text-caption", "text-overline",
        "text-primary", "text-secondary", "text-accent",
        "text-positive", "text-negative", "text-warning", "text-info",
        "text-dark", "text-white", "text-black", "text-cancel",
    }
)  # fmt: skip

#: A Quasar utility class with no measured Tailwind equivalent. Utilities belong
#: to Tailwind under the convention, so these need a human, not a guess.
_QUASAR_UTILITY = re.compile(r"^q-[a-z]")

#: How often a literal has to repeat before it is worth a shared constant.
PROMOTION_THRESHOLD = 3

#: Every token this module objects to, whatever the reason. `gui/tests/test_styles.py`
#: uses it to assert that no retired spelling survives in a migrated file.
RETIRED_CLASS_TOKENS: dict[str, str] = {
    **{token: swap for token, swap in CLASS_TOKEN_SWAPS.items()},
    **{token: report.suggestion for token, report in CLASS_TOKEN_REPORTS.items()},
}

GUIDE = "docs/guides/contributing/styling.md"
MODULE = "src/cibmangotree/gui/_style_rules.py"

# --- Findings ------------------------------------------------------------

FIXED = "FIXED"
FIXABLE = "FIXABLE"
NEEDS_HUMAN = "NEEDS A HUMAN"
CONSIDER = "CONSIDER"

#: Levels that should stop a commit. A `CONSIDER` never does — this tool must not
#: block a pull request that is about something else.
BLOCKING = frozenset({FIXED, FIXABLE, NEEDS_HUMAN})


@dataclass(frozen=True)
class Finding:
    level: str
    path: Path
    line: int
    summary: str
    detail: str = ""

    def render(self, root: Path | None = None) -> str:
        try:
            where = self.path.relative_to(root) if root else self.path
        except ValueError:
            where = self.path
        head = f"{self.level:<14} {where}:{self.line}  {self.summary}"
        if not self.detail:
            return head
        pad = " " * 15
        return "\n".join([head, *(f"{pad}{line}" for line in self.detail.splitlines())])


# --- Locating the literals -----------------------------------------------


@dataclass(frozen=True)
class StyleLiteral:
    """One string literal reaching a `.classes()` or `.style()` argument.

    `start` and `end` are character offsets into `lines[row - 1]` bounding the
    literal's *inner* text — the quotes are outside the span, so an edit can never
    unbalance them.

    `left_edge` / `right_edge` say whether that span boundary is a real end of the
    string. They are only ever false for part of an f-string, where the boundary
    abuts an interpolation and a class token touching it is half-written:
    `f"q-mb-md{suffix}"` must not be swapped, because what renders is `q-mb-md`
    glued to something else.
    """

    method: str
    row: int
    start: int
    end: int
    text: str
    left_edge: bool = True
    right_edge: bool = True
    decline: str | None = None


def _byte_col(line: str, col: int) -> int:
    """Character offset -> UTF-8 byte offset, the frame `ast` reports in."""
    return len(line[:col].encode("utf-8"))


def _split_lines(source: str) -> list[str]:
    """Split on `\\n` only, keeping any `\\r` at the end of its line.

    `str.splitlines()` would also break on form feed and the Unicode line
    separators, which `tokenize` does not — the two would disagree about row
    numbers. Rejoining with `"\\n"` reproduces the file byte for byte.
    """
    return source.split("\n")


def _eligible(source: str) -> dict[tuple[int, int], tuple[str, int, int]]:
    """Map a literal's start position to its method and end position.

    Positions are `(row, utf-8 byte column)`, the frame `ast` reports in.
    f-strings are keyed by their `JoinedStr`, which starts at the `f` prefix.
    """
    found: dict[tuple[int, int], tuple[str, int, int]] = {}
    for node in ast.walk(ast.parse(source)):
        if not isinstance(node, ast.Call) or not isinstance(node.func, ast.Attribute):
            continue
        if node.func.attr not in ("classes", "style"):
            continue
        for arg in [*node.args, *(kw.value for kw in node.keywords)]:
            constant = isinstance(arg, ast.Constant) and isinstance(arg.value, str)
            if not constant and not isinstance(arg, ast.JoinedStr):
                continue
            found[(arg.lineno, arg.col_offset)] = (
                node.func.attr,
                arg.end_lineno,
                arg.end_col_offset,
            )
    return found


def _unquote(token: tokenize.TokenInfo) -> tuple[int, int, str, str] | None:
    """Return `(inner_start, inner_end, text, prefix)` for a single-line STRING."""
    raw = token.string
    quote_at = next((i for i, ch in enumerate(raw) if ch in "\"'"), -1)
    if quote_at < 0:
        return None
    prefix = raw[:quote_at]
    fence = 3 if raw[quote_at : quote_at + 3] in ('"""', "'''") else 1
    if fence == 3:
        return None
    start = token.start[1] + quote_at + fence
    return start, token.end[1] - fence, raw[quote_at + fence : -fence], prefix


def iter_style_literals(source: str) -> Iterator[StyleLiteral]:
    """Yield every literal reaching a `.classes()` / `.style()` argument.

    Parts of an f-string and of an implicit concatenation are yielded separately,
    so a retired token is reported wherever it is written. Only the parts that are
    safe to edit in place come back without a `decline` reason.
    """
    lines = _split_lines(source)
    eligible = _eligible(source)
    chunks = [line + "\n" for line in lines[:-1]] + ([lines[-1]] if lines[-1] else [])
    stream = iter(chunks)

    tokens = list(tokenize.generate_tokens(lambda: next(stream, "")))
    index = 0
    while index < len(tokens):
        token = tokens[index]
        index += 1
        # ENDMARKER sits on a row past the last line, so check the type first.
        if token.type not in (tokenize.STRING, tokenize.FSTRING_START):
            continue
        row, col = token.start
        key = (row, _byte_col(lines[row - 1], col))
        if key not in eligible:
            continue
        method, end_row, end_byte_col = eligible[key]

        if token.type == tokenize.FSTRING_START:
            parts_out: list[StyleLiteral] = []
            index = _read_fstring(tokens, index, method, parts_out)
            yield from parts_out
            continue

        # `ast` merges implicitly concatenated strings into one node, so keep
        # taking STRING tokens until one ends where the node does.
        parts = [token]
        while index < len(tokens) and not _ends_at(
            parts[-1], lines, end_row, end_byte_col
        ):
            if tokens[index].type == tokenize.STRING:
                parts.append(tokens[index])
            index += 1
        for part in parts:
            yield _plain_literal(part, method, concatenated=len(parts) > 1)


def _ends_at(token: tokenize.TokenInfo, lines: list[str], row: int, col: int) -> bool:
    """Does this token end exactly where `ast` said the literal ends?"""
    return token.end[0] == row and _byte_col(lines[row - 1], token.end[1]) == col


def _plain_literal(
    part: tokenize.TokenInfo, method: str, *, concatenated: bool
) -> StyleLiteral:
    """One STRING token, carrying the reason it may not be edited in place.

    Declining is never silent — the scanner still reports what is inside. A raw
    or escaped literal is refused because its source text and its value can
    disagree about where one class token ends and the next begins.
    """
    cut = _unquote(part)
    if cut is None or part.start[0] != part.end[0]:
        return StyleLiteral(
            method, part.start[0], part.start[1], part.end[1], part.string,
            decline="multi-line or triple-quoted literal",
        )  # fmt: skip

    start, stop, text, prefix = cut
    if prefix:
        decline = f"{prefix}-prefixed literal"
    elif "\\" in text:
        decline = "escape sequence in the literal"
    elif concatenated:
        decline = "implicitly concatenated literal"
    else:
        decline = None
    return StyleLiteral(method, part.start[0], start, stop, text, decline=decline)


def _read_fstring(
    tokens: list[tokenize.TokenInfo],
    index: int,
    method: str,
    out: list[StyleLiteral],
) -> int:
    """Collect the literal parts of one f-string; return the index after its end.

    An edge counts as a real end of the string only when the neighbouring token
    is the f-string's own `f"` or `"`. Anywhere else the part abuts an
    interpolation — or the far half of a doubled brace — and a class token
    touching that edge is only part of what actually renders:
    `f"q-mb-md{suffix}"` renders one glued class, not `q-mb-md`.
    """
    depth = 1
    pending: list[int] = []
    while index < len(tokens) and depth:
        token = tokens[index]
        index += 1
        if token.type == tokenize.FSTRING_START:
            depth += 1
        elif token.type == tokenize.FSTRING_END:
            depth -= 1
        elif token.type == tokenize.FSTRING_MIDDLE and depth == 1:
            pending.append(index - 1)
    for at in pending:
        token = tokens[at]
        out.append(
            StyleLiteral(
                method,
                token.start[0],
                token.start[1],
                token.end[1],
                token.string,
                left_edge=tokens[at - 1].type == tokenize.FSTRING_START,
                right_edge=tokens[at + 1].type == tokenize.FSTRING_END,
                decline=(
                    None if token.start[0] == token.end[0] else "multi-line f-string"
                ),
            )
        )
    return index


# --- Fixing --------------------------------------------------------------

_GAPS = re.compile(r"(\s+)")


def _swap(literal: StyleLiteral) -> tuple[str, list[str]]:
    """Rewrite the verified tokens in one literal's text. Whole tokens only."""
    pieces = _GAPS.split(literal.text)
    swaps: list[str] = []
    for i, piece in enumerate(pieces):
        if not piece or _GAPS.fullmatch(piece):
            continue
        if i == 0 and not literal.left_edge:
            continue
        if i == len(pieces) - 1 and not literal.right_edge:
            continue
        replacement = CLASS_TOKEN_SWAPS.get(piece)
        if replacement:
            pieces[i] = replacement
            swaps.append(f"{piece} -> {replacement}")
    return "".join(pieces), swaps


def fix_source(source: str) -> tuple[str, list[tuple[int, str]]]:
    """Apply the verified token swaps. Returns the new source and `(line, swap)`.

    Edits are collected first and applied last-to-first, so no earlier edit can
    invalidate a later position. Nothing outside a string literal is touched, and
    a second run over the result is a no-op.
    """
    edits: list[tuple[int, int, int, str]] = []
    applied: list[tuple[int, str]] = []
    for literal in iter_style_literals(source):
        if literal.method != "classes" or literal.decline:
            continue
        replacement, swaps = _swap(literal)
        if not swaps:
            continue
        edits.append((literal.row, literal.start, literal.end, replacement))
        applied.extend((literal.row, swap) for swap in swaps)

    if not edits:
        return source, []

    lines = _split_lines(source)
    for row, start, end, replacement in sorted(edits, reverse=True):
        line = lines[row - 1]
        lines[row - 1] = line[:start] + replacement + line[end:]
    return "\n".join(lines), sorted(applied)


# --- Scanning ------------------------------------------------------------


def scan_source(source: str, path: Path) -> list[Finding]:
    """Report every convention problem in one file, fixable or not."""
    findings: list[Finding] = []
    for literal in iter_style_literals(source):
        if literal.method == "style":
            for declaration, constant in STYLE_DECLARATION_REPORTS.items():
                if declaration in literal.text:
                    findings.append(
                        Finding(
                            NEEDS_HUMAN,
                            path,
                            literal.row,
                            f"`{declaration}` has a constant",
                            f"Use {constant} from gui.theme and pass it to .style().",
                        )
                    )
            continue

        tokens = literal.text.split()
        for token in tokens:
            if token in QUASAR_KEPT:
                continue
            if token in CLASS_TOKEN_SWAPS:
                findings.append(
                    Finding(
                        FIXABLE,
                        path,
                        literal.row,
                        f"`{token}` -> `{CLASS_TOKEN_SWAPS[token]}`",
                        (
                            f"Declined: {literal.decline}. Apply it by hand."
                            if literal.decline
                            else "Run with --fix."
                        ),
                    )
                )
            elif token in CLASS_TOKEN_REPORTS:
                report = CLASS_TOKEN_REPORTS[token]
                findings.append(
                    Finding(
                        NEEDS_HUMAN,
                        path,
                        literal.row,
                        f"`{token}` is retired",
                        f"{report.why}\nSuggested: {report.suggestion}.",
                    )
                )
            elif _QUASAR_UTILITY.match(token):
                findings.append(
                    Finding(
                        NEEDS_HUMAN,
                        path,
                        literal.row,
                        f"`{token}` is a Quasar utility with no measured equivalent",
                        "Utility classes belong to Tailwind. Measure both classes, "
                        "then add the pair to CLASS_TOKEN_SWAPS — the recipe is in "
                        f"the docstring at the top of {MODULE}.",
                    )
                )
            elif token in CONSTANT_BY_TOKEN and len(tokens) > 1:
                # A literal that is *only* this token is the case below, which
                # names the constant directly rather than pointing at a token.
                findings.append(
                    Finding(
                        CONSIDER,
                        path,
                        literal.row,
                        f"`{token}` is the value of {CONSTANT_BY_TOKEN[token]}",
                        f"Reach it through {CONSTANT_BY_TOKEN[token]} so a palette "
                        "change stays a one-line edit.",
                    )
                )

        constant = CONSTANT_BY_TOKEN_SET.get(frozenset(tokens))
        if constant:
            findings.append(
                Finding(
                    CONSIDER,
                    path,
                    literal.row,
                    f"this literal is {constant}",
                    f"Import {constant} from gui.theme instead.",
                )
            )
    return findings


def scan_repetition(seen: Counter[frozenset[str]], where: dict) -> list[Finding]:
    """Warn about a class string repeated often enough to deserve a constant."""
    findings = []
    for tokens, count in seen.items():
        if count < PROMOTION_THRESHOLD or tokens in CONSTANT_BY_TOKEN_SET:
            continue
        path, line, text = where[tokens]
        findings.append(
            Finding(
                CONSIDER,
                path,
                line,
                f'"{text}" appears {count} times',
                f"At {PROMOTION_THRESHOLD}+ uses this is worth a named constant in "
                "gui/theme.py.",
            )
        )
    return findings


# --- Files ---------------------------------------------------------------

#: Files that legitimately contain what this tool objects to: `theme.py` *defines*
#: the values, and this module *names* them.
EXEMPT = frozenset({"theme.py", "_style_rules.py"})


def in_scope(path: Path) -> bool:
    """Only GUI source. Analyzers and storage may hold such strings as data."""
    parts = path.parts
    return (
        path.suffix == ".py"
        and "gui" in parts[:-1]
        and "tests" not in parts
        and path.name not in EXEMPT
    )


def read_source(path: Path) -> tuple[str, str]:
    """Decode with the file's own encoding, so a coding cookie or BOM survives."""
    raw = path.read_bytes()
    encoding, _ = tokenize.detect_encoding(io.BytesIO(raw).readline)
    return raw.decode(encoding), encoding


def process(paths: Iterable[Path], *, fix: bool) -> tuple[list[Finding], bool]:
    """Check, or fix and then check what is left. Returns findings and whether
    anything was written."""
    findings: list[Finding] = []
    wrote = False
    seen: Counter[frozenset[str]] = Counter()
    where: dict[frozenset[str], tuple[Path, int, str]] = {}

    for path in paths:
        if not in_scope(path):
            continue
        try:
            source, encoding = read_source(path)
            literals = list(iter_style_literals(source))
        except (SyntaxError, UnicodeDecodeError) as error:
            findings.append(Finding(NEEDS_HUMAN, path, 1, f"cannot be read: {error}"))
            continue

        if fix:
            fixed, swaps = fix_source(source)
            if swaps:
                path.write_bytes(fixed.encode(encoding))
                wrote = True
                source = fixed
                findings.extend(
                    Finding(FIXED, path, line, swap) for line, swap in swaps
                )

        findings.extend(scan_source(source, path))
        for literal in literals:
            tokens = frozenset(literal.text.split())
            if literal.method == "classes" and len(tokens) > 1:
                seen[tokens] += 1
                where.setdefault(tokens, (path, literal.row, literal.text.strip()))

    findings.extend(scan_repetition(seen, where))
    return findings, wrote


def default_paths(root: Path) -> list[Path]:
    return sorted(p for p in (root / "gui").rglob("*.py") if in_scope(p))


def main(argv: list[str] | None = None) -> int:
    """Exit 1 when something was fixed or needs a human; 0 for advice alone."""
    parser = argparse.ArgumentParser(
        prog="python -m cibmangotree.gui._style_rules",
        description="Check GUI styling against the convention in " + GUIDE,
    )
    parser.add_argument("paths", nargs="*", type=Path)
    parser.add_argument(
        "--fix", action="store_true", help="apply the verified token swaps in place"
    )
    args = parser.parse_args(argv)

    package = Path(__file__).resolve().parent.parent  # src/cibmangotree
    paths = list(args.paths) or default_paths(package)
    findings, _ = process(paths, fix=args.fix)
    if not findings:
        return 0

    repo = package.parent.parent  # so a printed path starts at src/
    order = {FIXED: 0, NEEDS_HUMAN: 1, FIXABLE: 2, CONSIDER: 3}
    for finding in sorted(
        findings, key=lambda f: (order[f.level], str(f.path), f.line)
    ):
        print(finding.render(repo))

    blocking = [f for f in findings if f.level in BLOCKING]
    print(f"\nThe convention: {GUIDE}")
    print(f"Adding a mapping, and how to check a class: {MODULE}")
    return 1 if blocking else 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
