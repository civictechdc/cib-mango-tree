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

The `gui-styles` pre-commit hook enforces retired tokens on modules listed in
`GUARDED_PATHS` (`gui/_style_rules.py`). Install and run hooks via
[Installation](../get-started/installation.md).
