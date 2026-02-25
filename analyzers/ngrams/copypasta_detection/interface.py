from analyzer_interface import (
    AnalyzerOutput,
    AnalyzerParam,
    OutputColumn,
    SecondaryAnalyzerInterface,
)
from analyzer_interface.params import BooleanParam

from ..ngrams_base import interface as ngrams_interface
from ..ngrams_base.interface import (
    COL_AUTHOR_ID,
    COL_MESSAGE_SURROGATE_ID,
    COL_MESSAGE_TEXT,
)

# Output IDs
OUTPUT_COPYPASTA_NODES = "copypasta_nodes"
OUTPUT_COPYPASTA_EDGES = "copypasta_edges"
OUTPUT_COPYPASTA_SUMMARY = "copypasta_summary"

# Node/edge column names
COL_CLUSTER_ID = "cluster_id"
COL_SOURCE_ID = "source_id"
COL_TARGET_ID = "target_id"

# Summary column names
COL_TOTAL_CLUSTERS = "total_clusters"
COL_TOTAL_REPEATED_MESSAGES = "total_repeated_messages"
COL_UNIQUE_AUTHORS = "unique_authors_involved"
COL_LARGEST_CLUSTER_SIZE = "largest_cluster_size"

# Parameter IDs
PARAM_CROSS_AUTHOR_ONLY = "cross_author_only"

interface = SecondaryAnalyzerInterface(
    id="copypasta_detection",
    version="0.2.0",
    name="Copypasta Detection",
    short_description="Detects repeated messages across accounts using exact text matching",
    long_description="""
Identifies groups of messages that contain identical text (after normalization),
indicating copied or pasted content. Outputs graph-compatible node and edge tables
so users can browse which posts repeat and which accounts posted them.

This is useful for detecting coordinated inauthentic behavior where multiple
accounts post the same content verbatim.

Normalization includes: lowercasing, Unicode normalization, and collapsing
whitespace — so minor formatting differences do not prevent matching.
    """,
    base_analyzer=ngrams_interface,
    outputs=[
        AnalyzerOutput(
            id=OUTPUT_COPYPASTA_NODES,
            name="Repeated message nodes",
            description="Messages involved in repeated content, for use as graph nodes",
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
                    human_readable_name="Message Text",
                ),
            ],
        ),
        AnalyzerOutput(
            id=OUTPUT_COPYPASTA_EDGES,
            name="Repeated message edges",
            description="Pairwise connections between messages with identical text, for use as graph edges",
            columns=[
                OutputColumn(
                    name=COL_SOURCE_ID,
                    data_type="identifier",
                    human_readable_name="Source Message ID",
                ),
                OutputColumn(
                    name=COL_TARGET_ID,
                    data_type="identifier",
                    human_readable_name="Target Message ID",
                ),
                OutputColumn(
                    name=COL_CLUSTER_ID,
                    data_type="identifier",
                    human_readable_name="Cluster ID",
                ),
            ],
        ),
        AnalyzerOutput(
            id=OUTPUT_COPYPASTA_SUMMARY,
            name="Copypasta summary statistics",
            description="Aggregate statistics about detected repeated content",
            columns=[
                OutputColumn(
                    name=COL_TOTAL_CLUSTERS,
                    data_type="integer",
                    human_readable_name="Total Clusters",
                ),
                OutputColumn(
                    name=COL_TOTAL_REPEATED_MESSAGES,
                    data_type="integer",
                    human_readable_name="Total Repeated Messages",
                ),
                OutputColumn(
                    name=COL_UNIQUE_AUTHORS,
                    data_type="integer",
                    human_readable_name="Unique Authors Involved",
                ),
                OutputColumn(
                    name=COL_LARGEST_CLUSTER_SIZE,
                    data_type="integer",
                    human_readable_name="Largest Cluster Size",
                ),
            ],
        ),
    ],
    params=[
        AnalyzerParam(
            id=PARAM_CROSS_AUTHOR_ONLY,
            human_readable_name="Cross-Author Only",
            description="Only flag clusters where the repeated message comes from more than one author",
            type=BooleanParam(),
            default=True,
        ),
    ],
)
