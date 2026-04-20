"""
Base class for all analyzer dashboard pages.

Provides a standard layout shell for dashboards:
- Header inherited from GuiPage (with back-to-results navigation)
- A full-width content area for charts and tables
- Footer inherited from GuiPage

All analyzer-specific dashboard pages should subclass BaseDashboardPage
and implement render_content().
"""

import abc

from nicegui import ui

from gui.base import GuiPage
from gui.routes import gui_routes
from gui.session import GuiSession


class BaseDashboardPage(GuiPage, abc.ABC):
    """
    Abstract base class for all analyzer dashboard pages.

    Extends GuiPage with dashboard-specific defaults:
    - Back button navigates to the post-analysis page
    - Title is derived from the selected analyzer name
    - Footer is shown

    Subclasses implement render_content() to provide the actual
    charts, tables, and interactive controls for each analyzer.

    Usage:
        ```python
        class NgramsDashboardPage(BaseDashboardPage):
            def render_content(self) -> None:
                ui.label("N-grams dashboard content here")
        ```
    """

    def __init__(self, session: GuiSession):
        analyzer_name = (
            session.selected_analyzer_name
            if session.selected_analyzer_name
            else "Results Dashboard"
        )
        super().__init__(
            session=session,
            route=gui_routes.dashboard,
            title=f"{analyzer_name}: Results Dashboard",
            show_back_button=True,
            back_route=gui_routes.post_analysis,
            show_footer=True,
        )

    def _create_loading_container(
        self, height: str = "500px"
    ) -> tuple[ui.column, ui.column]:
        """
        Create a loading spinner container and a (hidden) content container.

        Subclasses call this inside render_content() and later call
        _show_content() / _show_error() to switch states.

        Returns:
            (loading_container, content_container)
        """
        loading_container = (
            ui.column()
            .classes("w-full items-center justify-center")
            .style(f"height: {height};")
        )
        with loading_container:
            ui.spinner("pie", size="xl")
            ui.label("Loading dashboard...").classes("text-grey-6 q-mt-md")

        content_container = (
            ui.column().classes("w-full").style(f"height: {height}; display: none;")
        )

        return loading_container, content_container

    def _show_content(self, loading_container: ui.column, content_container: ui.column):
        """Switch from loading state to content display."""
        loading_container.style("display: none;")
        content_container.style("display: block;")

    def _show_error(
        self,
        loading_container: ui.column,
        message: str,
    ) -> None:
        """Replace loading spinner with an error message in-place."""
        loading_container.clear()
        with loading_container:
            ui.icon("error_outline", size="3rem").classes("text-negative")
            ui.label(message).classes("text-negative q-mt-md")

    @abc.abstractmethod
    def render_content(self) -> None:
        """Render dashboard-specific charts, tables, and controls."""
        raise NotImplementedError
