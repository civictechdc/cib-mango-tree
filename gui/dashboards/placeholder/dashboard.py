"""
Placeholder dashboard shown when an analyzer has no dashboard yet.
"""

from nicegui import ui

from gui.session import GuiSession

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
            ui.icon("bar_chart", size="4rem").classes("text-grey-5")
            ui.label("Dashboard coming soon").classes("text-h6 text-grey-6 q-mt-md")
            ui.label(
                "A results dashboard for this analyzer is not yet available."
            ).classes("text-grey-5")
