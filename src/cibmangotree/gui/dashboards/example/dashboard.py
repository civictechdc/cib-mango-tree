"""
Example analyzer dashboard page.

The __example__ analyzer is a tutorial for contributors (counts characters
per message), so this dashboard is intentionally minimal:

Layout:
- Histogram of message character-count distribution (full width)
- Data table listing each message's id, character count, and whether it
  was flagged "long" by the example secondary analyzer
"""

import polars as pl
from nicegui import run, ui

from cibmangotree.analyzers.example.example_report.interface import (
    interface as example_report_interface,
)
from cibmangotree.gui.session import GuiSession

from ..base_dashboard import BaseDashboardPage
from .plots import CHARACTER_COUNT_COL, plot_character_count_histogram_echart


class ExampleDashboardPage(BaseDashboardPage):
    """Minimal dashboard for the tutorial/example analyzer."""

    _secondary_analyzer_id = example_report_interface.id

    def __init__(self, session: GuiSession):
        super().__init__(session=session)

        self._chart: ui.echart | None = None
        self._loading: ui.column | None = None
        self._content: ui.column | None = None
        self._grid: ui.aggrid | None = None

    def _load_data(self) -> pl.DataFrame | None:
        path = self.get_output_parquet_path("example_report")
        if path is None:
            return None
        return pl.read_parquet(path)

    async def _load_and_render_async(self) -> None:
        if self._loading is None or self._content is None:
            return

        try:
            df = await run.io_bound(self._load_data)
        except Exception as exc:
            self._show_error(self._loading, f"Could not load example analysis: {exc}")
            return

        if df is None:
            self._show_error(self._loading, "No analysis data found.")
            return

        if df.is_empty():
            self._show_error(self._loading, "No messages found.")
            return

        try:
            option = await run.cpu_bound(plot_character_count_histogram_echart, df)
        except Exception as exc:
            self._show_error(self._loading, f"Could not build chart: {exc}")
            return

        if option is None:
            # run.cpu_bound() returns None (rather than raising) if the task
            # was cancelled or the app is shutting down - retry once rather
            # than crash on the update() call below.
            option = plot_character_count_histogram_echart(df)

        if self._chart is not None:
            self._chart.options.update(option)
            self._chart.update()

        if self._grid is not None:
            df_display = df.rename(
                {
                    "message_id": "Message ID",
                    CHARACTER_COUNT_COL: "Character count",
                    "is_long": "Long message?",
                }
            )
            self._grid.options["rowData"] = df_display.to_dicts()
            self._grid.options["columnDefs"] = [
                {
                    "field": "Message ID",
                    "sortable": True,
                    "filter": True,
                    "resizable": True,
                },
                {
                    "field": "Character count",
                    "sortable": True,
                    "filter": True,
                    "resizable": True,
                },
                {
                    "field": "Long message?",
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
                        "400px"
                    )
                    with self._content:
                        self._chart = (
                            ui.echart({}).classes("w-full").style("height: 350px")
                        )
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
