"""
N-grams results dashboard page.

Displays an interactive scatter plot of n-gram frequency vs. unique poster
count, loaded from the ``ngram_stats`` secondary analyzer output. Clicking
a point filters the data grid to show all occurrences of that n-gram.
"""

import polars as pl
from nicegui import run, ui

from analyzers.ngrams.ngrams_stats.interface import (
    COL_AUTHOR_ID,
    COL_MESSAGE_TEXT,
    COL_MESSAGE_TIMESTAMP,
    COL_NGRAM_DISTINCT_POSTER_COUNT,
    COL_NGRAM_TOTAL_REPS,
    COL_NGRAM_WORDS,
    OUTPUT_NGRAM_FULL,
    OUTPUT_NGRAM_STATS,
)
from analyzers.ngrams.ngrams_stats.interface import interface as ngram_stats_interface
from analyzers.ngrams.ngrams_web.plots import plot_scatter_echart
from gui.base import GuiSession

from .base_dashboard import BaseDashboardPage

# Highlight marker color for selected points
HIGHLIGHT_COLOR = "#d62728"  # Red
HIGHLIGHT_SERIES_NAME = "__highlight__"


class NgramsDashboardPage(BaseDashboardPage):
    """
    Results dashboard for the N-grams (Copy-Pasta Detector) analyzer.

    Renders a log-log scatter plot of n-gram frequency versus unique poster
    count.  Each point represents one n-gram; points are coloured by n-gram
    length.

    Interactive features:
    - Click a point to highlight it and filter the data grid to show all
      occurrences of that n-gram
    - Click the same point again to deselect and return to summary view
    - Click a different point to switch selection
    """

    def __init__(self, session: GuiSession):
        super().__init__(session=session)
        # State for tracking selection
        self._selected_words: str | None = None
        self._selected_point_coords: tuple[float, float] | None = None
        # DataFrames
        self._df_stats: pl.DataFrame | None = None
        self._df_full: pl.DataFrame | None = None
        # UI component references (set during render)
        self._chart: ui.echart | None = None
        self._grid: ui.aggrid | None = None
        self._info_label: ui.label | None = None

    def _get_parquet_path(self, output_id: str) -> str | None:
        """
        Get the path to a secondary output parquet file.

        Args:
            output_id: The output identifier (OUTPUT_NGRAM_STATS or OUTPUT_NGRAM_FULL)

        Returns:
            Path string or None if the analysis or its output files are missing.
        """
        analysis = self.session.current_analysis
        if analysis is None:
            return None

        storage = self.session.app.context.storage
        try:
            return storage.get_secondary_output_parquet_path(
                analysis,
                ngram_stats_interface.id,
                output_id,
            )
        except Exception:
            return None

    def _get_top_n_summary(self, n: int = 100) -> pl.DataFrame:
        """
        Get top N n-grams by frequency for the summary view.

        Args:
            n: Number of top n-grams to return (default 100)

        Returns:
            DataFrame with summary columns, sorted by total_reps descending
        """
        if self._df_stats is None or self._df_stats.is_empty():
            return pl.DataFrame()

        return (
            self._df_stats.select(
                [
                    COL_NGRAM_WORDS,
                    COL_NGRAM_TOTAL_REPS,
                    COL_NGRAM_DISTINCT_POSTER_COUNT,
                ]
            )
            .sort(COL_NGRAM_TOTAL_REPS, descending=True)
            .head(n)
            .rename(
                {
                    COL_NGRAM_WORDS: "N-gram content",
                    COL_NGRAM_TOTAL_REPS: "Total repetitions",
                    COL_NGRAM_DISTINCT_POSTER_COUNT: "Unique posters",
                }
            )
        )

    def _get_filtered_full_data(self, words: str) -> pl.DataFrame:
        """
        Get all occurrences of a specific n-gram from the full report.

        Args:
            words: The n-gram words string to filter by

        Returns:
            DataFrame with detail columns for the selected n-gram
        """
        if self._df_full is None or self._df_full.is_empty():
            return pl.DataFrame()

        return (
            self._df_full.filter(pl.col(COL_NGRAM_WORDS) == words)
            .select(
                [
                    COL_AUTHOR_ID,
                    COL_NGRAM_WORDS,
                    COL_MESSAGE_TEXT,
                    COL_MESSAGE_TIMESTAMP,
                ]
            )
            .with_columns(
                pl.col(COL_MESSAGE_TIMESTAMP).dt.strftime("%B %d, %Y %I:%M %p")
            )
            .rename(
                {
                    COL_AUTHOR_ID: "User ID",
                    COL_NGRAM_WORDS: "N-gram content",
                    COL_MESSAGE_TEXT: "Post content",
                    COL_MESSAGE_TIMESTAMP: "Timestamp",
                }
            )
        )

    def _update_info_label(self) -> None:
        """Update the info label based on current selection state."""
        if self._info_label is None:
            return

        if self._selected_words is None:
            self._info_label.text = (
                "Showing top 100 n-grams by frequency. "
                "Click a point on the scatter plot to view all occurrences."
            )
        else:
            # Get count for selected n-gram
            if self._df_full is not None:
                count = self._df_full.filter(
                    pl.col(COL_NGRAM_WORDS) == self._selected_words
                ).height
            else:
                count = 0
            self._info_label.text = (
                f"N-gram: '{self._selected_words}' — {count:,} total repetitions"
            )

    def _update_grid(self) -> None:
        """Update the data grid based on current selection state."""
        if self._grid is None:
            return

        if self._selected_words is None:
            # Show summary view
            df_display = self._get_top_n_summary()
        else:
            # Show filtered detail view
            df_display = self._get_filtered_full_data(self._selected_words)

        if df_display.is_empty():
            self._grid.options["rowData"] = []
            self._grid.options["columnDefs"] = []
        else:
            # Convert to ag-grid format
            self._grid.options["rowData"] = df_display.to_dicts()
            self._grid.options["columnDefs"] = [
                {"field": col, "sortable": True, "filter": True, "resizable": True}
                for col in df_display.columns
            ]
        self._grid.update()

    def _add_highlight_series(
        self, x: float, y: float, words: str, total_reps: int
    ) -> None:
        """
        Add a highlight marker series at the specified coordinates.

        Args:
            x: X coordinate (distinct_posters)
            y: Y coordinate (total_reps with jitter)
            words: The n-gram words string (for click detection and tooltip)
            total_reps: Total repetitions count (for tooltip display)
        """
        if self._chart is None:
            return

        # Remove existing highlight series if present
        self._remove_highlight_series()

        # Add new highlight series with full data for tooltip and click detection
        highlight_series = {
            "name": HIGHLIGHT_SERIES_NAME,
            "type": "scatter",
            "symbolSize": 18,
            "itemStyle": {
                "color": HIGHLIGHT_COLOR,
                "opacity": 1.0,
                "borderColor": "white",
                "borderWidth": 2,
            },
            "z": 100,  # Ensure it's on top
            "data": [{"value": [x, y], "words": words, "total_reps": total_reps}],
        }

        self._chart.options["series"].append(highlight_series)
        self._chart.update()

    def _remove_highlight_series(self) -> None:
        """Remove the highlight marker series from the chart."""
        if self._chart is None:
            return

        series = self._chart.options.get("series", [])
        self._chart.options["series"] = [
            s for s in series if s.get("name") != HIGHLIGHT_SERIES_NAME
        ]
        self._chart.update()

    def _handle_point_click(self, e) -> None:
        """
        Handle click events on scatter plot points.

        Implements toggle behavior:
        - Click unselected point → select it
        - Click selected point → deselect it
        - Click different point → switch selection

        Args:
            e: Click event object with point data
        """
        clicked_words = e.data.get("words")
        if clicked_words is None:
            return

        # Get coordinates for highlight marker
        x, y = e.value  # [distinct_posters, total_reps_jittered]

        if self._selected_words == clicked_words:
            # Clicking same point - deselect
            self._selected_words = None
            self._selected_point_coords = None
            self._remove_highlight_series()
        else:
            # Clicking new point - select it
            self._selected_words = clicked_words
            self._selected_point_coords = (x, y)
            total_reps = e.data.get("total_reps", 0)
            self._add_highlight_series(x, y, clicked_words, total_reps)

        # Update UI components
        self._update_info_label()
        self._update_grid()

    def render_content(self) -> None:
        """Render the scatter plot and data grid in full-width cards."""
        with ui.column().classes("w-full q-pa-md gap-4"):
            # Scatter plot card
            with ui.card().classes("w-full"):
                with ui.card_section():
                    ui.label("N-gram statistics").classes("text-h6")

                # Create chart with empty options and click handler
                self._chart = (
                    ui.echart({}, on_point_click=self._handle_point_click)
                    .classes("w-full")
                    .style("height: 500px")
                )

                # Create placeholder for error/empty state (hidden by default)
                error_container = (
                    ui.row()
                    .classes("w-full justify-center items-center")
                    .style("height: 500px; display: none;")
                )
                with error_container:
                    ui.label("No n-gram data available.").classes(
                        "text-grey-6 text-subtitle1"
                    )

            # Data viewer card
            with ui.card().classes("w-full"):
                with ui.card_section():
                    ui.label("Data viewer").classes("text-h6")

                # Info label showing current state
                self._info_label = ui.label("Loading data...").classes(
                    "text-body2 text-grey-7 q-mb-sm"
                )

                # Data grid
                self._grid = (
                    ui.aggrid(
                        {
                            "columnDefs": [],
                            "rowData": [],
                            "defaultColDef": {
                                "sortable": True,
                                "filter": True,
                                "resizable": True,
                            },
                        },
                        theme="quartz",
                    )
                    .classes("w-full")
                    .style("height: 400px")
                )

            async def load_and_render() -> None:
                """Load data asynchronously and update the chart and grid."""
                stats_path = self._get_parquet_path(OUTPUT_NGRAM_STATS)
                full_path = self._get_parquet_path(OUTPUT_NGRAM_FULL)

                if stats_path is None or self._chart is None:
                    if self._chart is not None:
                        self._chart.set_visibility(False)
                    error_container.style("display: flex;")
                    self.notify_error("No analysis found in the current session.")
                    return

                try:
                    # Load both parquet files in background thread
                    self._df_stats = await run.io_bound(pl.read_parquet, stats_path)
                    if full_path:
                        self._df_full = await run.io_bound(pl.read_parquet, full_path)
                except Exception as exc:
                    if self._chart is not None:
                        self._chart.set_visibility(False)
                    error_container.style("display: flex;")
                    self.notify_error(f"Could not load n-gram results: {exc}")
                    return

                if self._df_stats.is_empty():
                    if self._chart is not None:
                        self._chart.set_visibility(False)
                    error_container.style("display: flex;")
                    return

                # Build ECharts option and update chart
                option = plot_scatter_echart(self._df_stats)
                self._chart.options.update(option)
                self._chart.update()

                # Initialize grid with summary view
                self._update_info_label()
                self._update_grid()

            # Start async loading after page renders (allows spinner to show)
            ui.timer(0, load_and_render, once=True)
