"""Behavior tests for gui.dashboards.ngrams.NgramsDashboardPage."""

from cibmangotree.gui.dashboards.base_dashboard import BaseDashboardPage
from cibmangotree.gui.dashboards.ngrams import NgramsDashboardPage


def test_ngrams_dashboard_extends_base_dashboard() -> None:
    assert issubclass(NgramsDashboardPage, BaseDashboardPage)
