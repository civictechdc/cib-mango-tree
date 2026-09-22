# Styling

This document is the reference guide for contributors working on the application's frontend.

It defines the styling conventions we currently follow and should be updated as the frontend architecture evolves.

## Principles

### One source of truth for shared styles

Shared style constants and brand colours live in [`gui/theme.py`][theme].

If a shared constant already exists, import and reuse it instead of repeating the same class string, CSS value, or colour.

### Quasar for widgets, Tailwind for customization

The UI is built with [NiceGUI](https://nicegui.io/), which uses Quasar components and supports Tailwind utility classes.

The general rule is:

> **Quasar owns components and their semantic behavior. Tailwind owns layout and visual customization.**

## Quasar vs. Tailwind

|                       | **Quasar**                                                              | **Tailwind**                                                          |
| --------------------- | ----------------------------------------------------------------------- | --------------------------------------------------------------------- |
| **What is it?**       | UI component framework used by NiceGUI                                  | Utility-first CSS framework                                           |
| **Use it for**        | Widgets, widget props, typography scale, brand/status colours           | Layout, spacing, sizing, borders, shadows, font size, and font weight |
| **Looks like**        | `.props("flat outline")`, `color="primary"`, `text-h6`, `text-negative` | `mb-4`, `w-full`, `p-4`, `gap-2`, `shadow-none`, `font-bold`          |
| **Do not use it for** | Layout or spacing such as `q-mb-md`, `q-pa-md`, or `no-shadow`          | Quasar typography roles or semantic brand/status colours              |
| **Example**           | `ui.button("Save", color="primary").props("flat no-caps")`              | `ui.card().classes("w-full p-4 shadow-none")`                         |

### Quick lookup

| If you are setting…             | Use                 | Example                                          |
| ------------------------------- | ------------------- | ------------------------------------------------ |
| Margin or padding               | Tailwind            | `mb-4`, `mt-2`, `p-4`                            |
| Width or height                 | Tailwind            | `w-full`, `w-72`                                 |
| Flex layout, alignment, or gaps | Tailwind            | `items-center`, `justify-end`, `gap-2`           |
| Borders or shadows              | Tailwind            | `border border-gray-200`, `shadow-none`          |
| Font size or weight             | Tailwind            | `text-sm`, `text-lg`, `font-bold`, `font-medium` |
| Heading/body typography role    | Quasar              | `text-h6`, `text-body2`, `text-caption`          |
| Brand or status colour          | Quasar              | `color="primary"`, `text-negative`               |
| Muted or secondary text         | Shared constant     | `TEXT_MUTED`                                     |
| Widget appearance or behavior   | Quasar props        | `.props("flat outline")`, `.props("persistent")` |
| A repeated semantic style       | `theme.py` constant | `CARD_CONTENT`, `ROW_ACTIONS`                    |

## Style constants

Reusable styles are stored as constants in [`gui/theme.py`][theme].

A style constant is simply a named Python string:

```python
TEXT_MUTED = "text-grey-8"
```

Instead of repeating the literal throughout the application:

```python
ui.label("No analyses found").classes("text-grey-8")
```

import and reuse the constant:

```python
from cibmangotree.gui.theme import TEXT_MUTED

ui.label("No analyses found").classes(TEXT_MUTED)
```

This keeps styling consistent and allows a shared style to be changed in one place.

### Where to define constants

All shared UI style constants should live in:

```text
src/cibmangotree/gui/theme.py
```

Local Tailwind classes are still fine for styles that are only used once.

### Naming

Use the prefix to describe the element or semantic role:

* `CARD_*` — cards
* `ROW_*` — rows
* `COL_*` — columns
* `TEXT_*` — text
* `ICON_*` — icons
* `STYLE_*` — raw CSS passed to `.style()`

For example:

```python
CARD_FLAT = "shadow-none border border-gray-200"
TEXT_MUTED = "text-grey-8"
STYLE_CENTERED = "max-width: 960px; margin: 0 auto;"
```

### `.classes()` vs. `.style()`

Constants beginning with `STYLE_*` contain raw CSS and must be passed to `.style()`.

Other styling constants contain classes and should be passed to `.classes()`.

```python
ui.label("Status").classes(TEXT_MUTED)
ui.column().style(STYLE_CENTERED)
```

Do not mix them:

```python
# Correct
element.classes(TEXT_MUTED)
element.style(STYLE_CENTERED)

# Incorrect
element.classes(STYLE_CENTERED)
element.style(TEXT_MUTED)
```

### When to add a constant

Before adding a new constant, check whether an existing semantic constant already represents the same purpose.

A local Tailwind literal is fine for a one-off:

```python
ui.row().classes("gap-2")
```

Add a shared constant when:

* the style represents a reusable semantic role, or
* the same pattern appears in **3 or more places**.

For example:

```python
CARD_CONTENT = "w-full p-4 shadow-none border border-gray-200"
```

rather than repeating the same card styling across multiple files.

> `gui/theme.py` should be a shared styling vocabulary, not a registry of every class string in the application.

### Compose instead of duplicate

Build related constants from existing constants where appropriate:

```python
CARD_FLAT = "shadow-none border border-gray-200"
CARD_CONTENT = CARD_FLAT + " w-full p-4"
```

This keeps related styles synchronized.

### Class ordering

Keep utility classes in a consistent order:

```text
layout → sizing → spacing → typography → colour
```

Prefer:

```python
"flex w-full gap-4 text-sm text-grey-8"
```

over:

```python
"text-grey-8 gap-4 w-full flex text-sm"
```

Both may produce the same result, but consistent ordering makes duplicate and near-duplicate patterns easier to identify.


## Before opening a PR

Run the formatting and lint checks:

```bash
uv run pre-commit run --all-files
```

Some hooks automatically modify files and then exit with a non-zero status.

If this happens, review the changes, stage them, and run the command again:

```bash
git add -u
uv run pre-commit run --all-files
```

Repeat until all checks pass.

Then run the test suite:

```bash
uv run pytest
```

`src/cibmangotree/gui/tests/test_styles.py` checks `.classes()` and `.style()` usage and reports retired styling patterns together with their expected replacements.

[theme]: https://github.com/civictechdc/cib-mango-tree/blob/main/src/cibmangotree/gui/theme.py
[rules]: https://github.com/civictechdc/cib-mango-tree/blob/main/src/cibmangotree/gui/_style_rules.py
