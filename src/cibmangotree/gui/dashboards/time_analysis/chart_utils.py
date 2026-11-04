"""ECharts network plot defaults, click payload helpers, and series builders."""

import networkx as nx

# Slightly above ECharts' default (12) so hovered account names stay readable.
NODE_LABEL_FONT_SIZE = 14

# Edge colors on the displayed (cut) graph, by max endpoint degree N:
# Grey for 1:1 (distinct from default ECharts node blue); warmer colors as N grows.
EDGE_GROUP_PAIR = "pair"
EDGE_GROUP_2_5 = "g2_5"
EDGE_GROUP_6_10 = "g6_10"
EDGE_GROUP_11_20 = "g11_20"

EDGE_COLOR_PAIR = "#B0B7C3"  # N == 1 (light grey)
EDGE_COLOR_GROUP_2_5 = "#1B9E77"  # 2 <= N <= 5 (teal/green)
EDGE_COLOR_GROUP_6_10 = "#D7268A"  # 6 <= N <= 10 (magenta)
EDGE_COLOR_GROUP_11_20 = "#8B2E8B"  # N >= 11 (incl. >20)

# (group_key, color, label) — keys used for visibility toggles.
EDGE_COLOR_LEGEND = (
    (EDGE_GROUP_PAIR, EDGE_COLOR_PAIR, "1:1 pair"),
    (EDGE_GROUP_2_5, EDGE_COLOR_GROUP_2_5, "Group of 2–5"),
    (EDGE_GROUP_6_10, EDGE_COLOR_GROUP_6_10, "Group of 6–10"),
    (EDGE_GROUP_11_20, EDGE_COLOR_GROUP_11_20, "Group of 11–20"),
)

ALL_EDGE_GROUPS = frozenset(key for key, _color, _label in EDGE_COLOR_LEGEND)

ECHART_GRAPH_DEFAULTS = {
    "type": "graph",
    "layout": "force",
    "symbolSize": 28,
    "roam": "scale",  # zoom only — pan/drag was swallowing edge clicks
    "label": {
        "show": False,
        "position": "right",
        "formatter": "{b}",
        "fontSize": NODE_LABEL_FONT_SIZE,
    },
    "edgeLabel": {"show": False},
    "lineStyle": {"opacity": 0.9, "width": 8, "curveness": 0.2},
    "edgeSymbol": ["none", "none"],
    "force": {
        "repulsion": 140,
        "edgeLength": [60, 160],
    },
    "animationDurationUpdate": 0,
    # Dim unrelated nodes/edges on hover; labels are toggled by NETWORK_HOVER_*_JS.
    "emphasis": {
        "focus": "adjacency",
        "lineStyle": {"width": 14},
    },
}

# Browser-side handler for ECharts graph clicks (passed to NiceGUI's js_handler).
# The raw chart:click payload is huge and not JSON-serializable to Python, so this
# strips it down and emit()s only what we need: edge source/target or node name.
NETWORK_CLICK_JS = """
(evt) => {
    if (!evt || evt.componentType !== 'series') return;
    if (evt.dataType === 'edge') {
        const d = evt.data || {};
        emit({
            dataType: 'edge',
            name: evt.name || '',
            source: d.source,
            target: d.target,
        });
    } else if (evt.dataType === 'node') {
        emit({ dataType: 'node', name: evt.name || '' });
    }
}
"""


def network_hover_show_labels_js(chart_id: int) -> str:
    """Client-only hover handler: show labels on the edge's endpoint nodes."""
    return f"""
(evt) => {{
    const c = getElement({chart_id}).chart;
    if (!c || !evt || evt.componentType !== 'series') return;
    const series = (c.getOption().series || [])[0];
    if (!series || !series.data) return;
    let names = [];
    if (evt.dataType === 'edge') {{
        const d = evt.data || {{}};
        names = [d.source, d.target];
    }} else if (evt.dataType === 'node') {{
        names = [evt.name || (evt.data && evt.data.name)];
    }} else {{
        return;
    }}
    const nameSet = new Set(names.filter((n) => n != null).map(String));
    const data = series.data.map((n) => {{
        const id = String(n.id != null ? n.id : n.name);
        const show = nameSet.has(id) || nameSet.has(String(n.name));
        return Object.assign({{}}, n, {{
            label: {{
                show: show,
                position: 'right',
                formatter: '{{b}}',
                fontSize: {NODE_LABEL_FONT_SIZE},
            }},
        }});
    }});
    c.setOption({{ series: [{{ data: data }}] }}, {{ lazyUpdate: true }});
}}
"""


def network_hover_clear_labels_js(chart_id: int) -> str:
    """Client-only handler: hide all node labels when the pointer leaves."""
    return f"""
() => {{
    const c = getElement({chart_id}).chart;
    if (!c) return;
    const series = (c.getOption().series || [])[0];
    if (!series || !series.data) return;
    const data = series.data.map((n) => Object.assign({{}}, n, {{
        label: {{
            show: false,
            position: 'right',
            formatter: '{{b}}',
            fontSize: {NODE_LABEL_FONT_SIZE},
        }},
    }}));
    c.setOption({{ series: [{{ data: data }}] }}, {{ lazyUpdate: true }});
}}
"""


def resolve_node_ref(ref, nodes: list | None = None) -> str | None:
    """Map an ECharts node id/index to a username string."""
    if ref is None:
        return None
    if isinstance(ref, str):
        return ref
    if isinstance(ref, int):
        if nodes is not None and 0 <= ref < len(nodes):
            return str(nodes[ref])
        return None
    return str(ref)


def users_from_edge_payload(args, nodes: list | None = None) -> tuple[str, str] | None:
    """Parse a network chart click payload into (user0, user1)."""
    if isinstance(args, list) and args:
        args = args[0]
    if not isinstance(args, dict):
        return None

    data_type = args.get("dataType")
    name = args.get("name") or ""

    if data_type == "edge":
        source = resolve_node_ref(args.get("source"), nodes)
        target = resolve_node_ref(args.get("target"), nodes)
        data = args.get("data")
        if (source is None or target is None) and isinstance(data, dict):
            source = source or resolve_node_ref(data.get("source"), nodes)
            target = target or resolve_node_ref(data.get("target"), nodes)
        if source is not None and target is not None:
            return source, target

    if isinstance(name, str) and ">" in name:
        left, right = name.split(">", 1)
        return left.strip(), right.strip()
    return None


def edge_is_one_to_one(G: nx.Graph, u, v) -> bool:
    """True when the edge is an isolated pair in G (both endpoints degree 1)."""
    return G.degree[u] == 1 and G.degree[v] == 1


def edge_group_for_link(G: nx.Graph, u, v) -> str:
    """Group key by max endpoint degree on the displayed graph."""
    n = max(G.degree[u], G.degree[v])
    if n <= 1:
        return EDGE_GROUP_PAIR
    if n <= 5:
        return EDGE_GROUP_2_5
    if n <= 10:
        return EDGE_GROUP_6_10
    return EDGE_GROUP_11_20


def edge_color_for_link(G: nx.Graph, u, v) -> str:
    """Color by max endpoint degree on the displayed graph."""
    group = edge_group_for_link(G, u, v)
    for key, color, _label in EDGE_COLOR_LEGEND:
        if key == group:
            return color
    return EDGE_COLOR_GROUP_11_20


def apply_edge_group_visibility(
    series: list, visible_groups: set[str] | frozenset[str]
):
    """Return a series copy with only links whose edgeGroup is visible.

    Nodes are unchanged so layout context remains when groups are toggled off.
    """
    if not series:
        return series
    out = []
    for s in series:
        links = s.get("links") or []
        filtered = [lk for lk in links if lk.get("edgeGroup") in visible_groups]
        out.append({**s, "links": filtered})
    return out


def plot_subgraph_echart(G: nx.Graph):
    nodes = list(G.nodes())
    data = [{"name": node, "id": node} for node in nodes]
    links = []
    for edge in G.edges():
        u, v = edge[0], edge[1]
        weight = G.edges[edge].get("norm_weight", 1.0)
        group = edge_group_for_link(G, u, v)
        links.append(
            {
                "source": u,
                "target": v,
                "name": f"{u} > {v}",
                "value": float(weight),
                "edgeGroup": group,
                "lineStyle": {"color": edge_color_for_link(G, u, v)},
            }
        )
    series = [dict(ECHART_GRAPH_DEFAULTS, data=data, links=links)]
    return series
