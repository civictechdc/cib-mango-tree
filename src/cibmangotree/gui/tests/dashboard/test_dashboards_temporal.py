"""Behavior tests for gui.dashboards.temporal.TemporalDashboardPage."""

from datetime import time

import polars as pl

from cibmangotree.analyzers.temporal.temporal_base.interface import (
    OUTPUT_COL_POST_COUNT,
    OUTPUT_COL_TIME_INTERVAL_END,
    OUTPUT_COL_TIME_INTERVAL_START,
)
from cibmangotree.gui.dashboards.base_dashboard import BaseDashboardPage
from cibmangotree.gui.dashboards.temporal import TemporalDashboardPage
from cibmangotree.gui.dashboards.temporal.plots import plot_temporal_bar_echart


def test_temporal_dashboard_extends_base_dashboard() -> None:
    assert issubclass(TemporalDashboardPage, BaseDashboardPage)


def test_plot_temporal_bar_labels_and_counts() -> None:
    df = pl.DataFrame(
        {
            OUTPUT_COL_TIME_INTERVAL_START: [time(8, 0), time(14, 0)],
            OUTPUT_COL_TIME_INTERVAL_END: [time(9, 0), time(15, 0)],
            OUTPUT_COL_POST_COUNT: [3, 1],
        }
    )
    option = plot_temporal_bar_echart(df)

    assert option["xAxis"]["data"] == ["08:00-09:00", "14:00-15:00"]
    assert option["series"][0]["data"] == [3, 1]
