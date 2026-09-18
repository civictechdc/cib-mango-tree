"""
Temporal analyzer dashboard page.

Layout:
- Bar chart of post counts per time-of-day interval (full width)
- Data table with the same interval/count breakdown below the chart
"""

import polars as pl
from nicegui import run, ui

from cibmangotree.analyzers.temporal.temporal_base.interface import (
    OUTPUT_COL_POST_COUNT,
    OUTPUT_COL_TIME_INTERVAL_END,
    OUTPUT_COL_TIME_INTERVAL_START,
    OUTPUT_TABLE_INTERVAL_COUNT,
)
from cibmangotree.gui.session import GuiSession

from ..base_dashboard import BaseDashboardPage
from .plots import plot_temporal_bar_echart


class TemporalDashboardPage(BaseDashboardPage):
    """Dashboard showing posting activity broken down by time of day."""

    def __init__(self, session: GuiSession):
        super().__init__(session=session)

        self._chart: ui.echart | None = None
        self._loading: ui.column | None = None
        self._content: ui.column | None = None
        self._grid: ui.aggrid | None = None

    def _load_data(self) -> pl.DataFrame | None:
        path = self.get_primary_output_parquet_path(OUTPUT_TABLE_INTERVAL_COUNT)
        if path is None:
            return None
        return pl.read_parquet(path)

    async def _load_and_render_async(self) -> None:
        if self._loading is None or self._content is None:
            return

        try:
            df = await run.io_bound(self._load_data)
        except Exception as exc:
            self._show_error(self._loading, f"Could not load temporal analysis: {exc}")
            return

        if df is None:
            self._show_error(self._loading, "No analysis data found.")
            return

        if df.is_empty():
            self._show_error(self._loading, "No temporal data available.")
            return

        try:
            option = await run.cpu_bound(plot_temporal_bar_echart, df)
        except Exception as exc:
            self._show_error(self._loading, f"Could not build chart: {exc}")
            return

        if option is None:
            # run.cpu_bound() returns None (rather than raising) if the task
            # was cancelled or the app is shutting down - retry once rather
            # than crash on the update() call below.
            option = plot_temporal_bar_echart(df)

        if self._chart is not None:
            self._chart.options.update(option)
            self._chart.update()

        if self._grid is not None:
            df_display = df.select(
                [
                    OUTPUT_COL_TIME_INTERVAL_START,
                    OUTPUT_COL_TIME_INTERVAL_END,
                    OUTPUT_COL_POST_COUNT,
                ]
            ).rename(
                {
                    OUTPUT_COL_TIME_INTERVAL_START: "Interval start",
                    OUTPUT_COL_TIME_INTERVAL_END: "Interval end",
                    OUTPUT_COL_POST_COUNT: "Post count",
                }
            )
            self._grid.options["rowData"] = [
                {k: str(v) if k != "Post count" else v for k, v in row.items()}
                for row in df_display.to_dicts()
            ]
            self._grid.options["columnDefs"] = [
                {
                    "field": "Interval start",
                    "sortable": True,
                    "filter": True,
                    "resizable": True,
                },
                {
                    "field": "Interval end",
                    "sortable": True,
                    "filter": True,
                    "resizable": True,
                },
                {
                    "field": "Post count",
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
