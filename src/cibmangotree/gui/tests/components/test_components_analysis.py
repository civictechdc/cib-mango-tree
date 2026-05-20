"""Behavior tests for gui.components.analysis.AnalysisParamsCard."""

from gui.components.analysis import AnalysisParamsCard
from nicegui import ui
from nicegui.testing import User


async def test_analysis_params_card_empty_shows_message(user: User) -> None:
    @ui.page("/analysis-card")
    def page() -> None:
        AnalysisParamsCard(params=[], default_values={})

    await user.open("/analysis-card")
    await user.should_see("no configurable parameters")
