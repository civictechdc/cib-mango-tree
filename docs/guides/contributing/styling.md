# Styling

**Set every GUI presentation value in `src/cibmangotree/gui/theme.py`.**

Pages, components, and dashboards must not invent class strings, CSS snippets,
Quasar `.props()` literals, or brand hexes locally. Define (or reuse) a named
constant in `theme.py`, then import and apply it.

No: hard-code class/style/props at the call site.

```python
ui.button("Save", color="primary").classes("w-full mb-4")
ui.label("Hint").style("max-width: 960px; margin: 0 auto;")
```

Yes: those live in `theme.py`; Quasar `color=` uses a slot name (see below).

```python
from cibmangotree.gui.theme import STYLE_CENTERED, WIDTH_FULL_MB_4

ui.button("Save", color="primary").classes(WIDTH_FULL_MB_4)
ui.label("Hint").style(STYLE_CENTERED)
```

If the value you need is missing, **add it to `theme.py` first**, then use it.

Do not “just this once” inline a Tailwind class, Quasar prop, or hex in a GUI
module.

## Quasar color slots (read this)

Quasar widgets (`ui.button`, `ui.icon`, `ui.notify`, …) expect a **named color
slot** on `color=`, not a raw hex.

`GuiPage._setup_colors()` calls `ui.colors(...)` once per page to override
Quasar’s default slots with our `gui_colors` hexes (and to register custom
names like `cancel` / `brand-progress`). After that:

```python
ui.button("Save", color="primary")  # looks up the slot → brand paint + light text
```

**Footgun:** passing a hex (or `gui_colors.brand_primary`) to `color=` sets the
background only. Quasar does not treat that as a named slot, so labels/icons
often stay **black** on a dark button.

```python
# Wrong — hex bypasses Quasar slot styling
ui.button("Save", color=gui_colors.brand_primary)

# Right — slot name registered in _setup_colors
ui.button("Save", color="primary")
```

Use `gui_colors.*` hexes for charts, CSS, and other places that need a raw color
value — not for Quasar `color=` on buttons/icons/notifies.

Built-in slots we override: `primary`, `secondary`, `accent`, `dark`,
`positive`, `negative`, `warning`, `info`. Custom slots we register: `cancel`,
`brand-progress`. Palette names like `grey` / `red` work without registration.

## Quasar and Tailwind

NiceGUI uses Quasar widgets and supports Tailwind utilities. Utility *names*
and Quasar presentation flags belong inside theme constants; pages and
components do not inline them.

| Purpose                                   | Use                      | Examples                                          |
| ----------------------------------------- | ------------------------ | ------------------------------------------------- |
| Widget chrome / Quasar props              | Theme `gui_props`        | `.props(gui_props.flat)`, `.props(gui_props.outline)`     |
| Quasar `color=` on buttons/icons/notifies | Slot name strings        | `color="primary"`, `color="negative"`, `color="cancel"` |
| Charts / raw CSS hex                      | Theme `gui_colors`       | `gui_colors.brand_progress`, `gui_colors.chart_highlight` |
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
- Do not leave class strings, CSS snippets, Quasar `.props()` string literals,
  or brand hex literals in GUI modules.
- Unique layouts still get a theme constant; uniqueness is not a reason for a
  local literal.

Hex palette values live on `GuiColors` (`gui_colors`) and are registered onto
Quasar slots in `_setup_colors` (see **Quasar color slots** above).

Use names that describe the role: `gui_colors.*`, `CARD_*`, `ROW_*`, `COL_*`,
`TEXT_*`, `ICON_*`, and `STYLE_*`. Class constants go to `.classes()`; `STYLE_*`
constants contain raw CSS and go to `.style()`; Quasar presentation flags go
through `gui_props` to `.props()`; Quasar widget `color=` uses slot name
strings.

```python
from cibmangotree.gui.theme import (
    CARD_CONTENT,
    COL_STEP_BODY,
    STYLE_CENTERED,
    TEXT_MUTED,
    gui_props,
)

with ui.column().classes(COL_STEP_BODY).style(STYLE_CENTERED):
    with ui.card().classes(CARD_CONTENT):
        ui.label("No analyses found").classes(TEXT_MUTED)
    ui.button("Continue", color="primary").props(gui_props.outline)
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
`.style()`, and `.props()`. Quasar `color=` slot name strings are allowed.
It also flags retired Quasar/layout tokens in class literals. Widen
`FILES_TO_CHECK` and the hook `files` pattern together when migrating more
modules (drift is caught by `test_hook_covers_exactly_the_files_to_check` in
`gui/tests/test_styles.py`). Install and run hooks via
[Installation](../get-started/installation.md).
