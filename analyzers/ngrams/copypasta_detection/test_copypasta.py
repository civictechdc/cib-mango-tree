"""
Tests for copypasta detection secondary analyzer.

Tests cover:
- Exact duplicate detection across authors
- Text normalization (case, whitespace)
- Cross-author filtering
- Graph edge generation
- Empty inputs
"""

import polars as pl

from .interface import (
    COL_CLUSTER_ID,
    COL_SOURCE_ID,
    COL_TARGET_ID,
)
from .main import _build_clusters, _build_edges

COL_MSG_ID = "message_surrogate_id"
COL_AUTHOR = "user_id"
COL_TEXT = "message_text"


def _make_messages(rows: list[tuple[int, str, str]]) -> pl.DataFrame:
    """Helper: create a messages DataFrame from (surrogate_id, author_id, text) tuples."""
    return pl.DataFrame(
        {
            COL_MSG_ID: [r[0] for r in rows],
            COL_AUTHOR: [r[1] for r in rows],
            COL_TEXT: [r[2] for r in rows],
        }
    )


class TestExactMatchClustering:
    def test_exact_duplicates(self):
        """Two messages with identical text from different authors form one cluster."""
        df = _make_messages(
            [
                (1, "alice", "hello world"),
                (2, "bob", "hello world"),
            ]
        )
        result = _build_clusters(df, cross_author_only=True)
        assert result.height == 2
        assert result[COL_CLUSTER_ID].n_unique() == 1

    def test_normalization_case(self):
        """Case differences are collapsed — 'Hello World' and 'hello world' form the same cluster."""
        df = _make_messages(
            [
                (1, "alice", "Hello World"),
                (2, "bob", "hello world"),
            ]
        )
        result = _build_clusters(df, cross_author_only=True)
        assert result.height == 2
        assert result[COL_CLUSTER_ID].n_unique() == 1

    def test_normalization_whitespace(self):
        """Extra whitespace is collapsed — messages differing only in spacing form the same cluster."""
        df = _make_messages(
            [
                (1, "alice", "hello  world"),
                (2, "bob", "hello world"),
            ]
        )
        result = _build_clusters(df, cross_author_only=True)
        assert result.height == 2
        assert result[COL_CLUSTER_ID].n_unique() == 1

    def test_no_repetition(self):
        """All unique messages produce empty output."""
        df = _make_messages(
            [
                (1, "alice", "message one"),
                (2, "bob", "message two"),
                (3, "carol", "message three"),
            ]
        )
        result = _build_clusters(df, cross_author_only=True)
        assert result.height == 0

    def test_cross_author_filter_excludes_same_author(self):
        """With cross_author_only=True, clusters where only one author posted are excluded."""
        df = _make_messages(
            [
                (1, "alice", "repeated message"),
                (2, "alice", "repeated message"),
            ]
        )
        result = _build_clusters(df, cross_author_only=True)
        assert result.height == 0

    def test_cross_author_filter_off_keeps_same_author(self):
        """With cross_author_only=False, same-author duplicates are included."""
        df = _make_messages(
            [
                (1, "alice", "repeated message"),
                (2, "alice", "repeated message"),
            ]
        )
        result = _build_clusters(df, cross_author_only=False)
        assert result.height == 2

    def test_multiple_clusters(self):
        """Two distinct repeated messages produce two separate clusters."""
        df = _make_messages(
            [
                (1, "alice", "first repeated"),
                (2, "bob", "first repeated"),
                (3, "carol", "second repeated"),
                (4, "dave", "second repeated"),
                (5, "eve", "unique message"),
            ]
        )
        result = _build_clusters(df, cross_author_only=True)
        assert result.height == 4
        assert result[COL_CLUSTER_ID].n_unique() == 2

    def test_empty_input(self):
        """Empty input produces empty output."""
        df = pl.DataFrame(
            schema={
                COL_MSG_ID: pl.Int64,
                COL_AUTHOR: pl.Utf8,
                COL_TEXT: pl.Utf8,
            }
        )
        result = _build_clusters(df, cross_author_only=True)
        assert result.height == 0


class TestGraphEdges:
    def test_two_message_cluster_produces_one_edge(self):
        """A cluster of 2 messages produces exactly 1 edge."""
        df_nodes = pl.DataFrame(
            {
                COL_CLUSTER_ID: [0, 0],
                COL_MSG_ID: [1, 2],
                COL_AUTHOR: ["alice", "bob"],
                COL_TEXT: ["hello", "hello"],
            }
        )
        edges = _build_edges(df_nodes)
        assert edges.height == 1
        assert edges[COL_SOURCE_ID][0] == 1
        assert edges[COL_TARGET_ID][0] == 2

    def test_three_message_cluster_produces_three_edges(self):
        """A cluster of 3 messages produces 3 pairwise edges."""
        df_nodes = pl.DataFrame(
            {
                COL_CLUSTER_ID: [0, 0, 0],
                COL_MSG_ID: [1, 2, 3],
                COL_AUTHOR: ["alice", "bob", "carol"],
                COL_TEXT: ["x", "x", "x"],
            }
        )
        edges = _build_edges(df_nodes)
        assert edges.height == 3
        assert (edges[COL_CLUSTER_ID] == 0).all()

    def test_separate_clusters_do_not_cross(self):
        """Edges are never generated across different clusters."""
        df_nodes = pl.DataFrame(
            {
                COL_CLUSTER_ID: [0, 0, 1, 1],
                COL_MSG_ID: [1, 2, 3, 4],
                COL_AUTHOR: ["alice", "bob", "carol", "dave"],
                COL_TEXT: ["a", "a", "b", "b"],
            }
        )
        edges = _build_edges(df_nodes)
        assert edges.height == 2
        cluster_ids = set(edges[COL_CLUSTER_ID].to_list())
        assert cluster_ids == {0, 1}

    def test_no_duplicate_edges(self):
        """Each pair appears exactly once (source_id < target_id)."""
        df_nodes = pl.DataFrame(
            {
                COL_CLUSTER_ID: [0, 0, 0],
                COL_MSG_ID: [10, 20, 30],
                COL_AUTHOR: ["a", "b", "c"],
                COL_TEXT: ["x", "x", "x"],
            }
        )
        edges = _build_edges(df_nodes)
        assert edges.height == 3
        assert (edges[COL_SOURCE_ID] < edges[COL_TARGET_ID]).all()

    def test_empty_nodes_produces_empty_edges(self):
        """Empty nodes table produces empty edges."""
        df_nodes = pl.DataFrame(
            schema={
                COL_CLUSTER_ID: pl.Int64,
                COL_MSG_ID: pl.Int64,
                COL_AUTHOR: pl.Utf8,
                COL_TEXT: pl.Utf8,
            }
        )
        edges = _build_edges(df_nodes)
        assert edges.height == 0
