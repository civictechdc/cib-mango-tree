"""Unit tests for time-coordination core (ported from cib-time-analysis)."""

from datetime import datetime, timedelta

import numpy as np
import pandas as pd
import pytest

from cibmangotree.analyzers.time_coordination.graph_utils import (
    cut_graph_by_weight,
    ranked_edges,
    remember_top_edges,
)
from cibmangotree.analyzers.time_coordination.time_coordination_base import analysis


class _Progress:
    def __init__(self):
        self.value = 0.0


@pytest.fixture
def sample_prepared(tmp_path):
    path = tmp_path / "sample.csv"
    start = datetime(2024, 1, 1, 0, 0, 0)
    rows = [
        "created_at,account.username,content_cleaned",
        f"{start},alice,a1",
        f"{start + timedelta(seconds=10)},bob,b1",
        f"{start + timedelta(seconds=20)},alice,a2",
        f"{start + timedelta(seconds=25)},bob,b2",
        f"{start + timedelta(seconds=300)},carol,c1",
        f"{start + timedelta(seconds=305)},dave,d1",
    ]
    path.write_text("\n".join(rows) + "\n", encoding="utf-8")
    return analysis.DatasetSpec(
        str(path), "created_at", "account.username", "content_cleaned"
    )


def test_read_csv_adds_relative_timestamps_and_sorts(sample_prepared):
    csv_df, time_data = analysis.read_csv(*sample_prepared)
    assert len(csv_df) == 6
    assert len(time_data) == 6
    assert "rel_timestamp" in csv_df.columns
    assert csv_df["rel_timestamp"].iloc[0] == 0
    assert list(csv_df["rel_timestamp"]) == sorted(csv_df["rel_timestamp"])


def test_read_csv_drops_incomplete_rows(tmp_path):
    path = tmp_path / "sparse.csv"
    path.write_text(
        "\n".join(
            [
                "created_at,account.username,content_cleaned",
                "2024-01-01 00:00:00,alice,ok",
                "2024-01-01 00:00:10,,missing-user",
                "2024-01-01 00:00:20,bob,",
                "",
            ]
        ),
        encoding="utf-8",
    )
    csv_df, _ = analysis.read_csv(
        str(path), "created_at", "account.username", "content_cleaned"
    )
    assert len(csv_df) == 1
    assert csv_df["account.username"].iloc[0] == "alice"


def test_get_tvec_marks_post_times():
    df = pd.DataFrame(
        {
            "account.username": ["alice", "bob", "alice"],
            "rel_timestamp": [0, 1, 3],
        }
    )
    tvec, num_posts = analysis.get_tvec("alice", df, "account.username", t_step=1)
    assert num_posts == 2
    assert tvec.tolist() == [1, 0, 0, 1]


def test_sliding_window_connects_co_active_users(sample_prepared):
    progress = _Progress()
    G = analysis.sliding_window(sample_prepared, progress, win_size=2, t_step=60)
    assert G.has_edge("alice", "bob")
    assert progress.value == 1.0 or progress.value > 0


def test_ado_window_connects_co_active_users(sample_prepared):
    progress = _Progress()
    G = analysis.ado_window(sample_prepared, progress, win_size=2, t_step=60)
    assert G.has_edge("alice", "bob")


def test_time_overlap_respects_min_posts(sample_prepared):
    progress = _Progress()
    G = analysis.time_overlap(
        sample_prepared, progress, win_size=2, t_step=60, min_posts=1
    )
    assert G.number_of_nodes() >= 2


def test_overlapping_content_for_users(sample_prepared):
    csv_df, _ = analysis.read_csv(*sample_prepared)
    items = analysis.overlapping_content_for_users(
        "alice",
        "bob",
        csv_df,
        "account.username",
        "content_cleaned",
        "created_at",
        dt=60,
    )
    assert items
    users = {row[0] for row in items}
    assert users <= {"alice", "bob"}


def test_ranked_and_cut_graph(sample_prepared):
    progress = _Progress()
    G = analysis.sliding_window(sample_prepared, progress, win_size=2, t_step=60)
    remember_top_edges(G, limit=10)
    cut = cut_graph_by_weight(G, 2)
    assert cut.number_of_edges() <= 2
    assert len(ranked_edges(G, 5)) <= 5


def test_methods_order():
    assert analysis.METHODS == {
        "sliding_window": analysis.sliding_window,
        "ado_window": analysis.ado_window,
        "time_overlap": analysis.time_overlap,
    }


def test_prepare_dataframe_from_datetime():
    df = pd.DataFrame(
        {
            "user_id": ["a", "b"],
            "timestamp": pd.to_datetime(["2024-01-01 00:00:00", "2024-01-01 00:01:00"]),
            "message_text": ["x", "y"],
        }
    )
    prepared = analysis.prepare_dataframe(df, "timestamp", "user_id", "message_text")
    assert list(prepared.df["rel_timestamp"]) == [0.0, 60.0]
    assert np.isclose(prepared.df["rel_timestamp"].iloc[1], 60.0)
