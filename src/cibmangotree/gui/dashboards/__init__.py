"""
Dashboard pages for the NiceGUI GUI.

Each analyzer that produces results has a corresponding dashboard module here.
All dashboard pages inherit from BaseDashboardPage, which extends GuiPage.

Modules:
    base_dashboard: BaseDashboardPage abstract base class
    example: ExampleDashboardPage for the tutorial/example analyzer
    hashtags: HashtagsDashboardPage for the hashtags analyzer
    ngrams: NgramsDashboardPage for the n-grams analyzer
    temporal: TemporalDashboardPage for the temporal analyzer
    time_coordination: TimeCoordinationDashboardPage for the time_coordination analyzer
    placeholder: PlaceholderDashboard shown when no dashboard exists yet
"""

from .base_dashboard import BaseDashboardPage
from .example import ExampleDashboardPage
from .hashtags import HashtagsDashboardPage
from .ngrams import NgramsDashboardPage
from .placeholder import PlaceholderDashboard
from .temporal import TemporalDashboardPage
from .time_coordination import TimeCoordinationDashboardPage

_DASHBOARD_REGISTRY: dict[str, type[BaseDashboardPage]] = {
    "__example__": ExampleDashboardPage,
    "hashtags": HashtagsDashboardPage,
    "ngrams": NgramsDashboardPage,
    "temporal": TemporalDashboardPage,
    "time_coordination": TimeCoordinationDashboardPage,
}


def get_dashboard(analyzer_id: str | None) -> type[BaseDashboardPage] | None:
    """Look up a registered dashboard class by analyzer ID."""
    return _DASHBOARD_REGISTRY.get(analyzer_id) if analyzer_id else None


__all__ = [
    "BaseDashboardPage",
    "ExampleDashboardPage",
    "HashtagsDashboardPage",
    "NgramsDashboardPage",
    "PlaceholderDashboard",
    "TemporalDashboardPage",
    "TimeCoordinationDashboardPage",
    "get_dashboard",
]
