"""
N-grams results dashboard page.

Displays an interactive scatter plot of n-gram frequency vs. unique poster
count, loaded from the ``ngram_stats`` secondary analyzer output. Clicking
a point filters the data grid to show all occurrences of that n-gram.
"""

import polars as pl
from nicegui import run, ui

from cibmangotree.analyzers.ngrams.ngrams_base.interface import (
    COL_MESSAGE_SURROGATE_ID,
    COL_MESSAGE_TEXT,
    OUTPUT_MESSAGE,
    COL_AUTHOR_ID,
    COL_MESSAGE_TIMESTAMP,
)
from cibmangotree.analyzers.ngrams.ngrams_stats.interface import (
    COL_NGRAM_WORDS,
    OUTPUT_NGRAM_FULL,
    OUTPUT_NGRAM_STATS,
)
from cibmangotree.analyzers.ngrams.ngrams_stats.interface import (
    interface as ngram_stats_interface,
)
from cibmangotree.gui.session import GuiSession

from ..base_dashboard import BaseDashboardPage
from .data import filter_ngrams_by_text, make_detail_columns, make_summary_columns
from .plots import SamplingMetadata, plot_scatter_echart, sample_ngram_data

# Number of suggestions to match server-side and send to the browser
MAX_AUTOCOMPLETE_OPTIONS = 50
MIN_AUTOCOMPLETE_CHARS = 2


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

    _secondary_analyzer_id = ngram_stats_interface.id

    def __init__(self, session: GuiSession):
        super().__init__(session=session)
        self._selected_words: str | None = None
        self._selected_series_index: int | None = None
        self._selected_data_index: int | None = None

        self._filter_text: str | None = None
        self._filter_applied: bool = False
        self._all_ngram_options: list[str] = []

        self._df_stats: pl.DataFrame | None = None
        self._df_full: pl.DataFrame | None = None
        self._messages_path: str | None = None
        self._df_stats_sampled: pl.DataFrame | None = None
        self._sampling_metadata: SamplingMetadata | None = None

        self._chart: ui.echart | None = None
        self._grid: ui.aggrid | None = None
        self._info_label: ui.label | None = None
        self._ngram_select: ui.input | None = None
        self._chart_loading: ui.column | None = None
        self._chart_content: ui.column | None = None
        self._grid_loading: ui.column | None = None
        self._grid_content: ui.column | None = None
        self._sampling_label: ui.label | None = None
        self._show_all_btn: ui.button | None = None

        #Popup 
        self._oldest_post: str | None = None
        self._newest_post: str | None = None
        

    def _get_top_n_summary(self, n: int = 100) -> pl.DataFrame:
        df = self._get_filtered_stats()
        if df.is_empty():
            return pl.DataFrame()

        return (
            make_summary_columns(df).sort("Total repetitions", descending=True).head(n)
        )

    def _get_filtered_full_data(self, words: str) -> pl.DataFrame:
        if self._df_full is None or self._df_full.is_empty():
            return pl.DataFrame()

        rows = self._df_full.filter(pl.col(COL_NGRAM_WORDS) == words)
        return self._attach_message_text(rows).pipe(make_detail_columns)

    def _attach_message_text(self, rows: pl.DataFrame) -> pl.DataFrame:
        """
        Look up post text for the rows being displayed.

        The full report omits message_text so it is fetched here for just the
        selected n-gram's rows rather than being held in memory for the whole
        corpus.
        """
        if COL_MESSAGE_TEXT in rows.columns or self._messages_path is None:
            return rows
        if rows.is_empty():
            return rows.with_columns(
                pl.lit(None, dtype=pl.String).alias(COL_MESSAGE_TEXT)
            )

        wanted = rows[COL_MESSAGE_SURROGATE_ID].unique()
        try:
            texts = (
                pl.scan_parquet(self._messages_path)
                .select(COL_MESSAGE_SURROGATE_ID, COL_MESSAGE_TEXT)
                .filter(pl.col(COL_MESSAGE_SURROGATE_ID).is_in(wanted))
                .collect()
            )
        except Exception:
            return rows.with_columns(
                pl.lit(None, dtype=pl.String).alias(COL_MESSAGE_TEXT)
            )

        return rows.join(texts, on=COL_MESSAGE_SURROGATE_ID, how="left")

    def _update_info_label(self) -> None:
        if self._info_label is None:
            return

        if self._selected_words is not None:
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
            df_filtered = self._get_filtered_stats()
            count = df_filtered.height
            if count == 0:
                self._info_label.text = (
                    f"No n-grams found matching '{self._filter_text}'. "
                    "Try a different search term."
                )
            elif not self._filter_applied:
                self._info_label.text = (
                    f"Filter: '{self._filter_text}' — {count:,} matches found. "
                    "Press Enter to apply filter to chart and grid."
                )
            else:
                self._info_label.text = (
                    f"Showing {min(count, 100):,} of {count:,} n-grams "
                    f"matching '{self._filter_text}'. "
                    "Click a point to view all occurrences."
                )
        else:
            self._info_label.text = (
                "Showing top 100 n-grams by frequency. "
                "Type to search, then press Enter to filter. "
                "Click a point to view all occurrences."
            )

    def _update_grid(self) -> None:
        if self._grid is None:
            return

        if self._selected_words is None:
            df_display = self._get_top_n_summary()
        else:
            df_display = self._get_filtered_full_data(self._selected_words)

        if df_display.is_empty():
            self._grid.options["rowData"] = []
            self._grid.options["columnDefs"] = []
        else:
            self._grid.options["rowData"] = df_display.to_dicts()
            column_defs = []
            for col in df_display.columns:
                col_def = {
                    "field": col,
                    "sortable": True,
                    "filter": True,
                    "resizable": True,
                }
                if col == "Post content":
                    col_def[":tooltipValueGetter"] = "(params) => params.value"
                column_defs.append(col_def)
            self._grid.options["columnDefs"] = column_defs
        self._grid.update()

    def _highlight_point(self, series_index: int, data_index: int) -> None:
        if self._chart is None:
            return
        self._chart.run_chart_method(
            "dispatchAction",
            {"type": "highlight", "seriesIndex": series_index, "dataIndex": data_index},
        )

    def _downplay_point(self, series_index: int, data_index: int) -> None:
        self._chart.run_chart_method(
            "dispatchAction",
            {"type": "downplay", "seriesIndex": series_index, "dataIndex": data_index},
        )

    def _clear_all_highlights(self) -> None:
        self._chart.run_chart_method("dispatchAction", {"type": "downplay"})

    #For cell clicking
    def _handle_cell_click(self, e) -> None:
        data = e.args 
        if not data or "data" not in data: 
            return
        
        user = data["data"].get("User ID")
        if not user:
            return    

        col_id = data['colId']
        if col_id == "User ID":
            self._open_user_popup(user)

    #Popup
    def _open_user_popup(self, user) -> None:
        posts = (
            pl.scan_parquet(self._messages_path)
            .filter(pl.col(COL_AUTHOR_ID) == user)
            .select(COL_MESSAGE_TIMESTAMP, COL_MESSAGE_TEXT)
            .collect()
        )
        total_num_posts = posts.height
        self._oldest_post = posts[COL_MESSAGE_TIMESTAMP].min()
        self._newest_post = posts[COL_MESSAGE_TIMESTAMP].max()

        posts = posts.with_columns(pl.col(COL_MESSAGE_TIMESTAMP).dt.strftime("%B %d, %Y %H:%M:%S"))

       
        with ui.dialog() as dialog, ui.card().classes("w-full").style("max-width: none"):
            with ui.row().classes("w-full justify-between items-center"):
                ui.label(f"User Viewer - {user}").classes("text-h6")
                ui.button(icon="close", on_click=dialog.close).props("flat round dense") 
            with ui.row().classes("text-body2 text-grey-7 gap-7"):
                ui.label(f"Total Posts: {total_num_posts}")
                ui.label(f"First Post: { self._oldest_post.strftime("%H:%M:%S %d/%M/%Y") }")
                ui.label(f"Last Post: { self._newest_post.strftime("%H:%M:%S %d/%M/%Y") }")
            ui.aggrid(
                        {
                        "columnDefs": [
                            {"headerName": "Post Content", "field": COL_MESSAGE_TEXT},
                            {"headerName": "Timestamp", "field": COL_MESSAGE_TIMESTAMP}
                        ],
                        "rowData": posts.to_dicts(),
                        "defaultColDef": {
                            "sortable": True,
                            "filter": True,
                            "resizable": True,
                            },
                        "tooltipShowDelay": 200,
                        "tooltipSwitchShowDelay": 70,
                        ":tooltipValueGetter": "(params) => params.value"
                        },
                        theme="quartz",
                    ).classes("w-full").style("height: 400px")   
                    
        dialog.open()
        


    def _handle_point_click(self, e) -> None:
        clicked_words = e.data.get("words")
        if clicked_words is None:
            return

        series_index = e.series_index
        data_index = e.data_index

        if (
            self._selected_series_index is not None
            and self._selected_data_index is not None
        ):
            self._downplay_point(self._selected_series_index, self._selected_data_index)

        if self._selected_words == clicked_words:
            self._selected_words = None
            self._selected_series_index = None
            self._selected_data_index = None
        else:
            self._selected_words = clicked_words
            self._selected_series_index = series_index
            self._selected_data_index = data_index
            self._highlight_point(series_index, data_index)

        self._update_info_label()
        self._update_grid()

    def _handle_filter_change(self, e) -> None:
        self._filter_text = e.value if e.value else None
        self._filter_applied = False
        self._refresh_autocomplete()
        self._update_info_label()

    def _refresh_autocomplete(self) -> None:
        """
        Offer suggestions for what the user has typed so far.

        Matches internally to avoid handing the websocket too much information
        and sabotaging the connection
        """
        if self._ngram_select is None:
            return

        text = (self._filter_text or "").strip()
        if self._df_stats is None or len(text) < MIN_AUTOCOMPLETE_CHARS:
            self._all_ngram_options = []
            self._ngram_select.set_autocomplete([])
            return

        try:
            matches = (
                filter_ngrams_by_text(self._df_stats, text)
                .select(COL_NGRAM_WORDS)
                .unique()
                .sort(COL_NGRAM_WORDS)
                .head(MAX_AUTOCOMPLETE_OPTIONS)
                .to_series()
                .to_list()
            )
        except Exception:
            # A partially typed value can be an invalid regex, offer nothing
            matches = []

        self._all_ngram_options = matches
        self._ngram_select.set_autocomplete(matches)

    def _handle_enter_press(self, e) -> None:
        self._selected_words = None
        self._selected_series_index = None
        self._selected_data_index = None
        self._clear_all_highlights()

        self._filter_applied = True

        self._update_chart_with_filter()
        self._update_grid()
        self._update_info_label()

    def _get_filtered_stats(self) -> pl.DataFrame:
        if self._df_stats is None:
            return pl.DataFrame()

        if not self._filter_text:
            return (
                self._df_stats_sampled
                if self._df_stats_sampled is not None
                else self._df_stats
            )

        return filter_ngrams_by_text(self._df_stats, self._filter_text)

    def _handle_clear(self) -> None:
        self._filter_text = None
        self._filter_applied = False

        self._selected_words = None
        self._selected_series_index = None
        self._selected_data_index = None
        self._clear_all_highlights()

        self._refresh_autocomplete()
        self._update_chart_with_filter()
        self._update_grid()
        self._update_info_label()

    async def _load_and_render_async(self) -> None:
        stats_path = self.get_output_parquet_path(OUTPUT_NGRAM_STATS)
        full_path = self.get_output_parquet_path(OUTPUT_NGRAM_FULL)
        self._messages_path = self.get_primary_output_parquet_path(OUTPUT_MESSAGE)

        if stats_path is None:
            if self._chart_loading is not None:
                self._show_error(
                    self._chart_loading, "No analysis found in the current session."
                )
            return

        try:
            self._df_stats = await run.io_bound(pl.read_parquet, stats_path)
            if full_path:
                self._df_full = await run.io_bound(pl.read_parquet, full_path)
        except Exception as exc:
            if self._chart_loading is not None:
                self._show_error(
                    self._chart_loading, f"Could not load n-gram results: {exc}"
                )
            return

        if self._df_stats.is_empty():
            if self._chart_loading is not None:
                self._show_error(self._chart_loading, "No n-gram data available.")
            return

        try:
            self._df_stats_sampled, self._sampling_metadata = await run.cpu_bound(
                sample_ngram_data,
                self._df_stats,
                50000,
            )
            option = await run.cpu_bound(
                plot_scatter_echart,
                self._df_stats_sampled,
                False,
            )
        except Exception as exc:
            if self._chart_loading is not None:
                self._show_error(self._chart_loading, f"Could not build chart: {exc}")
            return

        # suggestions computed per keystroke in _handle_filter_change
        self._refresh_autocomplete()

        if (
            self._chart is None
            or self._chart_content is None
            or self._chart_loading is None
        ):
            return
        self._chart.options.update(option)
        self._chart.update()
        self._show_content(self._chart_loading, self._chart_content)

        self._update_sampling_info_label()
        self._update_info_label()
        self._update_grid()
        if self._grid_loading is not None and self._grid_content is not None:
            self._show_content(self._grid_loading, self._grid_content)

    def _update_sampling_info_label(self) -> None:
        if self._sampling_label is None or self._sampling_metadata is None:
            return
        self._sampling_label.text = self._sampling_metadata.sampling_message
        if self._show_all_btn is not None:
            self._show_all_btn.set_visibility(self._sampling_metadata.is_sampled)

    async def _handle_show_all_click(self) -> None:
        if self._df_stats is None:
            return

        total = len(self._df_stats)

        if total > 100_000:
            with ui.dialog() as dialog, ui.card():
                ui.label(f"Load all {total:,} data points?").classes("text-h6")
                ui.label(
                    "This may cause the browser to slow down or become unresponsive."
                ).classes("text-body2 text-grey-7")
                with ui.row().classes("gap-4 justify-end"):
                    ui.button("Cancel", on_click=dialog.close).props("flat")

                    async def _confirm():
                        dialog.close()
                        await self._load_full_dataset()

                    ui.button("Load all", on_click=_confirm, color="primary")
            dialog.open()
        else:
            await self._load_full_dataset()

    async def _load_full_dataset(self) -> None:
        if self._show_all_btn is not None:
            self._show_all_btn.set_enabled(False)
        if self._sampling_label is not None:
            self._sampling_label.text = "Loading full dataset..."

        if self._df_stats is None:
            return

        df_stats = self._df_stats

        try:
            option = await run.cpu_bound(
                plot_scatter_echart,
                df_stats,
                False,
            )
        except Exception as exc:
            self.notify_error(f"Could not load full dataset: {exc}")
            if self._show_all_btn is not None:
                self._show_all_btn.set_enabled(True)
            return

        self._df_stats_sampled = df_stats
        self._sampling_metadata = SamplingMetadata(
            total_count=len(df_stats),
            sampled_count=len(df_stats),
            is_sampled=False,
            strategy="none",
        )

        if self._chart is not None:
            self._chart.options.update(option)
            self._chart.update()
        self._update_sampling_info_label()

    def _update_chart_with_filter(self) -> None:
        if self._chart is None:
            return

        df_filtered = self._get_filtered_stats()

        if df_filtered.is_empty():
            self._chart.options.clear()
            self._chart.update()
            return

        option = plot_scatter_echart(df_filtered, enable_large_mode=False)
        self._chart.options.update(option)
        self._chart.update()

    def render_content(self) -> None:
        ui.add_css("""
            .ag-tooltip {
                white-space: normal !important;
                max-width: 450px !important;
                word-wrap: break-word !important;
            }
        """)
        with ui.row().classes("w-full justify-center"):
            with ui.column().classes("w-3/4 q-pa-md gap-4"):
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

                    self._chart_loading, self._chart_content = (
                        self._create_loading_container("500px")
                    )
                    with self._chart_content:
                        self._chart = (
                            ui.echart({}, on_point_click=self._handle_point_click)
                            .classes("w-full")
                            .style("height: 500px")
                        )
                with ui.row().classes("w-full items-center gap-4"):
                    self._sampling_label = ui.label("").classes(
                        "text-body2 text-grey-7"
                    )
                    self._show_all_btn = ui.button(
                        "Show all data",
                        on_click=self._handle_show_all_click,
                        color="secondary",
                    ).props("outline dense")
                    self._show_all_btn.set_visibility(False)

                with ui.card().classes("w-full"):
                    with ui.card_section():
                        ui.label("Data viewer").classes("text-h6")
                    self._info_label = ui.label("Loading data...").classes(
                        "text-body2 text-grey-7 q-mb-sm"
                    )
                    self._grid_loading, self._grid_content = (
                        self._create_loading_container("400px")
                    )
                    with self._grid_content:
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
                                    "tooltipShowDelay": 200,
                                    "tooltipSwitchShowDelay": 70,
                                },
                                theme="quartz",
                            )
                            .classes("w-full")
                            .style("height: 400px")
                        )
                        #For popup
                        self._grid.on("cellClicked", self._handle_cell_click)

        ui.timer(0, self._load_and_render_async, once=True)
