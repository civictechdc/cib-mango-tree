"""Behavior tests for gui.components.analysis_utils."""

from datetime import datetime, timedelta
from unittest.mock import MagicMock

from gui.components.analysis_utils import analysis_label, present_timestamp


def test_present_timestamp_just_now() -> None:
    now = datetime(2025, 1, 1, 12, 0, 2)
    past = datetime(2025, 1, 1, 12, 0, 1)
    assert present_timestamp(past, now) == "just now"


def test_analysis_label_includes_suffix_when_timestamp_set() -> None:
    now = datetime(2025, 1, 15, 12, 0, 0)
    analysis = MagicMock()
    analysis.display_name = "Run A"
    analysis.create_time = now - timedelta(days=10)

    label = analysis_label(analysis, now)
    assert label.startswith("Run A")
