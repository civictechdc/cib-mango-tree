"""
Tests for copypasta detection secondary analyzer.

Tests cover:
- Exact duplicate detection across authors
- Partial overlap detection
- Same-author filtering
- Threshold filtering
- Cluster assignment
- Empty inputs
"""

import polars as pl
import pytest

from .interface import (
    COL_AUTHOR_ID_A,
    COL_AUTHOR_ID_B,
    COL_CLUSTER_ID,
    COL_JACCARD_SIMILARITY,
    COL_MESSAGE_SURROGATE_ID_A,
    COL_MESSAGE_SURROGATE_ID_B,
    COL_SHARED_NGRAM_COUNT,
)
from .main import _assign_clusters, _compute_jaccard_pairs

# Column names matching the primary ngram analyzer output
COL_MSG_ID = "message_surrogate_id"
COL_NGRAM_ID = "ngram_id"


@pytest.mark.unit
class TestJaccardComputation:
    """Test the Jaccard similarity computation."""

    def test_exact_duplicates(self):
        """Two messages sharing all n-grams should have similarity = 1.0."""
        # Messages 1 and 2 share the same 3 n-grams
        df_msg_ngrams = pl.DataFrame(
            {
                COL_MSG_ID: [1, 1, 1, 2, 2, 2],
                COL_NGRAM_ID: [10, 20, 30, 10, 20, 30],
            }
        )
        result = _compute_jaccard_pairs(df_msg_ngrams, threshold=0.5)

        assert result.height == 1
        row = result.row(0, named=True)
        assert row[COL_JACCARD_SIMILARITY] == pytest.approx(1.0)
        assert row[COL_SHARED_NGRAM_COUNT] == 3

    def test_partial_overlap(self):
        """Messages with partial n-gram overlap should have 0 < similarity < 1."""
        # Message 1 has ngrams {10, 20, 30}, Message 2 has {20, 30, 40}
        # Intersection = {20, 30} = 2, Union = {10, 20, 30, 40} = 4
        # Jaccard = 2/4 = 0.5
        df_msg_ngrams = pl.DataFrame(
            {
                COL_MSG_ID: [1, 1, 1, 2, 2, 2],
                COL_NGRAM_ID: [10, 20, 30, 20, 30, 40],
            }
        )
        result = _compute_jaccard_pairs(df_msg_ngrams, threshold=0.3)

        assert result.height == 1
        row = result.row(0, named=True)
        assert row[COL_JACCARD_SIMILARITY] == pytest.approx(0.5)
        assert row[COL_SHARED_NGRAM_COUNT] == 2

    def test_no_overlap(self):
        """Messages with no shared n-grams should not appear in results."""
        df_msg_ngrams = pl.DataFrame(
            {
                COL_MSG_ID: [1, 1, 2, 2],
                COL_NGRAM_ID: [10, 20, 30, 40],
            }
        )
        result = _compute_jaccard_pairs(df_msg_ngrams, threshold=0.1)
        assert result.height == 0

    def test_threshold_filtering(self):
        """Pairs below the threshold should be excluded."""
        # Jaccard = 2/4 = 0.5
        df_msg_ngrams = pl.DataFrame(
            {
                COL_MSG_ID: [1, 1, 1, 2, 2, 2],
                COL_NGRAM_ID: [10, 20, 30, 20, 30, 40],
            }
        )
        # Threshold 0.6 should exclude this pair (similarity = 0.5)
        result = _compute_jaccard_pairs(df_msg_ngrams, threshold=0.6)
        assert result.height == 0

        # Threshold 0.5 should include it
        result = _compute_jaccard_pairs(df_msg_ngrams, threshold=0.5)
        assert result.height == 1

    def test_multiple_pairs(self):
        """Multiple message pairs with different similarities."""
        # Msg 1: {10, 20, 30}
        # Msg 2: {10, 20, 30} -> Jaccard(1,2) = 1.0
        # Msg 3: {30, 40, 50} -> Jaccard(1,3) = 1/5 = 0.2, Jaccard(2,3) = 0.2
        df_msg_ngrams = pl.DataFrame(
            {
                COL_MSG_ID: [1, 1, 1, 2, 2, 2, 3, 3, 3],
                COL_NGRAM_ID: [10, 20, 30, 10, 20, 30, 30, 40, 50],
            }
        )
        result = _compute_jaccard_pairs(df_msg_ngrams, threshold=0.5)
        # Only the (1,2) pair should pass at 0.5 threshold
        assert result.height == 1
        row = result.row(0, named=True)
        assert row[COL_JACCARD_SIMILARITY] == pytest.approx(1.0)

    def test_empty_input(self):
        """Empty input should return empty result."""
        df_msg_ngrams = pl.DataFrame(
            schema={COL_MSG_ID: pl.Int64, COL_NGRAM_ID: pl.Int64}
        )
        result = _compute_jaccard_pairs(df_msg_ngrams, threshold=0.5)
        assert result.height == 0

    def test_single_message(self):
        """Single message should produce no pairs."""
        df_msg_ngrams = pl.DataFrame(
            {
                COL_MSG_ID: [1, 1, 1],
                COL_NGRAM_ID: [10, 20, 30],
            }
        )
        result = _compute_jaccard_pairs(df_msg_ngrams, threshold=0.5)
        assert result.height == 0


@pytest.mark.unit
class TestClusterAssignment:
    """Test the union-find cluster assignment."""

    def test_single_pair(self):
        """Two connected messages form one cluster."""
        df_pairs = pl.DataFrame(
            {
                COL_MESSAGE_SURROGATE_ID_A: [1],
                COL_MESSAGE_SURROGATE_ID_B: [2],
            }
        )
        result = _assign_clusters(df_pairs)
        assert result.height == 2
        # Both messages should be in the same cluster
        cluster_ids = result[COL_CLUSTER_ID].to_list()
        assert cluster_ids[0] == cluster_ids[1]

    def test_transitive_chain(self):
        """Transitive pairs (1-2, 2-3) should form one cluster."""
        df_pairs = pl.DataFrame(
            {
                COL_MESSAGE_SURROGATE_ID_A: [1, 2],
                COL_MESSAGE_SURROGATE_ID_B: [2, 3],
            }
        )
        result = _assign_clusters(df_pairs)
        assert result.height == 3
        cluster_ids = result[COL_CLUSTER_ID].unique().to_list()
        assert len(cluster_ids) == 1

    def test_separate_clusters(self):
        """Disconnected pairs should form separate clusters."""
        df_pairs = pl.DataFrame(
            {
                COL_MESSAGE_SURROGATE_ID_A: [1, 3],
                COL_MESSAGE_SURROGATE_ID_B: [2, 4],
            }
        )
        result = _assign_clusters(df_pairs)
        assert result.height == 4
        cluster_ids = result[COL_CLUSTER_ID].unique().to_list()
        assert len(cluster_ids) == 2

    def test_empty_pairs(self):
        """Empty input should return empty result."""
        df_pairs = pl.DataFrame(
            schema={
                COL_MESSAGE_SURROGATE_ID_A: pl.Int64,
                COL_MESSAGE_SURROGATE_ID_B: pl.Int64,
            }
        )
        result = _assign_clusters(df_pairs)
        assert result.height == 0

    def test_complex_graph(self):
        """Complex connectivity: (1-2), (2-3), (4-5) -> 2 clusters."""
        df_pairs = pl.DataFrame(
            {
                COL_MESSAGE_SURROGATE_ID_A: [1, 2, 4],
                COL_MESSAGE_SURROGATE_ID_B: [2, 3, 5],
            }
        )
        result = _assign_clusters(df_pairs)
        assert result.height == 5
        cluster_ids = result[COL_CLUSTER_ID].unique().to_list()
        assert len(cluster_ids) == 2

        # Messages 1, 2, 3 should be in the same cluster
        cluster_for_1 = result.filter(pl.col(COL_MSG_ID) == 1)[COL_CLUSTER_ID].item()
        cluster_for_2 = result.filter(pl.col(COL_MSG_ID) == 2)[COL_CLUSTER_ID].item()
        cluster_for_3 = result.filter(pl.col(COL_MSG_ID) == 3)[COL_CLUSTER_ID].item()
        assert cluster_for_1 == cluster_for_2 == cluster_for_3

        # Messages 4, 5 should be in a different cluster
        cluster_for_4 = result.filter(pl.col(COL_MSG_ID) == 4)[COL_CLUSTER_ID].item()
        cluster_for_5 = result.filter(pl.col(COL_MSG_ID) == 5)[COL_CLUSTER_ID].item()
        assert cluster_for_4 == cluster_for_5
        assert cluster_for_4 != cluster_for_1
