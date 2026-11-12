# Styling

GUI styling is standardized: Quasar for widget behavior, typography, and brand
colors; Tailwind for layout, spacing, sizing, and weight. **All class and CSS
style values live in `src/cibmangotree/gui/theme.py`.** GUI modules import and
apply those constants — they must not hard-code style strings.

## Quasar and Tailwind

NiceGUI uses Quasar widgets and supports Tailwind utilities. Utility *names*
belong inside theme constants; pages and components do not inline them.

| Purpose | Use | Examples |
| --- | --- | --- |
| Widget appearance and behavior | Quasar props (allowed inline) | `.props("flat outline")`, `.props("persistent")` |
| Brand and status color *names* | Quasar color args (allowed) | `color="primary"`, `color="mango-orange"` |
| Heading/body typography roles | Quasar classes via theme | `TEXT_HEADING` → `text-h6` |
| Layout, spacing, sizing, borders, shadows | Tailwind via theme | `CARD_CONTENT`, `ROW_ACTIONS` |
| Font size and weight | Tailwind via theme | `TEXT_SM`, `TEXT_BOLD`, `TEXT_WEIGHT_MEDIUM` |

Use Tailwind utilities (inside theme constants) instead of Quasar layout/spacing
utilities such as `q-mb-md` or `q-pa-md`. Keep Quasar's semantic typography and
colors.

## Shared constants

`src/cibmangotree/gui/theme.py` is the single authority for GUI styling:

- Prefer an existing constant.
- If none fits, **add** a role-based constant in `theme.py`, then import it.
- Do not leave class strings, CSS snippets, or brand hex literals in GUI modules.
- Unique layouts still get a theme constant; uniqueness is not a reason for a
  local literal.

Allowed outside `theme.py`: Quasar `.props(...)` and semantic `color="..."`
names. Chart/option hex colors must use theme exports (`MANGO_*`, `CANCEL`,
etc.).

Use names that describe the role: `CARD_*`, `ROW_*`, `COL_*`, `TEXT_*`,
`ICON_*`, and `STYLE_*`. Class constants go to `.classes()`; `STYLE_*`
constants contain raw CSS and go to `.style()`.

```python
from cibmangotree.gui.theme import (
    CARD_CONTENT,
    COL_STEP_BODY,
    STYLE_CENTERED,
    TEXT_MUTED,
)

with ui.column().classes(COL_STEP_BODY).style(STYLE_CENTERED):
    with ui.card().classes(CARD_CONTENT):
        ui.label("No analyses found").classes(TEXT_MUTED)
```

Compose related constants so their common styles stay synchronized:

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
`GUARDED_PATHS`. It rejects string and f-string arguments to `.classes()` and
`.style()` (use theme constants instead) and flags retired Quasar/layout tokens.
Widen `GUARDED_PATHS` and the hook `files` pattern together when migrating more
modules. Install and run hooks via
[Installation](../get-started/installation.md).
