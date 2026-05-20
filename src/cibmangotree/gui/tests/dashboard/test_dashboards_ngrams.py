"""Behavior tests for gui.dashboards.ngrams.NgramsDashboardPage."""

from gui.dashboards.base_dashboard import BaseDashboardPage
from gui.dashboards.ngrams import NgramsDashboardPage


def test_ngrams_dashboard_extends_base_dashboard() -> None:
    assert issubclass(NgramsDashboardPage, BaseDashboardPage)
