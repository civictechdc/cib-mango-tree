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
        self._selected_series_index: int | None = None
        self._selected_data_index: int | None = None
        # State for filter
        self._filter_text: str | None = None
        self._filter_applied: bool = False
        self._all_ngram_options: list[str] = []
        # DataFrames
        self._df_stats: pl.DataFrame | None = None
        self._df_full: pl.DataFrame | None = None
        # UI component references (set during render)
        self._chart: ui.echart | None = None
        self._grid: ui.aggrid | None = None
        self._info_label: ui.label | None = None
        self._ngram_select: ui.input | None = None

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

        Respects the current filter text to show only matching n-grams.

        Args:
            n: Number of top n-grams to return (default 100)

        Returns:
            DataFrame with summary columns, sorted by total_reps descending
        """
        # Use filtered stats to respect current filter
        df = self._get_filtered_stats()
        if df.is_empty():
            return pl.DataFrame()

        return (
            df.select(
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
        """Update the info label based on current selection and filter state."""
        if self._info_label is None:
            return

        if self._selected_words is not None:
            # Show detail for selected n-gram (click takes precedence)
            if self._df_full is not None:
                count = self._df_full.filter(
                    pl.col(COL_NGRAM_WORDS) == self._selected_words
                ).height
            else:
                count = 0
            self._info_label.text = (
                f"N-gram: '{self._selected_words}' — {count:,} total repetitions"
            )
        elif self._filter_text:
            # Show filter status
            df_filtered = self._get_filtered_stats()
            count = df_filtered.height
            if count == 0:
                self._info_label.text = (
                    f"No n-grams found matching '{self._filter_text}'. "
                    "Try a different search term."
                )
            elif not self._filter_applied:
                # User is typing, show hint to press Enter
                self._info_label.text = (
                    f"Filter: '{self._filter_text}' — {count:,} matches found. "
                    "Press Enter to apply filter to chart and grid."
                )
            else:
                # Filter has been applied
                self._info_label.text = (
                    f"Showing {min(count, 100):,} of {count:,} n-grams "
                    f"matching '{self._filter_text}'. "
                    "Click a point to view all occurrences."
                )
        else:
            # Default summary view
            self._info_label.text = (
                "Showing top 100 n-grams by frequency. "
                "Type to search, then press Enter to filter. "
                "Click a point to view all occurrences."
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

    def _highlight_point(self, series_index: int, data_index: int) -> None:
        """
        Highlight a point using ECharts dispatchAction (no chart redraw).

        This is much more efficient than adding a separate highlight series,
        as it only toggles visual styles without re-rendering the chart.

        Args:
            series_index: Index of the series containing the point
            data_index: Index of the data point within the series
        """
        if self._chart is None:
            return
        self._chart.run_chart_method(
            "dispatchAction",
            {"type": "highlight", "seriesIndex": series_index, "dataIndex": data_index},
        )

    def _downplay_point(self, series_index: int, data_index: int) -> None:
        """
        Remove highlight from a point using ECharts dispatchAction (no chart redraw).

        Args:
            series_index: Index of the series containing the point
            data_index: Index of the data point within the series
        """
        if self._chart is None:
            return
        self._chart.run_chart_method(
            "dispatchAction",
            {"type": "downplay", "seriesIndex": series_index, "dataIndex": data_index},
        )

    def _clear_all_highlights(self) -> None:
        """
        Clear all highlights from the chart.

        Calling dispatchAction with type 'downplay' without specifying
        seriesIndex/dataIndex will downplay all highlighted elements.
        """
        if self._chart is None:
            return
        self._chart.run_chart_method("dispatchAction", {"type": "downplay"})

    def _handle_point_click(self, e) -> None:
        """
        Handle click events on scatter plot points.

        Implements toggle behavior:
        - Click unselected point → select it
        - Click selected point → deselect it
        - Click different point → switch selection

        Uses ECharts dispatchAction for efficient highlight/downplay without
        triggering a full chart redraw.

        Args:
            e: Click event object with point data (EChartPointClickEventArguments)
        """
        clicked_words = e.data.get("words")
        if clicked_words is None:
            return

        series_index = e.series_index
        data_index = e.data_index

        # Downplay previous selection if any
        if (
            self._selected_series_index is not None
            and self._selected_data_index is not None
        ):
            self._downplay_point(self._selected_series_index, self._selected_data_index)

        if self._selected_words == clicked_words:
            # Clicking same point - deselect (already downplayed above)
            self._selected_words = None
            self._selected_series_index = None
            self._selected_data_index = None
        else:
            # Clicking new point - highlight it
            self._selected_words = clicked_words
            self._selected_series_index = series_index
            self._selected_data_index = data_index
            self._highlight_point(series_index, data_index)

        # Update UI components
        self._update_info_label()
        self._update_grid()

    def _handle_filter_change(self, e) -> None:
        """
        Handle n-gram filter input changes (fires on every keystroke).

        Updates info label to guide user.
        Does NOT update chart/grid (expensive operations) - those happen on Enter.

        Args:
            e: Change event from ui.input with value attribute
        """
        self._filter_text = e.value if e.value else None
        self._filter_applied = False
        # Update info label to show hint
        self._update_info_label()

    def _handle_enter_press(self, e) -> None:
        """
        Handle Enter key press in search input.

        Updates the expensive visualizations (chart and grid) with the
        current filter text. This provides good performance by avoiding
        continuous redraws on every keystroke.

        Args:
            e: Keydown event from ui.input
        """
        # Clear any previous selection
        self._selected_words = None
        self._selected_series_index = None
        self._selected_data_index = None
        self._clear_all_highlights()

        # Mark filter as applied
        self._filter_applied = True

        # Update expensive visualizations
        self._update_chart_with_filter()
        self._update_grid()

        # Update info label to show results
        self._update_info_label()

    def _get_filtered_stats(self) -> pl.DataFrame:
        """
        Get df_stats filtered by the current filter text.

        Returns:
            Filtered DataFrame or full df_stats if no filter is active
        """
        if self._df_stats is None:
            return pl.DataFrame()

        if not self._filter_text:
            return self._df_stats

        # Substring/contains match (case-insensitive)
        return self._df_stats.filter(
            pl.col(COL_NGRAM_WORDS).str.contains(f"(?i){self._filter_text}")
        )

    def _handle_clear(self) -> None:
        """
        Handle clear button click on search input.

        Resets the chart and grid to show the initial unfiltered state.
        """
        # Clear filter state
        self._filter_text = None
        self._filter_applied = False

        # Clear any selection
        self._selected_words = None
        self._selected_series_index = None
        self._selected_data_index = None
        self._clear_all_highlights()

        # Re-render chart with full dataset
        self._update_chart_with_filter()

        # Update grid and info label
        self._update_grid()
        self._update_info_label()

    def _update_chart_with_filter(self) -> None:
        """
        Re-render the chart with filtered data.

        Applies the current filter text to show only matching n-grams.
        """
        if self._chart is None:
            return

        df_filtered = self._get_filtered_stats()

        if df_filtered.is_empty():
            # Show empty chart state
            self._chart.options.clear()
            self._chart.update()
            return

        # Build ECharts option with filtered data
        option = plot_scatter_echart(df_filtered)
        self._chart.options.update(option)
        self._chart.update()

    def render_content(self) -> None:
        """Render the scatter plot and data grid in full-width cards."""
        with ui.row().classes("w-full justify-center"):
            with ui.column().classes("w-3/4 q-pa-md gap-4"):
                # Scatter plot card
                with ui.card().classes("w-full"):
                    self._ngram_select = (
                        ui.input(
                            autocomplete=[],
                            label="Search N-gram",
                            on_change=self._handle_filter_change,
                        )
                        .props('clearable autocomplete="off"')
                        .classes("w-1/4")
                        .on("keydown.enter", self._handle_enter_press)
                        .on("clear", self._handle_clear)
                    )

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
                            self._df_full = await run.io_bound(
                                pl.read_parquet, full_path
                            )
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

                    # Populate filter select with unique n-gram values
                    if self._ngram_select is not None:
                        self._all_ngram_options = (
                            self._df_stats.select(pl.col(COL_NGRAM_WORDS).unique())
                            .sort(COL_NGRAM_WORDS)
                            .to_series()
                            .to_list()
                        )
                        # Set all n-grams as autocomplete options
                        self._ngram_select.set_autocomplete(self._all_ngram_options)

                    # Build ECharts option and update chart
                    option = plot_scatter_echart(self._df_stats)
                    self._chart.options.update(option)
                    self._chart.update()

                    # Initialize grid with summary view
                    self._update_info_label()
                    self._update_grid()

                # Start async loading after page renders (allows spinner to show)
                ui.timer(0, load_and_render, once=True)
