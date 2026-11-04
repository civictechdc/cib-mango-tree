"""Time analysis results dashboard — Explore network.

Ported from cib-time-analysis Explore step. Configure dataset buttons and
in-dashboard Build are intentionally omitted: the host workflow already ran
the primary analyzer. Compare users opens a separate screen.
"""

from __future__ import annotations

import polars as pl
from nicegui import ui
from nicegui.events import GenericEventArguments

from cibmangotree.analyzers.time_analysis.graph_utils import (
    EXPLORE_MAX_PAIRS,
    cut_graph_by_weight,
    graph_from_edges_df,
    remember_top_edges,
)
from cibmangotree.analyzers.time_analysis.time_analysis_base.analysis import (
    METHOD_LABELS,
)
from cibmangotree.analyzers.time_analysis.time_analysis_base.interface import (
    COL_USER_ID,
    OUTPUT_EDGES,
    OUTPUT_POSTS,
    PARAM_METHOD,
)
from cibmangotree.gui.routes import gui_routes
from cibmangotree.gui.session import GuiSession

from ..base_dashboard import BaseDashboardPage
from .chart_utils import (
    ALL_EDGE_GROUPS,
    EDGE_COLOR_LEGEND,
    NETWORK_CLICK_JS,
    apply_edge_group_visibility,
    network_hover_clear_labels_js,
    network_hover_show_labels_js,
    plot_subgraph_echart,
    users_from_edge_payload,
)


class TimeAnalysisDashboardPage(BaseDashboardPage):
    """Explore the user network; Compare users opens a separate screen."""

    # Primary-only outputs; no secondary analyzer for v1.
    _secondary_analyzer_id = None

    def __init__(self, session: GuiSession):
        super().__init__(session=session)
        self._graph = None
        self._cut_graph = None
        self._chart = None
        self._full_series = None
        self._selected = {"user0": None, "user1": None}
        self._group_checks: dict = {}
        self._method_id = "time_overlap"

    def render_content(self) -> None:
        edges_path = self.get_primary_output_parquet_path(OUTPUT_EDGES)
        posts_path = self.get_primary_output_parquet_path(OUTPUT_POSTS)
        if not edges_path or not posts_path:
            ui.label("No time-analysis outputs found for this run.").classes(
                "text-negative"
            )
            return

        analysis = self.session.current_analysis
        params = (
            getattr(analysis, "param_values", None)
            or getattr(self.session, "analysis_params", None)
            or {}
        )
        if isinstance(params, dict):
            self._method_id = str(params.get(PARAM_METHOD, "time_overlap"))

        edges = pl.read_parquet(edges_path)
        posts = pl.read_parquet(posts_path)
        posts_df = posts.to_pandas()
        if "rel_timestamp" not in posts_df.columns:
            ui.label("Posts table missing rel_timestamp.").classes("text-negative")
            return
        # Graph nodes and select values are strings; keep join keys aligned.
        posts_df[COL_USER_ID] = posts_df[COL_USER_ID].astype(str)

        self._graph = remember_top_edges(graph_from_edges_df(edges))

        method_name = METHOD_LABELS.get(self._method_id, "Time Analysis")
        ui.label(f"{method_name} — Explore network").classes("text-h5")
        ui.label(
            "Select a linked pair from the list or by clicking a line between two nodes, "
            "then compare their overlapping posts."
        ).classes("text-grey-8")

        n_edges = max(self._graph.number_of_edges(), 1)
        slider_max = min(EXPLORE_MAX_PAIRS, n_edges)
        slider_value = min(20, n_edges)

        with ui.row().classes("w-full items-stretch gap-4 flex-wrap"):
            with (
                ui.column()
                .classes("gap-3")
                .style("flex:1 1 220px; min-width:200px; max-width:320px;")
            ):
                self._edge_select = ui.select(
                    options={},
                    label="Select a pair of users",
                    with_input=True,
                ).classes("w-full")
                self._edge_select.on_value_change(
                    lambda e: self._on_edge_selected_from_list(e.value)
                )

                self._selection_label = ui.label("Users Selected: —").classes(
                    "text-body2 text-grey-8"
                )
                self._inspect_button = ui.button(
                    "Compare users", on_click=self._show_compare
                ).props("unelevated")
                self._inspect_button.disable()

            with ui.column().classes("gap-2").style("flex:3 1 360px; min-width:280px;"):
                self._slider = (
                    ui.slider(min=1, max=slider_max, value=slider_value)
                    .classes("w-full")
                    .on(
                        "update:model-value",
                        lambda e: self._on_slider(int(e.args)),
                        throttle=0.4,
                        leading_events=False,
                    )
                )
                ui.label("Filter by group size.").classes("text-caption text-grey-7")
                self._group_checks = {}
                with ui.row().classes(
                    "items-center gap-4 q-mb-sm flex-wrap justify-center"
                ):
                    for key, color, label in EDGE_COLOR_LEGEND:
                        with ui.row().classes("items-center gap-1"):
                            cb = ui.checkbox(
                                value=True,
                                on_change=lambda _e: self._apply_visibility(),
                            ).props("dense")
                            ui.element("div").style(
                                f"width:18px;height:4px;border-radius:2px;"
                                f"background:{color};"
                            )
                            ui.label(label).classes("text-caption text-grey-7")
                            self._group_checks[key] = cb

                self._chart_slot = ui.column().classes("w-full")

        self._refresh_chart(int(self._slider.value))

    def _visible_edge_groups(self) -> set[str]:
        if not self._group_checks:
            return set(ALL_EDGE_GROUPS)
        return {
            key for key, cb in self._group_checks.items() if getattr(cb, "value", True)
        }

    def _apply_visibility(self) -> None:
        if self._chart is None or self._full_series is None:
            return
        series = apply_edge_group_visibility(
            self._full_series, self._visible_edge_groups()
        )
        self._chart.options["series"] = series
        self._chart.update()

    def _on_slider(self, num_top: int) -> None:
        self._refresh_chart(num_top)

    def _refresh_chart(self, num_top: int) -> None:
        if self._graph is None:
            return
        self._cut_graph = cut_graph_by_weight(self._graph, num_top)
        series = plot_subgraph_echart(self._cut_graph)
        self._full_series = series
        options = {f"{u}\t{v}": f"{u}  ↔  {v}" for u, v in self._cut_graph.edges()}
        self._edge_select.set_options(options)
        self._edge_select.set_value(None)
        self._selected["user0"] = None
        self._selected["user1"] = None
        self._selection_label.set_text("Users Selected: —")
        self._inspect_button.disable()
        if options:
            self._edge_select.enable()
        else:
            self._edge_select.disable()

        self._chart_slot.clear()
        with self._chart_slot:
            self._chart = (
                ui.echart(
                    {
                        "tooltip": {"show": False},
                        "series": apply_edge_group_visibility(
                            series, self._visible_edge_groups()
                        ),
                    }
                )
                .classes("w-full")
                .style("display:block; width:100%; min-width:100%; height:520px;")
            )
            # NiceGUI ECharts events are namespaced as chart:* (not bare "click").
            self._chart.on(
                "chart:click",
                self._on_chart_click,
                js_handler=NETWORK_CLICK_JS,
            )
            self._chart.on(
                "chart:mouseover",
                js_handler=network_hover_show_labels_js(self._chart.id),
            )
            self._chart.on(
                "chart:globalout",
                js_handler=network_hover_clear_labels_js(self._chart.id),
            )
            ui.timer(0.05, lambda: self._chart.run_chart_method("resize"), once=True)
            ui.timer(0.25, lambda: self._chart.run_chart_method("resize"), once=True)

    def _cut_graph_nodes(self) -> list | None:
        if self._cut_graph is None:
            return None
        return list(self._cut_graph.nodes())

    def _sync_edge_select_value(self, user0: str, user1: str) -> None:
        options = self._edge_select.options or {}
        key = f"{user0}\t{user1}"
        alt = f"{user1}\t{user0}"
        if key in options:
            self._edge_select.set_value(key)
        elif alt in options:
            self._edge_select.set_value(alt)

    def _select_user_pair(self, user0: str, user1: str) -> None:
        self._selected["user0"] = user0
        self._selected["user1"] = user1
        self._sync_edge_select_value(user0, user1)
        self._selection_label.set_text(f"Users Selected: {user0} and {user1}")
        self._inspect_button.enable()

    def _on_edge_selected_from_list(self, value) -> None:
        if not value or "\t" not in str(value):
            return
        user0, user1 = str(value).split("\t", 1)
        if (self._selected["user0"] == user0 and self._selected["user1"] == user1) or (
            self._selected["user0"] == user1 and self._selected["user1"] == user0
        ):
            self._selection_label.set_text(f"Users Selected: {user0} and {user1}")
            self._inspect_button.enable()
            return
        self._select_user_pair(user0, user1)

    def _on_chart_click(self, e: GenericEventArguments) -> None:
        users = users_from_edge_payload(e.args, self._cut_graph_nodes())
        if users is None:
            if isinstance(e.args, dict) and e.args.get("dataType") == "node":
                ui.notify(
                    "Click a connecting line between two users, or use the list on the left."
                )
            return
        user0, user1 = users
        self._select_user_pair(user0, user1)

    def _show_compare(self) -> None:
        user0 = self._selected["user0"]
        user1 = self._selected["user1"]
        if not user0 or not user1:
            ui.notify("Select a user link first.")
            return
        self.session.time_analysis_compare_user0 = str(user0)
        self.session.time_analysis_compare_user1 = str(user1)
        self.navigate_to(gui_routes.dashboard_time_analysis_compare)
