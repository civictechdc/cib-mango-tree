"""Behavior tests for gui.components.analysis.AnalysisParamsCard."""

import pytest
from nicegui import ui

from gui.components.analysis import AnalysisParamsCard


@pytest.mark.asyncio
async def test_analysis_params_card_empty_shows_message(user) -> None:
    @ui.page("/analysis-card")
    def page() -> None:
        AnalysisParamsCard(params=[], default_values={})

    await user.open("/analysis-card")
    await user.should_see("no configurable parameters")
