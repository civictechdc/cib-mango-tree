# Styling

Shared styles live in `src/cibmangotree/gui/theme.py`. Reuse an existing semantic
constant before adding another class string or CSS preset.

## Quasar and Tailwind

NiceGUI uses Quasar widgets and supports Tailwind utilities:

| Purpose | Use | Examples |
| --- | --- | --- |
| Widget appearance and behavior | Quasar props | `.props("flat outline")`, `.props("persistent")` |
| Heading/body typography roles | Quasar | `text-h6`, `text-body2`, `text-caption` |
| Brand and status colors | Quasar | `color="primary"`, `text-negative` |
| Layout, spacing, sizing, borders, shadows | Tailwind | `items-center`, `mb-4`, `w-full`, `shadow-none` |
| Font size and weight | Tailwind | `text-sm`, `font-bold`, `font-medium` |
| Repeated semantic styles | Shared constants | `CARD_CONTENT`, `ROW_CENTERED`, `TEXT_MUTED` |

Use Tailwind utilities instead of Quasar layout/spacing utilities such as
`q-mb-md` or `q-pa-md`. Keep Quasar's semantic typography and colors.

## Shared constants

Use names that describe the role: `CARD_*`, `ROW_*`, `COL_*`, `TEXT_*`,
`ICON_*`, and `STYLE_*`. Class constants go to `.classes()`; `STYLE_*`
constants contain raw CSS and go to `.style()`.

```python
from cibmangotree.gui.theme import CARD_CONTENT, STYLE_CENTERED, TEXT_MUTED

with ui.column().classes("w-full items-center gap-6").style(STYLE_CENTERED):
    with ui.card().classes(CARD_CONTENT):
        ui.label("No analyses found").classes(TEXT_MUTED)
```

Keep one-off Tailwind utilities local. Add a shared constant when it represents
a reusable semantic role or the pattern appears in at least three places.
Compose related constants so their common styles stay synchronized:

```python
CARD_FLAT = "shadow-none border border-gray-200"
CARD_CONTENT = f"w-full p-4 {CARD_FLAT}"
CARD_PARAM = f"w-72 p-4 {CARD_FLAT}"
```

Keep class ordering consistent: layout, sizing, spacing, typography, then color.

`TEXT_MUTED` uses `text-grey-8`; info icons use `ICON_INFO`, whose class string
includes `text-grey-7`. Select the constant by the element's role.

## Initial rollout

The convention currently applies to two pilot modules:

- `gui/pages/analysis_workflow/run_step.py`
- `gui/components/analysis.py`

Other GUI modules still use their existing styles and will migrate in separate
PRs. Reusable layout helpers and loading/empty-state components are follow-up
work under issue [#399](https://github.com/civictechdc/cib-mango-tree/issues/399).

The local `gui-styles` hook checks direct string and f-string arguments to
`.classes()` for known retired tokens and `.style()` for existing CSS presets.
It prints the file, line, and suggested replacement. It never modifies files.
Variable values and arbitrary Python expressions are not evaluated.

The guarded modules are listed in `GUARDED_PATHS` in `gui/_style_rules.py`.
When a module is migrated, add it there and widen the hook's `files` pattern
in `.pre-commit-config.yaml`. A test checks that the two scopes match.

## Installing and running hooks

Install the Git hooks once per clone:

```bash
uv run pre-commit install
```

This includes the local `gui-styles` hook. If the Git hooks are already installed,
they pick up changes to `.pre-commit-config.yaml` automatically.

Hooks run during `git commit`, before the commit is created, and check matching
staged files. They do not run on `git push`. If the hooks pass during commits,
you do not need to rerun them manually before opening a PR.

You can also run the hooks manually to check all files they cover, including unchanged files. This is optional:

```bash
uv run pre-commit run --all-files
```

Formatting hooks may modify files; review their changes and rerun the checks.
The styling hook reports violations for a contributor to fix by hand.

## Testing before opening a PR

The hooks do not run the test suite. Run it separately before opening a PR:

```bash
uv run pytest
```
