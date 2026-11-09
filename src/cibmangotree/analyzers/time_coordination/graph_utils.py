"""Weight-based graph cutting helpers.

Ported from cib-time-analysis ``modules/my_graph.py`` — pure graph helpers only
(no NiceGUI session / dataset-index wiring).
"""

from __future__ import annotations

import networkx as nx

EXPLORE_MAX_PAIRS = 100
TOP_EDGES_KEY = "top_edges"
RANK_PROGRESS_EVERY = 5000


def ranked_edges(G, limit):
    """Strongest edges first, capped at limit. Does not copy G."""
    ranked = sorted(
        G.edges(data=True),
        key=lambda edge: edge[2].get("norm_weight", 0.0),
        reverse=True,
    )
    return ranked[:limit]


def remember_top_edges(G, limit=EXPLORE_MAX_PAIRS, progress=None):
    """Store the strongest links on ``G`` for Explore to slice."""
    total = G.number_of_edges()
    scanned = []
    for i, (u, v, data) in enumerate(G.edges(data=True), start=1):
        scanned.append((data.get("norm_weight", 0.0), u, v, data))
        if progress is not None and total and i % RANK_PROGRESS_EVERY == 0:
            progress.value = i / total
    scanned.sort(key=lambda item: item[0], reverse=True)
    G.graph[TOP_EDGES_KEY] = [(u, v, data) for _weight, u, v, data in scanned[:limit]]
    if progress is not None:
        progress.value = 1.0
    return G


def cut_graph_by_weight(G, num_top):
    """Build a small graph of the strongest ``num_top`` links."""
    ranked = G.graph.get(TOP_EDGES_KEY)
    chosen = ranked[:num_top] if ranked is not None else ranked_edges(G, num_top)
    cut = nx.Graph()
    for u, v, data in chosen:
        cut.add_edge(u, v, **data)
    return cut


def graph_from_edges_df(edges_df) -> nx.Graph:
    """Rebuild a NetworkX graph from the primary ``edges`` parquet/table."""
    G = nx.Graph()
    for row in edges_df.iter_rows(named=True):
        G.add_edge(
            row["user_a"],
            row["user_b"],
            weight=float(row["weight"]),
            norm_weight=float(row["norm_weight"]),
        )
    return G
