"""
Time coordination analyzer dashboard page.

Layout:
- Horizontal bar chart of the top coordinated user pairs (full width)
- Full ranked table of all coordinated pairs below the chart
"""

import polars as pl
from nicegui import run, ui

from cibmangotree.analyzers.time_coordination.interface import (
    OUTPUT_COL_FREQ,
    OUTPUT_COL_USER1,
    OUTPUT_COL_USER2,
)
from cibmangotree.gui.session import GuiSession

from ..base_dashboard import BaseDashboardPage
from .data import load_coordinated_pairs
from .plots import plot_top_pairs_echart

# A dataset with even a few thousand active users can produce tens of
# thousands of coordinated pairs. Sending all of them to the browser in one
# grid update is a multi-megabyte websocket payload that can stall or crash
# the client mid-render (matching the ngrams dashboard's own
# sample_ngram_data() cap, which exists for the same reason).
MAX_GRID_ROWS = 500


class TimeCoordinationDashboardPage(BaseDashboardPage):
    """Dashboard showing which users post in a time-coordinated manner."""

    def __init__(self, session: GuiSession):
        super().__init__(session=session)

        self._chart: ui.echart | None = None
        self._loading: ui.column | None = None
        self._content: ui.column | None = None
        self._grid: ui.aggrid | None = None
        self._grid_note: ui.label | None = None

    async def _load_and_render_async(self) -> None:
        if self._loading is None or self._content is None:
            return

        try:
            df = await run.io_bound(load_coordinated_pairs, self)
        except Exception as exc:
            self._show_error(
                self._loading, f"Could not load time coordination analysis: {exc}"
            )
            return

        if df is None:
            self._show_error(self._loading, "No analysis data found.")
            return

        if df.is_empty():
            self._show_error(self._loading, "No coordinated user pairs were found.")
            return

        try:
            option = await run.cpu_bound(plot_top_pairs_echart, df)
        except Exception as exc:
            self._show_error(self._loading, f"Could not build chart: {exc}")
            return

        if option is None:
            # run.cpu_bound() returns None (rather than raising) if the task
            # was cancelled or the app is shutting down - retry once rather
            # than crash on the update() call below.
            option = plot_top_pairs_echart(df)

        if self._chart is not None:
            self._chart.options.update(option)
            self._chart.update()

        if self._grid_note is not None:
            total_pairs = len(df)
            if total_pairs > MAX_GRID_ROWS:
                self._grid_note.text = (
                    f"Showing the top {MAX_GRID_ROWS} of {total_pairs} coordinated "
                    "pairs by co-occurrence count."
                )
                self._grid_note.set_visibility(True)
            else:
                self._grid_note.set_visibility(False)

        if self._grid is not None:
            df_display = df.head(MAX_GRID_ROWS).rename(
                {
                    OUTPUT_COL_USER1: "User 1",
                    OUTPUT_COL_USER2: "User 2",
                    OUTPUT_COL_FREQ: "Co-occurrences",
                }
            )
            self._grid.options["rowData"] = df_display.to_dicts()
            self._grid.options["columnDefs"] = [
                {
                    "field": "User 1",
                    "sortable": True,
                    "filter": True,
                    "resizable": True,
                },
                {
                    "field": "User 2",
                    "sortable": True,
                    "filter": True,
                    "resizable": True,
                },
                {
                    "field": "Co-occurrences",
                    "sortable": True,
                    "filter": True,
                    "resizable": True,
                },
            ]
            self._grid.update()

        self._show_content(self._loading, self._content)

    def render_content(self) -> None:
        with ui.row().classes("w-full justify-center"):
            with ui.column().classes("w-3/4 q-pa-md gap-4"):
                with ui.card().classes("w-full"):
                    self._loading, self._content = self._create_loading_container(
                        "500px"
                    )
                    with self._content:
                        self._chart = (
                            ui.echart({}).classes("w-full").style("height: 450px")
                        )
                        ui.label("All coordinated pairs").classes("text-h6 q-mt-md")
                        self._grid_note = ui.label().classes("text-body2 text-grey-7")
                        self._grid_note.set_visibility(False)
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
                            .style("height: 300px")
                        )

        ui.timer(0, self._load_and_render_async, once=True)
