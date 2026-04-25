"""
Dashboard pages for the NiceGUI GUI.

Each analyzer that produces results has a corresponding dashboard module here.
All dashboard pages inherit from BaseDashboardPage, which extends GuiPage.

Modules:
    base_dashboard: BaseDashboardPage abstract base class
    ngrams: NgramsDashboardPage for the n-grams analyzer
    hashtags: HashtagsDashboardPage for the hashtags analyzer
    temporal: TemporalDashboardPage for the temporal analyzer  (planned)
"""

from .base_dashboard import BaseDashboardPage
from .hashtags import HashtagsDashboardPage
from .ngrams import NgramsDashboardPage

__all__ = [
    "BaseDashboardPage",
    "HashtagsDashboardPage",
    "NgramsDashboardPage",
]
