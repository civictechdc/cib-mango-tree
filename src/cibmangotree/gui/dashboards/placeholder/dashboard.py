"""
Placeholder dashboard shown when an analyzer has no dashboard yet.
"""

from nicegui import ui

from cibmangotree.gui.session import GuiSession
from cibmangotree.gui.theme import (
    ICON_DECORATIVE,
    TEXT_HEADING,
    TEXT_MUTED,
)

from ..base_dashboard import BaseDashboardPage


class PlaceholderDashboard(BaseDashboardPage):
    """Fallback page shown when the selected analyzer has no dashboard yet."""

    def __init__(self, session: GuiSession):
        super().__init__(session=session)

    def render_content(self) -> None:
        with (
            ui.column()
            .classes("items-center justify-center")
            .style("height: 80vh; width: 100%")
        ):
            ui.icon("bar_chart", size="4rem").classes(ICON_DECORATIVE)
            ui.label("Dashboard coming soon").classes(
                f"{TEXT_HEADING} {TEXT_MUTED} mt-4"
            )
            ui.label(
                "A results dashboard for this analyzer is not yet available."
            ).classes(TEXT_MUTED)
