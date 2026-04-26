"""
Hashtags analyzer dashboard page.

Layout (Option A - Ranked Lists):
- Top: Gini line plot (full width) — click to select time window
- Middle-left: Hashtag ranked list (AG-Grid) — click row to select hashtag
- Middle-right: User ranked list (AG-Grid) — click row to select user
- Bottom: Tweet Explorer (AG-Grid) — shows tweets for selected user/hashtag/window
"""

from datetime import datetime

import polars as pl
from nicegui import run, ui

from analyzers.hashtags.hashtags_base.interface import (
    COL_AUTHOR_ID,
    COL_POST,
    COL_TIME,
    OUTPUT_COL_GINI,
    OUTPUT_COL_HASHTAGS,
    OUTPUT_COL_TIMESPAN,
    SECONDARY_COL_HASHTAG_PERC,
    SECONDARY_COL_USERS_ALL,
)
from analyzers.hashtags.hashtags_web.analysis import secondary_analyzer
from gui.dashboards.hashtags_data import (
    extract_users_for_hashtag,
    load_primary_output,
    load_transformed_raw_input,
)
from gui.dashboards.hashtags_plots import plot_gini_echart
from gui.session import GuiSession

from .base_dashboard import BaseDashboardPage


class HashtagsDashboardPage(BaseDashboardPage):
    """
    Hashtags dashboard with ranked lists instead of bar charts.

    Dependency chain:
    Gini plot click -> sets timewindow -> populates hashtag list
    Hashtag row click -> populates user list
    User row click -> populates tweet explorer
    """

    def __init__(self, session: GuiSession):
        super().__init__(session=session)

        # Data
        self._df_primary: pl.DataFrame | None = None
        self._df_raw: pl.DataFrame | None = None
        self._df_secondary: pl.DataFrame | None = None
        self._df_users: pl.DataFrame | None = None
        self._smooth: bool = False

        # State
        self._selected_timewindow: datetime | None = None
        self._selected_hashtag: str | None = None
        self._selected_user: str | None = None

        # UI references - Gini plot
        self._gini_chart: ui.echart | None = None
        self._gini_loading: ui.column | None = None
        self._gini_content: ui.column | None = None
        self._smooth_checkbox: ui.checkbox | None = None

        # UI references - Hashtag list
        self._hashtag_grid: ui.aggrid | None = None
        self._hashtag_loading: ui.column | None = None
        self._hashtag_content: ui.column | None = None
        self._hashtag_info: ui.label | None = None

        # UI references - User list
        self._user_grid: ui.aggrid | None = None
        self._user_loading: ui.column | None = None
        self._user_content: ui.column | None = None
        self._user_info: ui.label | None = None

        # UI references - Tweet explorer
        self._tweet_grid: ui.aggrid | None = None
        self._tweet_loading: ui.column | None = None
        self._tweet_content: ui.column | None = None
        self._tweet_info: ui.label | None = None

    # -- Data loading -----------------------------------------------

    async def _load_and_render_async(self) -> None:
        try:
            self._df_primary = await run.io_bound(load_primary_output, self.session)
        except Exception as exc:
            if self._gini_loading is not None:
                self._show_error(
                    self._gini_loading, f"Could not load hashtag analysis: {exc}"
                )
            return

        if self._df_primary.is_empty():
            if self._gini_loading is not None:
                self._show_error(self._gini_loading, "No hashtag data available.")
            return

        try:
            option = await run.cpu_bound(
                plot_gini_echart,
                self._df_primary,
                self._smooth,
            )
        except Exception as exc:
            if self._gini_loading is not None:
                self._show_error(self._gini_loading, f"Could not build chart: {exc}")
            return

        if (
            self._gini_chart is None
            or self._gini_content is None
            or self._gini_loading is None
        ):
            return

        self._gini_chart.options.update(option)
        self._gini_chart.update()
        self._show_content(self._gini_loading, self._gini_content)

    async def _load_raw_input(self) -> None:
        """Load raw input data for tweet explorer (expensive, deferred)."""
        if self._df_raw is not None:
            return
        try:
            self._df_raw = await run.io_bound(load_transformed_raw_input, self.session)
        except Exception as exc:
            self.notify_error(f"Could not load raw input data: {exc}")

    # -- Gini plot handlers -----------------------------------------

    def _handle_smooth_change(self, e) -> None:
        self._smooth = e.value
        if self._gini_chart is not None and self._df_primary is not None:
            option = plot_gini_echart(self._df_primary, smooth=self._smooth)
            self._gini_chart.options.update(option)
            self._gini_chart.update()

    def _handle_gini_click(self, e) -> None:
        """Handle click on Gini line plot point."""
        clicked_value = e.data
        if clicked_value is None or len(clicked_value) < 1:
            return

        time_str = clicked_value[0]
        try:
            timewindow = datetime.strptime(time_str, "%Y-%m-%d %H:%M")
        except ValueError:
            return

        if self._selected_timewindow == timewindow:
            return

        self._selected_timewindow = timewindow
        self._selected_hashtag = None
        self._selected_user = None

        self._update_hashtag_info()
        self._clear_user_grid()
        self._clear_tweet_grid()

        ui.timer(0, self._run_secondary_analysis, once=True)

    async def _run_secondary_analysis(self) -> None:
        """Run secondary analysis for selected timewindow and populate hashtag list."""
        if self._df_primary is None or self._selected_timewindow is None:
            return

        if self._hashtag_loading is None or self._hashtag_content is None:
            return

        try:
            df_secondary = await run.cpu_bound(
                secondary_analyzer,
                self._df_primary,
                self._selected_timewindow,
            )
        except Exception as exc:
            self._show_error(
                self._hashtag_loading, f"Could not analyze time window: {exc}"
            )
            return

        if df_secondary.is_empty():
            self._show_error(
                self._hashtag_loading, "No hashtag data for this time window."
            )
            return

        self._df_secondary = df_secondary
        self._update_hashtag_grid()
        self._show_content(self._hashtag_loading, self._hashtag_content)
        self._update_hashtag_info()

    # -- Hashtag list handlers --------------------------------------

    def _update_hashtag_grid(self) -> None:
        """Populate hashtag ranked list."""
        if self._hashtag_grid is None or self._df_secondary is None:
            return

        df_display = (
            self._df_secondary.select(
                [
                    OUTPUT_COL_HASHTAGS,
                    SECONDARY_COL_HASHTAG_PERC,
                    SECONDARY_COL_USERS_ALL,
                ]
            )
            .with_columns(
                n_users=pl.col(SECONDARY_COL_USERS_ALL).list.len(),
            )
            .sort(SECONDARY_COL_HASHTAG_PERC, descending=True)
            .rename(
                {
                    OUTPUT_COL_HASHTAGS: "Hashtag",
                    SECONDARY_COL_HASHTAG_PERC: "% of hashtags",
                    "n_users": "Unique users",
                }
            )
        )

        self._hashtag_grid.options["rowData"] = df_display.to_dicts()
        self._hashtag_grid.options["columnDefs"] = [
            {"field": "Hashtag", "sortable": True, "filter": True, "resizable": True},
            {
                "field": "% of hashtags",
                "sortable": True,
                "filter": True,
                "resizable": True,
                ":valueFormatter": "(params) => params.value.toFixed(1) + '%'",
            },
            {
                "field": "Unique users",
                "sortable": True,
                "filter": True,
                "resizable": True,
            },
        ]
        self._hashtag_grid.update()

    def _handle_hashtag_click(self, e) -> None:
        """Handle click on hashtag row."""
        data = e.args
        if not data or "data" not in data:
            return

        row_data = data["data"]
        hashtag = row_data.get("Hashtag")
        if not hashtag:
            return

        if self._selected_hashtag == hashtag:
            return

        self._selected_hashtag = hashtag
        self._selected_user = None

        self._clear_tweet_grid()
        self._update_user_grid()
        self._update_user_info()

    def _update_hashtag_info(self) -> None:
        """Update info label for hashtag panel."""
        if self._hashtag_info is None:
            return

        if self._selected_timewindow is None:
            self._hashtag_info.text = (
                "Click a point on the chart above to explore hashtags."
            )
        elif self._df_secondary is None:
            self._hashtag_info.text = "Loading hashtag data..."
        else:
            n_hashtags = len(self._df_secondary)
            date_str = self._selected_timewindow.strftime("%B %d, %Y %H:%M")
            self._hashtag_info.text = (
                f"{n_hashtags} hashtags found in window starting {date_str}"
            )

    # -- User list handlers -----------------------------------------

    def _update_user_grid(self) -> None:
        """Populate user ranked list for selected hashtag."""
        if (
            self._user_grid is None
            or self._df_secondary is None
            or self._selected_hashtag is None
        ):
            return

        df_users = extract_users_for_hashtag(self._df_secondary, self._selected_hashtag)

        if df_users.is_empty():
            self._clear_user_grid()
            return

        self._df_users = df_users

        self._user_grid.options["rowData"] = df_users.to_dicts()
        self._user_grid.options["columnDefs"] = [
            {"field": "User", "sortable": True, "filter": True, "resizable": True},
            {"field": "Posts", "sortable": True, "filter": True, "resizable": True},
        ]
        self._user_grid.update()

        if self._user_loading is not None and self._user_content is not None:
            self._show_content(self._user_loading, self._user_content)

    def _handle_user_click(self, e) -> None:
        """Handle click on user row."""
        data = e.args
        if not data or "data" not in data:
            return

        row_data = data["data"]
        user = row_data.get("User")
        if not user:
            return

        if self._selected_user == user:
            return

        self._selected_user = user
        ui.timer(0, self._load_tweets, once=True)

    def _update_user_info(self) -> None:
        """Update info label for user panel."""
        if self._user_info is None:
            return

        if self._selected_hashtag is None:
            self._user_info.text = "Click a hashtag above to see which users posted it."
        elif self._df_users is not None:
            n_users = len(self._df_users)
            self._user_info.text = f"{n_users} users posted '{self._selected_hashtag}'"
        else:
            self._user_info.text = "Loading user data..."

    def _clear_user_grid(self) -> None:
        """Clear user grid and reset state."""
        self._selected_user = None
        self._df_users = None
        if self._user_grid is not None:
            self._user_grid.options["rowData"] = []
            self._user_grid.options["columnDefs"] = []
            self._user_grid.update()
        self._update_user_info()
        if self._user_loading is not None:
            self._show_error(self._user_loading, "Select a hashtag to see users.")

    # -- Tweet explorer handlers ------------------------------------

    async def _load_tweets(self) -> None:
        """Load tweets for selected user/hashtag/timewindow."""
        if (
            self._selected_user is None
            or self._selected_hashtag is None
            or self._selected_timewindow is None
        ):
            return

        if self._tweet_loading is None or self._tweet_content is None:
            return

        await self._load_raw_input()

        if self._df_raw is None:
            self._show_error(self._tweet_loading, "Could not load tweet data.")
            return

        time_step = self._get_time_step()
        if time_step is None:
            self._show_error(
                self._tweet_loading, "Could not determine time window duration."
            )
            return

        timewindow_end = self._selected_timewindow + time_step

        try:
            df_tweets = await run.cpu_bound(
                self._filter_tweets,
                self._df_raw,
                self._selected_user,
                self._selected_hashtag,
                self._selected_timewindow,
                timewindow_end,
            )
        except Exception as exc:
            self._show_error(self._tweet_loading, f"Could not filter tweets: {exc}")
            return

        if df_tweets.is_empty():
            self._show_error(self._tweet_loading, "No tweets found for this selection.")
            return

        self._update_tweet_grid(df_tweets)
        self._show_content(self._tweet_loading, self._tweet_content)
        self._update_tweet_info(len(df_tweets))

    @staticmethod
    def _filter_tweets(
        df_raw: pl.DataFrame,
        user: str,
        hashtag: str,
        time_start: datetime,
        time_end: datetime,
    ) -> pl.DataFrame:
        """Filter raw tweets for user, hashtag, and time window."""
        return (
            df_raw.filter(
                pl.col(COL_AUTHOR_ID) == user,
                pl.col(COL_TIME).is_between(time_start, time_end),
                pl.col(COL_POST).str.contains(hashtag, literal=True),
            )
            .with_columns(pl.col(COL_TIME).dt.strftime("%B %d, %Y %I:%M %p"))
            .select([COL_TIME, COL_POST])
            .rename({COL_TIME: "Timestamp", COL_POST: "Post"})
        )

    def _update_tweet_grid(self, df_tweets: pl.DataFrame) -> None:
        """Populate tweet explorer grid."""
        if self._tweet_grid is None:
            return

        self._tweet_grid.options["rowData"] = df_tweets.to_dicts()
        self._tweet_grid.options["columnDefs"] = [
            {
                "field": "Timestamp",
                "sortable": True,
                "filter": True,
                "resizable": True,
            },
            {
                "field": "Post",
                "sortable": False,
                "filter": True,
                "resizable": True,
                "wrapText": True,
                "autoHeight": True,
                ":tooltipValueGetter": "(params) => params.value",
            },
        ]
        self._tweet_grid.update()

    def _update_tweet_info(self, count: int) -> None:
        """Update info label for tweet panel."""
        if self._tweet_info is None:
            return
        self._tweet_info.text = f"{count} posts found"

    def _clear_tweet_grid(self) -> None:
        """Clear tweet grid and reset state."""
        self._selected_user = None
        if self._tweet_grid is not None:
            self._tweet_grid.options["rowData"] = []
            self._tweet_grid.options["columnDefs"] = []
            self._tweet_grid.update()
        if self._tweet_info is not None:
            self._tweet_info.text = "Click a user above to see their posts."
        if self._tweet_loading is not None:
            self._show_error(self._tweet_loading, "Select a user to see their posts.")

    def _get_time_step(self):
        """Calculate time step from primary output."""
        if self._df_primary is None or len(self._df_primary) < 2:
            return None
        return (
            self._df_primary[OUTPUT_COL_TIMESPAN][1]
            - self._df_primary[OUTPUT_COL_TIMESPAN][0]
        )

    # -- Rendering --------------------------------------------------

    def render_content(self) -> None:
        """Render the dashboard with ranked lists layout."""
        ui.add_css(
            """
            .ag-row {
                cursor: pointer !important;
            }
            .ag-row-hover {
                background-color: #e3f2fd !important;
            }
            """
        )
        with ui.row().classes("w-full justify-center"):
            with ui.column().classes("w-3/4 q-pa-md gap-4"):
                # -- Gini line plot ----------------------------------
                with ui.card().classes("w-full"):
                    with ui.row().classes("w-full items-center"):
                        self._smooth_checkbox = ui.checkbox(
                            "Show smoothed line",
                            value=False,
                            on_change=self._handle_smooth_change,
                        )
                    self._gini_loading, self._gini_content = (
                        self._create_loading_container("350px")
                    )
                    with self._gini_content:
                        self._gini_chart = (
                            ui.echart(
                                {},
                                on_point_click=self._handle_gini_click,
                            )
                            .classes("w-full")
                            .style("height: 350px")
                        )

                # -- Middle row: Hashtag list + User list ------------
                with ui.row().classes("w-full gap-4"):
                    # Hashtag ranked list
                    with ui.card().classes("flex-1"):
                        with ui.card_section():
                            ui.label("Hashtags").classes("text-h6")
                            self._hashtag_info = ui.label(
                                "Click a point on the chart above to explore hashtags."
                            ).classes("text-body2 text-grey-7 q-mb-sm")
                        self._hashtag_loading, self._hashtag_content = (
                            self._create_loading_container("300px")
                        )
                        self._show_error(
                            self._hashtag_loading,
                            "Select a time window to see hashtags.",
                        )
                        with self._hashtag_content:
                            self._hashtag_grid = (
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
                            self._hashtag_grid.on(
                                "cellClicked", self._handle_hashtag_click
                            )

                    # User ranked list
                    with ui.card().classes("flex-1"):
                        with ui.card_section():
                            ui.label("Users").classes("text-h6")
                            self._user_info = ui.label(
                                "Click a hashtag above to see which users posted it."
                            ).classes("text-body2 text-grey-7 q-mb-sm")
                        self._user_loading, self._user_content = (
                            self._create_loading_container("300px")
                        )
                        self._show_error(
                            self._user_loading,
                            "Select a hashtag to see users.",
                        )
                        with self._user_content:
                            self._user_grid = (
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
                            self._user_grid.on("cellClicked", self._handle_user_click)

                # -- Tweet Explorer ----------------------------------
                with ui.card().classes("w-full"):
                    with ui.card_section():
                        ui.label("Tweet Explorer").classes("text-h6")
                        self._tweet_info = ui.label(
                            "Click a user above to see their posts."
                        ).classes("text-body2 text-grey-7 q-mb-sm")
                    self._tweet_loading, self._tweet_content = (
                        self._create_loading_container("300px")
                    )
                    self._show_error(
                        self._tweet_loading,
                        "Select a user to see their posts.",
                    )
                    with self._tweet_content:
                        self._tweet_grid = (
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
                            .style("height: 300px")
                        )

        ui.timer(0, self._load_and_render_async, once=True)
