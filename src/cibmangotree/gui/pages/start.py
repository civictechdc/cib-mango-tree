from nicegui import ui

from cibmangotree.gui.base import GuiPage
from cibmangotree.gui.routes import gui_routes
from cibmangotree.gui.session import GuiSession


class StartPage(GuiPage):
    """
    Main/home page of the application.

    Displays welcome message and primary navigation buttons for
    creating a new project or viewing existing projects.
    """

    def __init__(self, session: GuiSession):
        super().__init__(
            session=session,
            route="/",
            title="CIB Mango Tree",
            show_back_button=False,  # Home page - no back navigation
            show_footer=True,
        )

    def render_content(self) -> None:
        """Render main page content with action buttons."""
        # Main content area - centered vertically
        with self.centered_content():
            # Hero logo
            ui.html(self._load_svg_icon("cibmt_logo"), sanitize=False).classes(
                "size-36 q-mb-xl"
            )

            # Action buttons row
            with ui.row().classes("gap-4"):
                ui.button(
                    "New Project",
                    on_click=lambda: self.navigate_to(gui_routes.new_project),
                    icon="add",
                    color="primary",
                )

                ui.button(
                    "Show Existing Projects",
                    on_click=lambda: self.navigate_to(gui_routes.select_project),
                    icon="folder",
                    color="primary",
                )
