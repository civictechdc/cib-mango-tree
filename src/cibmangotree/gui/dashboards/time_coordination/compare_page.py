"""Time coordination Compare users screen (separate from Explore network)."""

from __future__ import annotations

import asyncio

import polars as pl
from nicegui import ui

from cibmangotree.analyzers.time_coordination.time_coordination_base.analysis import (
    overlapping_content_for_users,
)
from cibmangotree.analyzers.time_coordination.time_coordination_base.interface import (
    COL_MESSAGE_TEXT,
    COL_TIMESTAMP,
    COL_USER_ID,
    OUTPUT_POSTS,
    PARAM_T_STEP,
    PARAM_WIN_SIZE,
)
from cibmangotree.gui.routes import gui_routes
from cibmangotree.gui.session import GuiSession
from cibmangotree.gui.theme import (
    ROW_LOADING,
    SCROLL_PAIR,
    TEXT_BODY_MUTED,
    TEXT_BODY_NEGATIVE,
    TEXT_CAPTION_MUTED,
    TEXT_H5,
    TEXT_NEGATIVE,
)

from ..base_dashboard import BaseDashboardPage
from .compare import format_post_body


class TimeCoordinationComparePage(BaseDashboardPage):
    """Interleaved overlapping posts for a pair selected on Explore."""

    _secondary_analyzer_id = None

    def __init__(self, session: GuiSession):
        super().__init__(session=session)
        self.route = gui_routes.dashboard_time_coordination_compare
        self.back_route = gui_routes.dashboard
        self.back_text = "Back to network"
        self.title = "Time Coordination: Compare users"

    def render_content(self) -> None:
        user0 = self.session.time_coordination_compare_user0
        user1 = self.session.time_coordination_compare_user1
        if not user0 or not user1:
            ui.label("No user pair selected.").classes(TEXT_NEGATIVE)
            ui.button(
                "Back to network",
                on_click=lambda: self.navigate_to(gui_routes.dashboard),
            ).props("unelevated")
            return

        posts_path = self.get_primary_output_parquet_path(OUTPUT_POSTS)
        if not posts_path:
            ui.label("No time-coordination posts found for this run.").classes(
                TEXT_NEGATIVE
            )
            return

        analysis = self.session.current_analysis
        params = (
            getattr(analysis, "param_values", None)
            or getattr(self.session, "analysis_params", None)
            or {}
        )
        win_size = 2
        t_step = 300
        if isinstance(params, dict):
            win_size = int(params.get(PARAM_WIN_SIZE, 2))
            t_step = int(params.get(PARAM_T_STEP, 300))
        dt = int(win_size * t_step)

        posts = pl.read_parquet(posts_path).to_pandas()
        if "rel_timestamp" not in posts.columns:
            ui.label("Posts table missing rel_timestamp.").classes(TEXT_NEGATIVE)
            return
        posts[COL_USER_ID] = posts[COL_USER_ID].astype(str)

        ui.label(f"{user0}  ↔  {user1}").classes(TEXT_H5)
        meta = ui.label("").classes(TEXT_CAPTION_MUTED)
        with ui.row().classes(ROW_LOADING) as loading:
            ui.spinner(size="lg")
            ui.label("Loading interleaved posts…").classes(TEXT_BODY_MUTED)
        scroll = ui.scroll_area().classes(SCROLL_PAIR)

        async def _load() -> None:
            await asyncio.sleep(0)
            try:
                items = overlapping_content_for_users(
                    user0,
                    user1,
                    posts,
                    COL_USER_ID,
                    COL_MESSAGE_TEXT,
                    COL_TIMESTAMP,
                    dt,
                )
                if items:
                    overlap0 = sum(1 for u, _c, _t in items if str(u) == user0)
                    overlap1 = sum(1 for u, _c, _t in items if str(u) == user1)
                    meta.set_text(
                        f"{user0}: {overlap0} overlapping · "
                        f"{user1}: {overlap1} overlapping · "
                        f"window {dt}s"
                    )
                scroll.clear()
                with scroll:
                    if not items:
                        ui.label(
                            "No posts fall within an overlapping time window "
                            "for this pair (window duration = time step × window size)."
                        ).classes(TEXT_BODY_MUTED)
                    else:
                        for user, content, stamp in items:
                            ui.chat_message(
                                format_post_body(content, stamp),
                                name=str(user),
                                sent=str(user) == user0,
                            )
            except Exception as exc:
                scroll.clear()
                with scroll:
                    ui.label(
                        f"Could not load overlapping posts for this pair: {exc}"
                    ).classes(TEXT_BODY_NEGATIVE)
            finally:
                loading.visible = False

        ui.timer(0.05, _load, once=True)
