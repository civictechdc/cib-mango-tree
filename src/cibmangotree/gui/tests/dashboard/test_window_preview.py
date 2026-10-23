"""Tests for hashtag time-window preview bins and edges."""

from datetime import datetime, timedelta
from pathlib import Path

import polars as pl

from cibmangotree.analyzer_interface.params import TimeBinningValue
from cibmangotree.gui.dashboards.hashtags.window_preview import (
    activity_bins,
    plot_activity_echart,
    window_edges,
)


def test_activity_bins_cover_every_timestamp_once() -> None:
    start = datetime(2024, 1, 1, 0, 0)
    timestamps = pl.Series(
        [start, start + timedelta(hours=1), start + timedelta(hours=2), None]
    )
    bins = activity_bins(timestamps, bin_count=4)

    assert bins.height == 4
    assert int(bins["count"].sum()) == 3
    assert bins["bin_start"][0] == start


def test_window_edges_follow_datapoint_alignment() -> None:
    start = datetime(2024, 1, 1, 3, 15)
    timestamps = pl.Series(
        [
            start,
            start + timedelta(hours=1),
            start + timedelta(hours=12),
            start + timedelta(hours=25),
        ]
    )
    edges = window_edges(timestamps, TimeBinningValue(unit="hour", amount=12))

    assert edges.starts == [
        start,
        start + timedelta(hours=12),
        start + timedelta(hours=24),
    ]
    assert edges.count == 3


def test_window_edges_omit_lines_when_there_are_too_many() -> None:
    start = datetime(2024, 6, 1, 12, 0, 0)
    timestamps = pl.Series([start + timedelta(seconds=i) for i in range(81)])
    edges = window_edges(
        timestamps, TimeBinningValue(unit="second", amount=1), max_lines=80
    )

    assert edges.count == 81
    assert edges.starts is None

    option = plot_activity_echart(activity_bins(timestamps, bin_count=10), edges)
    assert option["series"][0]["markLine"]["data"] == []
    assert sum(point[1] for point in option["series"][0]["data"]) == 81


def test_sample_twelve_hour_windows_are_drawn() -> None:
    csv_path = (
        Path(__file__).resolve().parents[3]
        / "analyzers"
        / "hashtags"
        / "test_data"
        / "hashtag_test_input.csv"
    )
    timestamps = pl.read_csv(csv_path)["Timestamp"].str.to_datetime()

    twelve_hours = window_edges(timestamps, TimeBinningValue(unit="hour", amount=12))
    one_hour = window_edges(timestamps, TimeBinningValue(unit="hour", amount=1))
    one_minute = window_edges(timestamps, TimeBinningValue(unit="minute", amount=1))

    assert twelve_hours.starts is not None
    assert twelve_hours.count == 27
    assert one_hour.starts is not None
    assert one_minute.starts is None


def test_plot_activity_draws_one_line_per_window() -> None:
    start = datetime(2024, 1, 1, 3, 15)
    timestamps = pl.Series([start, start + timedelta(hours=12)])
    bins = activity_bins(timestamps, bin_count=2)
    edges = window_edges(timestamps, TimeBinningValue(unit="hour", amount=12))
    option = plot_activity_echart(bins, edges)

    assert len(option["series"][0]["markLine"]["data"]) == edges.count
