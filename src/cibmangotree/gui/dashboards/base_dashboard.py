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

from cibmangotree.gui.base import GuiPage
from cibmangotree.gui.routes import gui_routes
from cibmangotree.gui.session import GuiSession


class BaseDashboardPage(GuiPage, abc.ABC):
    """
    Abstract base class for all analyzer dashboard pages.

    Extends GuiPage with dashboard-specific defaults:
    - Back button navigates to the post-analysis page
    - Title is derived from the selected analyzer name
    - Footer is shown

    Subclasses must set _secondary_analyzer_id to enable
    get_output_parquet_path() for loading analysis results.

    Subclasses implement render_content() to provide the actual
    charts, tables, and interactive controls for each analyzer.

    Usage:
        ```python
        class NgramsDashboardPage(BaseDashboardPage):
            _secondary_analyzer_id = ngram_stats_interface.id

            def render_content(self) -> None:
                ui.label("N-grams dashboard content here")
        ```
    """

    _secondary_analyzer_id: str | None = None

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

    def get_output_parquet_path(self, output_id: str) -> str | None:
        """Get path to a secondary output parquet file for the current analysis."""
        analysis = self.session.current_analysis
        if analysis is None or self._secondary_analyzer_id is None:
            return None
        storage = self.session.app.context.storage
        try:
            return storage.get_secondary_output_parquet_path(
                analysis,
                self._secondary_analyzer_id,
                output_id,
            )
        except Exception:
            return None

    def get_primary_output_parquet_path(self, output_id: str) -> str | None:
        """
        Get path to a *primary* output parquet file for the current analysis.

        Dashboards need this to look up columns that a secondary output deliberately
        omits to keep its own file small (see `OutputDeNormalization`).
        """
        analysis = self.session.current_analysis
        if analysis is None:
            return None
        storage = self.session.app.context.storage
        try:
            return storage.get_primary_output_parquet_path(analysis, output_id)
        except Exception:
            return None

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
