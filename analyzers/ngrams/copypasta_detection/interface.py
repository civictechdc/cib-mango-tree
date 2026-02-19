from analyzer_interface import (
    AnalyzerOutput,
    AnalyzerParam,
    OutputColumn,
    SecondaryAnalyzerInterface,
)
from analyzer_interface.params import BooleanParam, IntegerParam

from ..ngrams_base import interface as ngrams_interface
from ..ngrams_base.interface import (
    COL_AUTHOR_ID,
    COL_MESSAGE_SURROGATE_ID,
    COL_MESSAGE_TEXT,
)

# Output IDs
OUTPUT_COPYPASTA_PAIRS = "copypasta_pairs"
OUTPUT_COPYPASTA_CLUSTERS = "copypasta_clusters"
OUTPUT_COPYPASTA_SUMMARY = "copypasta_summary"

# Output column names
COL_MESSAGE_SURROGATE_ID_A = "message_surrogate_id_a"
COL_MESSAGE_SURROGATE_ID_B = "message_surrogate_id_b"
COL_AUTHOR_ID_A = "author_a"
COL_AUTHOR_ID_B = "author_b"
COL_JACCARD_SIMILARITY = "jaccard_similarity"
COL_SHARED_NGRAM_COUNT = "shared_ngram_count"
COL_TEXT_A = "text_a"
COL_TEXT_B = "text_b"

COL_CLUSTER_ID = "cluster_id"

COL_TOTAL_PAIRS = "total_pairs"
COL_UNIQUE_MESSAGES = "unique_messages_involved"
COL_UNIQUE_AUTHORS = "unique_authors_involved"
COL_AVG_SIMILARITY = "avg_similarity"

# Parameter IDs
PARAM_SIMILARITY_THRESHOLD = "similarity_threshold"
PARAM_CROSS_AUTHOR_ONLY = "cross_author_only"

interface = SecondaryAnalyzerInterface(
    id="copypasta_detection",
    version="0.1.0",
    name="Copypasta Detection",
    short_description="Detects copied/pasted text across messages using n-gram similarity",
    long_description="""
Identifies pairs of messages that share a high proportion of n-grams, indicating
copied or pasted text. Uses Jaccard similarity on n-gram sets to measure overlap.

This is useful for detecting coordinated inauthentic behavior where multiple
accounts post identical or near-identical content.

The similarity threshold controls how similar two messages must be to be flagged.
A threshold of 50% means at least half of the combined unique n-grams must be shared.
    """,
    base_analyzer=ngrams_interface,
    outputs=[
        AnalyzerOutput(
            id=OUTPUT_COPYPASTA_PAIRS,
            name="Copypasta message pairs",
            description="Pairs of messages with high n-gram similarity",
            columns=[
                OutputColumn(
                    name=COL_MESSAGE_SURROGATE_ID_A,
                    data_type="identifier",
                    human_readable_name="Message A ID",
                ),
                OutputColumn(
                    name=COL_MESSAGE_SURROGATE_ID_B,
                    data_type="identifier",
                    human_readable_name="Message B ID",
                ),
                OutputColumn(
                    name=COL_AUTHOR_ID_A,
                    data_type="identifier",
                    human_readable_name="Author A",
                ),
                OutputColumn(
                    name=COL_AUTHOR_ID_B,
                    data_type="identifier",
                    human_readable_name="Author B",
                ),
                OutputColumn(
                    name=COL_JACCARD_SIMILARITY,
                    data_type="float",
                    human_readable_name="Jaccard Similarity",
                ),
                OutputColumn(
                    name=COL_SHARED_NGRAM_COUNT,
                    data_type="integer",
                    human_readable_name="Shared N-grams",
                ),
                OutputColumn(
                    name=COL_TEXT_A,
                    data_type="text",
                    human_readable_name="Text A",
                ),
                OutputColumn(
                    name=COL_TEXT_B,
                    data_type="text",
                    human_readable_name="Text B",
                ),
            ],
        ),
        AnalyzerOutput(
            id=OUTPUT_COPYPASTA_CLUSTERS,
            name="Copypasta clusters",
            description="Groups of messages clustered by shared content",
            columns=[
                OutputColumn(
                    name=COL_CLUSTER_ID,
                    data_type="identifier",
                    human_readable_name="Cluster ID",
                ),
                OutputColumn(
                    name=COL_MESSAGE_SURROGATE_ID,
                    data_type="identifier",
                    human_readable_name="Message ID",
                ),
                OutputColumn(
                    name=COL_AUTHOR_ID,
                    data_type="identifier",
                    human_readable_name="Author",
                ),
                OutputColumn(
                    name=COL_MESSAGE_TEXT,
                    data_type="text",
                    human_readable_name="Text",
                ),
            ],
        ),
        AnalyzerOutput(
            id=OUTPUT_COPYPASTA_SUMMARY,
            name="Copypasta summary statistics",
            description="Aggregate statistics about detected copypasta",
            columns=[
                OutputColumn(
                    name=COL_TOTAL_PAIRS,
                    data_type="integer",
                    human_readable_name="Total Pairs",
                ),
                OutputColumn(
                    name=COL_UNIQUE_MESSAGES,
                    data_type="integer",
                    human_readable_name="Unique Messages",
                ),
                OutputColumn(
                    name=COL_UNIQUE_AUTHORS,
                    data_type="integer",
                    human_readable_name="Unique Authors",
                ),
                OutputColumn(
                    name=COL_AVG_SIMILARITY,
                    data_type="float",
                    human_readable_name="Average Similarity",
                ),
            ],
        ),
    ],
    params=[
        AnalyzerParam(
            id=PARAM_SIMILARITY_THRESHOLD,
            human_readable_name="Similarity Threshold (%)",
            description="Minimum Jaccard similarity percentage to flag a pair (10-100)",
            type=IntegerParam(min=10, max=100),
            default=50,
        ),
        AnalyzerParam(
            id=PARAM_CROSS_AUTHOR_ONLY,
            human_readable_name="Cross-Author Only",
            description="Only flag pairs from different authors",
            type=BooleanParam(),
            default=True,
        ),
    ],
)
