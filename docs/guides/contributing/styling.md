# Styling

**Set every GUI presentation value in `src/cibmangotree/gui/theme.py`.**

Pages, components, and dashboards must not invent class strings, CSS snippets,
Quasar `color=` / `.props()` literals, or brand hexes locally. Define (or reuse)
a named constant in `theme.py`, then import and apply it.

No: hard-code at the call site.

```python
ui.button("Save", color="primary").classes("w-full mb-4")
ui.label("Hint").style("max-width: 960px; margin: 0 auto;")
```

Yes: constants live in `theme.py`; call sites only name them.

```python
from cibmangotree.gui.theme import COLOR_PRIMARY, STYLE_CENTERED, WIDTH_FULL_MB_4

ui.button("Save", color=COLOR_PRIMARY).classes(WIDTH_FULL_MB_4)
ui.label("Hint").style(STYLE_CENTERED)
```

If the value you need is missing, **add it to `theme.py` first**, then use it.

Do not “just this once” inline a Tailwind class, Quasar prop, or hex in a GUI
module.

## Quasar and Tailwind

NiceGUI uses Quasar widgets and supports Tailwind utilities. Utility *names*
and Quasar presentation flags belong inside theme constants; pages and
components do not inline them.

| Purpose                                   | Use                      | Examples                                          |
| ----------------------------------------- | ------------------------ | ------------------------------------------------- |
| Widget chrome / Quasar props              | Theme `PROPS_*`          | `.props(PROPS_FLAT)`, `.props(PROPS_OUTLINE)`     |
| Brand and status color roles              | Theme `COLOR_*`          | `color=COLOR_PRIMARY`, `color=COLOR_MANGO_ORANGE` |
| Heading/body typography roles             | Quasar classes via theme | `TEXT_HEADING` → `text-h6`                        |
| Layout, spacing, sizing, borders, shadows | Tailwind via theme       | `CARD_CONTENT`, `ROW_ACTIONS`                     |
| Font size and weight                      | Tailwind via theme       | `TEXT_SM`, `TEXT_BOLD`, `TEXT_WEIGHT_MEDIUM`      |

Use Tailwind utilities (inside theme constants) instead of Quasar layout/spacing
utilities such as `q-mb-md` or `q-pa-md`. Keep Quasar's semantic typography and
colors.

## Shared constants

`theme.py` is the single authority for GUI styling:

- Prefer an existing constant.
- If none fits, **add** a role-based constant in `theme.py`, then import it.
- Do not leave class strings, CSS snippets, Quasar `color=` / `.props()` string
  literals, or brand hex literals in GUI modules.
- Unique layouts still get a theme constant; uniqueness is not a reason for a
  local literal.

Hex palette values are registered once via `GuiPage._setup_colors()` /
`ui.colors(...)`. Call sites use `COLOR_*` role names, not hexes (except where
charts need a theme hex export such as `MANGO_ORANGE`).

Use names that describe the role: `COLOR_*`, `PROPS_*`, `CARD_*`, `ROW_*`,
`COL_*`, `TEXT_*`, `ICON_*`, and `STYLE_*`. Class constants go to `.classes()`;
`STYLE_*` constants contain raw CSS and go to `.style()`; `PROPS_*` go to
`.props()`; `COLOR_*` go to `color=`.

```python
from cibmangotree.gui.theme import (
    CARD_CONTENT,
    COLOR_PRIMARY,
    COL_STEP_BODY,
    PROPS_OUTLINE,
    STYLE_CENTERED,
    TEXT_MUTED,
)

with ui.column().classes(COL_STEP_BODY).style(STYLE_CENTERED):
    with ui.card().classes(CARD_CONTENT):
        ui.label("No analyses found").classes(TEXT_MUTED)
    ui.button("Continue", color=COLOR_PRIMARY).props(PROPS_OUTLINE)
```

Compose related constants in `theme.py` so their common styles stay
synchronized:

```python
CARD_FLAT = "shadow-none border border-gray-200"
CARD_CONTENT = f"w-full p-4 {CARD_FLAT}"
CARD_PARAM = f"w-72 p-4 {CARD_FLAT}"
```

Keep class ordering consistent: layout, sizing, spacing, typography, then color.

`TEXT_MUTED` uses `text-grey-8`; info icons use `ICON_INFO`, whose class string
includes `text-grey-7`. Select the constant by the element's role.

## Enforcement

The `gui-styles` pre-commit hook runs `gui/_style_rules.py` on modules listed in
`FILES_TO_CHECK`. It rejects string and f-string arguments to `.classes()`,
`.style()`, and `.props()`, and string literals on `color=` (use theme
constants instead). It also flags retired Quasar/layout tokens in class
literals. Widen `FILES_TO_CHECK` and the hook `files` pattern together when
migrating more modules (drift is caught by
`test_hook_covers_exactly_the_files_to_check` in `gui/tests/test_styles.py`).
Install and run hooks via [Installation](../get-started/installation.md).
