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
from collections.abc import Callable
from typing import TYPE_CHECKING

from nicegui import run, ui

from gui.base import GuiPage
from gui.routes import gui_routes
from gui.session import GuiSession

if TYPE_CHECKING:
    import polars as pl


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

    async def load_parquet_async(
        self,
        output_id: str,
        on_success: Callable[["pl.DataFrame"], None],
        loading_container: ui.column | None = None,
        content_container: ui.column | None = None,
    ) -> None:
        """
        Load a parquet file asynchronously with loading/error handling.

        Args:
            output_id: Secondary output identifier to locate the parquet file.
            on_success: Callback invoked with the loaded DataFrame on success.
            loading_container: Container to show error in if loading fails.
            content_container: Paired content container to reveal on success.
        """
        import polars as pl

        path = self.get_output_parquet_path(output_id)
        if path is None:
            if loading_container is not None:
                self._show_error(loading_container, "No analysis data found.")
            return
        try:
            df = await run.io_bound(pl.read_parquet, path)
            if df.is_empty():
                if loading_container is not None:
                    self._show_error(loading_container, "No data available.")
                return
            on_success(df)
            if loading_container is not None and content_container is not None:
                self._show_content(loading_container, content_container)
        except Exception as exc:
            if loading_container is not None:
                self._show_error(loading_container, f"Could not load data: {exc}")

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
