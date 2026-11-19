"""
Placeholder dashboard shown when an analyzer has no dashboard yet.
"""

from nicegui import ui

from cibmangotree.gui.session import GuiSession
from cibmangotree.gui.theme import (
    COL_PLACEHOLDER,
    ICON_MUTED,
    STYLE_CONTENT_DEFAULT,
    TEXT_PLACEHOLDER_TITLE,
)

from ..base_dashboard import BaseDashboardPage


class PlaceholderDashboard(BaseDashboardPage):
    """Fallback page shown when the selected analyzer has no dashboard yet."""

    def __init__(self, session: GuiSession):
        super().__init__(session=session)

    def render_content(self) -> None:
        with ui.column().classes(COL_PLACEHOLDER).style(STYLE_CONTENT_DEFAULT):
            ui.icon("bar_chart", size="4rem").classes(ICON_MUTED)
            ui.label("Dashboard coming soon").classes(TEXT_PLACEHOLDER_TITLE)
            ui.label(
                "A results dashboard for this analyzer is not yet available."
            ).classes(ICON_MUTED)
