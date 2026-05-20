"""
Dashboard pages for the NiceGUI GUI.

Each analyzer that produces results has a corresponding dashboard module here.
All dashboard pages inherit from BaseDashboardPage, which extends GuiPage.

Modules:
    base_dashboard: BaseDashboardPage abstract base class
    hashtags: HashtagsDashboardPage for the hashtags analyzer
    ngrams: NgramsDashboardPage for the n-grams analyzer
    placeholder: PlaceholderDashboard shown when no dashboard exists yet
    temporal: TemporalDashboardPage for the temporal analyzer  (planned)
"""

from .base_dashboard import BaseDashboardPage
from .hashtags import HashtagsDashboardPage
from .ngrams import NgramsDashboardPage
from .placeholder import PlaceholderDashboard

_DASHBOARD_REGISTRY: dict[str, type[BaseDashboardPage]] = {
    "hashtags": HashtagsDashboardPage,
    "ngrams": NgramsDashboardPage,
}


def get_dashboard(analyzer_id: str | None) -> type[BaseDashboardPage] | None:
    """Look up a registered dashboard class by analyzer ID."""
    return _DASHBOARD_REGISTRY.get(analyzer_id) if analyzer_id else None


__all__ = [
    "BaseDashboardPage",
    "HashtagsDashboardPage",
    "NgramsDashboardPage",
    "PlaceholderDashboard",
    "get_dashboard",
]
