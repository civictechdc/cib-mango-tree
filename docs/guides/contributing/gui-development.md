# GUI development

The CIB Mango Tree UI is a [NiceGUI](https://nicegui.io/documentation) app under
`src/cibmangotree/gui/`. This guide covers how we structure pages and how to add
or change them.

**Reading order:** [Installation](../get-started/installation.md) → this guide →
[Styling](./styling.md) → [Analyzers](./analyzers.md) (for results dashboards).
For run/build commands and session-flow diagrams, see the
[GUI module README](https://github.com/civictechdc/cib-mango-tree/blob/main/src/cibmangotree/gui/README.md).

## How we use NiceGUI

NiceGUI renders Quasar/Vue widgets from Python. On a normal desktop install the
app opens as a native window; in GitHub Codespaces it serves in the browser
(see [Installation](../get-started/installation.md)).

- **Routes:** each screen is an `@ui.page` handler registered in
  `register_pages()` in `main_workflow.py`. Path strings live on `gui_routes` in
  `routes.py`.
- **Pages:** every screen subclasses `GuiPage` (`base.py`). `render()` runs the
  template method: set Quasar colors → header → `render_content()` → footer.
  Subclasses only implement `render_content()`.
- **Session:** a shared `GuiSession` (Pydantic) holds project, import, and
  analysis state for the running UI.
- **Theme:** presentation values live in `theme.py`. Follow [Styling](./styling.md).

!!! warning "Common footguns"

    - Quasar `color=` needs a **named slot** (`"primary"`, `"negative"`, …), not
      a hex or `gui_colors.*` value. Details in [Styling](./styling.md).
    - Do not hardcode route path strings. Use `gui_routes.*` and
      `self.navigate_to(...)`.

!!! tip "NiceGUI docs for AI / MCP tooling"

    NiceGUI publishes a condensed LLM reference at
    [https://nicegui.io/llms.txt](https://nicegui.io/llms.txt) (also shipped in
    the installed package as `nicegui/llms.md`). Docs MCP servers and similar
    tooling often start from that file.

    Cursor is only one example of a MCP-capable environment. A minimal Cursor
    config using the hosted NiceGUI docs MCP looks like this (place it in
    `~/.cursor/mcp.json` or your project MCP settings). You may need to adjust
    the setup for your IDE, transport, or local vs hosted docs:

    ```json
    {
      "mcpServers": {
        "nicegui Docs": {
          "url": "https://gitmcp.io/zauberzeug/nicegui"
        }
      }
    }
    ```

    If you use AI tools while contributing, follow the project
    [AI Use Policy](https://github.com/civictechdc/cib-mango-tree/blob/main/AI_POLICY.md).

## Code organization

**Where does this code go?** New screen → `pages/`. Reusable widget →
`components/`. Analyzer results UI → `dashboards/` (see
[NiceGUI dashboards](./analyzers.md#nicegui-dashboards)). Presentation values →
`theme.py` / [Styling](./styling.md).

```text
src/cibmangotree/gui/
├── base.py
├── main_workflow.py
├── session.py
├── routes.py
├── theme.py
├── context.py
├── pages/
│   └── analysis_workflow/
├── components/
│   └── upload/
├── dashboards/
│   ├── base_dashboard.py
│   ├── hashtags/
│   ├── ngrams/
│   ├── time_coordination/
│   └── placeholder/
├── icons/
└── tests/
```

- **Root modules:** `GuiPage` shell, `register_pages` / `ui.run`, session,
  routes, theme SSOT, and `GUIContext`.
- **`pages/`:** route-level `GuiPage` subclasses. Stepper UI for configure/run
  lives under `pages/analysis_workflow/`.
- **`components/`:** reusable NiceGUI pieces; custom Vue (Vite) lives under
  `components/upload/`.
- **`dashboards/`:** `BaseDashboardPage` plus per-analyzer packages registered
  by primary analyzer id.
- **`tests/`:** component, dashboard, stepper, and e2e coverage.

API dump: [GUI reference](../../reference/gui.md).

## Basic component examples

Common building blocks: `ui.label`, `ui.button`, `ui.column`, `ui.row`,
`centered_content()`, and `notify_success` / `notify_warning` / `notify_error`
on `GuiPage`.

Study production patterns in `pages/start.py` or `pages/importer.py`. The
sample below is a minimal sketch only.

### Add a page checklist

1. Add the path on `GuiRoutes` in `routes.py`.
2. Subclass `GuiPage` under `pages/` and implement `render_content()`.
3. Register `@ui.page(...)` in `register_pages()` (`main_workflow.py`) using the
   shared `gui_session`.
4. Put classes, props, and colors in `theme.py` (see [Styling](./styling.md));
   respect the `gui-styles` pre-commit hook.
5. Optional: add a test under `gui/tests/` (see [Testing](#testing)).

### Minimal example

```python
from nicegui import ui

from cibmangotree.gui.base import GuiPage
from cibmangotree.gui.routes import gui_routes
from cibmangotree.gui.session import GuiSession


class MyPage(GuiPage):
    def __init__(self, session: GuiSession):
        super().__init__(
            session=session,
            route="/my_page",
            title="My Page",
            show_back_button=True,
            back_route=gui_routes.root,
        )

    def render_content(self) -> None:
        with self.centered_content():
            ui.label("Hello, CIB Mango Tree!")
            ui.button(
                "Go Home",
                on_click=lambda: self.navigate_to(gui_routes.root),
            )


# In register_pages() (main_workflow.py), after adding the path to GuiRoutes:
# @ui.page(gui_routes.my_page)  # once defined on GuiRoutes
# def my_page():
#     MyPage(session=gui_session).render()
```

## Dashboard development

Results dashboards subclass `BaseDashboardPage` and register by **primary
analyzer id** in `dashboards/__init__.py`. Recipe and registration details:
[NiceGUI dashboards](./analyzers.md#nicegui-dashboards).

## Testing

GUI tests live under `src/cibmangotree/gui/tests/` (components, dashboard,
stepper, e2e). How to run the project test suite:
[Testing](./testing.md).

## See also

- [Styling](./styling.md)
- [Analyzers](./analyzers.md) (NiceGUI dashboards)
- [Testing](./testing.md)
- [Installation](../get-started/installation.md) (docs preview with Zensical)
- [GUI module README](https://github.com/civictechdc/cib-mango-tree/blob/main/src/cibmangotree/gui/README.md)
- [GUI API reference](../../reference/gui.md)
- [NiceGUI documentation](https://nicegui.io/documentation)
- [NiceGUI `llms.txt`](https://nicegui.io/llms.txt)
- [AI Use Policy](https://github.com/civictechdc/cib-mango-tree/blob/main/AI_POLICY.md)
