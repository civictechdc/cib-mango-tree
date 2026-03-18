"""
Framework-agnostic figure builders for the n-grams analyzer.

These functions accept a Polars DataFrame and return either a Plotly
``Figure`` or an ECharts option dict.  They have no dependency on Shiny,
Dash, or NiceGUI and can therefore be imported from any GUI layer.
"""

import numpy as np
import plotly.express as px
import polars as pl

from ..ngrams_base.interface import COL_NGRAM_ID, COL_NGRAM_LENGTH
from ..ngrams_stats.interface import (
    COL_NGRAM_DISTINCT_POSTER_COUNT,
    COL_NGRAM_TOTAL_REPS,
    COL_NGRAM_WORDS,
)

TAB_10_PALETTE = [
    "#1f77b4",
    "#ff7f0e",
    "#2ca02c",
    "#d62728",
    "#9467bd",
    "#8c564b",
    "#e377c2",
    "#7f7f7f",
    "#bcbd22",
    "#17becf",
]


def plot_scatter(data: pl.DataFrame):
    """
    Build a log-log scatter plot of n-gram frequency vs. unique poster count.

    Each point represents one n-gram.  Points are coloured by n-gram length
    and carry ``customdata`` needed for click-based filtering:
    ``[words, ngram_id, total_reps]``.

    Args:
        data: The ``ngram_stats`` Polars DataFrame (must contain the standard
              n-gram statistics columns).

    Returns:
        A ``plotly.graph_objects.Figure`` ready to be passed to any Plotly
        renderer (``ui.plotly``, ``dcc.Graph``, ``fig.show()``, …).
    """
    rng = np.random.default_rng(seed=42)
    jitter_factor = 0.05

    data = data.with_columns(
        (
            pl.col(COL_NGRAM_TOTAL_REPS)
            * (1 + rng.uniform(-jitter_factor, jitter_factor, len(data)))
        ).alias("total_reps_jittered")
    )

    n_gram_categories = data.select(
        pl.col(COL_NGRAM_LENGTH).unique().sort()
    ).to_series()

    fig = px.scatter(
        data_frame=data,
        x=COL_NGRAM_DISTINCT_POSTER_COUNT,
        y="total_reps_jittered",
        log_y=True,
        log_x=True,
        custom_data=[COL_NGRAM_WORDS, COL_NGRAM_ID, COL_NGRAM_TOTAL_REPS],
        color=COL_NGRAM_LENGTH,
        category_orders={COL_NGRAM_LENGTH: n_gram_categories},
    )

    fig.update_traces(
        marker=dict(size=11, opacity=0.7, line=dict(width=0.5, color="white")),
        hovertemplate="<br>".join(
            [
                "<b>N-gram:</b> %{customdata[0]}",
                "<b>Frequency:</b> %{customdata[2]}",
                "<b>Nr. unique posters:</b> %{x}",
            ]
        ),
    )

    fig.update_layout(
        title_text="Repeated phrases and accounts",
        yaxis_title="N-gram frequency",
        xaxis_title="Nr. unique posters",
        hovermode="closest",
        legend=dict(title="N-gram length"),
        template="plotly_white",
    )

    return fig


def plot_scatter_echart(data: pl.DataFrame) -> dict:
    """
    Build a log-log scatter plot of n-gram frequency vs. unique poster count.

    This is the ECharts equivalent of :func:`plot_scatter`.  Each point
    represents one n-gram.  Points are coloured by n-gram length (one series
    per unique ``n`` value).  Custom metadata (``ngram_id``, ``words``,
    ``total_reps``) is attached to each data item for click-based filtering.

    Args:
        data: The ``ngram_stats`` Polars DataFrame (must contain the standard
              n-gram statistics columns).

    Returns:
        A plain dict representing the ECharts option object, ready to be
        passed to ``ui.echart(option)``.
    """
    # Apply jitter to y-axis values (same logic as plot_scatter)
    rng = np.random.default_rng(seed=42)
    jitter_factor = 0.05

    data = data.with_columns(
        (
            pl.col(COL_NGRAM_TOTAL_REPS)
            * (1 + rng.uniform(-jitter_factor, jitter_factor, len(data)))
        ).alias("total_reps_jittered")
    )

    # Get sorted unique n-gram lengths for legend/series ordering
    n_values = (
        data.select(pl.col(COL_NGRAM_LENGTH).unique().sort()).to_series().to_list()
    )

    # Build one series per n-gram length
    series = []
    for i, n in enumerate(n_values):
        subset = data.filter(pl.col(COL_NGRAM_LENGTH) == n)
        series_data = [
            {
                "value": [
                    row[COL_NGRAM_DISTINCT_POSTER_COUNT],
                    row["total_reps_jittered"],
                ],
                "ngram_id": row[COL_NGRAM_ID],
                "words": row[COL_NGRAM_WORDS],
                "total_reps": row[COL_NGRAM_TOTAL_REPS],
            }
            for row in subset.iter_rows(named=True)
        ]
        series.append(
            {
                "name": f"{n}-gram",
                "type": "scatter",
                "color": TAB_10_PALETTE[i],
                "symbolSize": 11,
                "itemStyle": {
                    "color": TAB_10_PALETTE[i % len(TAB_10_PALETTE)],
                    "opacity": 0.7,
                    "borderColor": "white",
                    "borderWidth": 0.5,
                },
                "emphasis": {
                    "itemStyle": {
                        "color": "#d62728",  # Highlight red color
                        "opacity": 1.0,
                        "borderColor": "white",
                        "borderWidth": 2,
                        "shadowBlur": 10,
                        "shadowColor": "rgba(0, 0, 0, 0.3)",
                    },
                    "scale": 1.5,  # Make point 50% larger when emphasized
                },
                "data": series_data,
            }
        )

    option = {
        "title": {"text": "Repeated phrases and accounts"},
        "tooltip": {
            "trigger": "item",
            ":formatter": """function(params) {
                var d = params.data;
                return '<b>N-gram:</b> ' + d.words
                    + '<br/><b>Frequency:</b> ' + d.total_reps
                    + '<br/><b>Nr. unique posters:</b> ' + params.value[0];
            }""",
        },
        "toolbox": {
            "feature": {
                "dataZoom": {},
                "brush": {"type": ["rect", "polygon", "clear"]},
            },
        },
        "legend": {
            "orient": "vertical",
            "type": "scroll",
            "data": [f"{n}-gram" for n in n_values],
            "right": 5,
            "top": "center",
        },
        "grid": {"top": 80},
        "xAxis": {
            "type": "log",
            "min": 0.5,
            "name": "Nr. unique posters",
            "nameLocation": "middle",
            "nameGap": 30,
            "nameTextStyle": {"fontSize": 14},
            "axisLabel": {
                ":formatter": "function(value) { return value >= 1 ? value : ''; }",
                "fontSize": 12,
            },
        },
        "yAxis": {
            "type": "log",
            "min": 0.5,
            "name": "N-gram frequency",
            "nameLocation": "middle",
            "nameGap": 40,
            "nameTextStyle": {"fontSize": 14},
            "axisLabel": {
                ":formatter": "function(value) { return value >= 1 ? value : ''; }",
                "fontSize": 12,
            },
        },
        "series": series,
    }

    return option
