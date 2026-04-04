"""
Framework-agnostic figure builders for the n-grams analyzer.

These functions accept a Polars DataFrame and return either a Plotly
``Figure`` or an ECharts option dict.  They have no dependency on Shiny,
Dash, or NiceGUI and can therefore be imported from any GUI layer.
"""

import numpy as np
import plotly.express as px
import polars as pl
from pydantic import BaseModel

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


class SamplingMetadata(BaseModel):
    """Metadata about data sampling applied before visualization."""

    total_count: int
    sampled_count: int
    is_sampled: bool
    strategy: str

    @property
    def sampling_message(self) -> str:
        """Human-readable summary shown in the dashboard info label."""
        if not self.is_sampled:
            return f"Showing all {self.total_count:,} n-grams."
        return (
            f"Showing top {self.sampled_count:,} of {self.total_count:,} n-grams "
            f"(by frequency). Click 'Show all' to load the complete dataset."
        )


def sample_ngram_data(
    df: pl.DataFrame,
    max_points: int = 50000,
    sort_column: str = COL_NGRAM_TOTAL_REPS,
) -> tuple[pl.DataFrame, SamplingMetadata]:
    """
    Sample n-gram data for visualization.

    For datasets larger than max_points, returns the top N rows sorted by
    frequency (total_reps). This preserves the most interesting data points
    while keeping rendering performant.

    Args:
        df: Input DataFrame with n-gram statistics.
        max_points: Maximum number of points to return (default 50,000).
        sort_column: Column to sort by for sampling (default: total_reps).

    Returns:
        Tuple of (sampled_dataframe, SamplingMetadata).
    """
    total_count = len(df)

    if total_count <= max_points:
        return df, SamplingMetadata(
            total_count=total_count,
            sampled_count=total_count,
            is_sampled=False,
            strategy="none",
        )

    sampled = df.sort(sort_column, descending=True).head(max_points)

    return sampled, SamplingMetadata(
        total_count=total_count,
        sampled_count=max_points,
        is_sampled=True,
        strategy="top_by_frequency",
    )


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


def plot_scatter_echart(
    data: pl.DataFrame,
    enable_large_mode: bool = True,
) -> dict:
    """
    Build a log-log scatter plot of n-gram frequency vs. unique poster count.

    This is the ECharts equivalent of :func:`plot_scatter`.  Each point
    represents one n-gram.  Points are coloured by n-gram length (one series
    per unique ``n`` value).  Custom metadata (``ngram_id``, ``words``,
    ``total_reps``) is attached to each data item for click-based filtering.

    Args:
        data: The ``ngram_stats`` Polars DataFrame (must contain the standard
              n-gram statistics columns).
        enable_large_mode: Inject ECharts large-dataset optimizations.
            Should be True whenever data has more than ~2,000 points.

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
        series_config = {
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

        if enable_large_mode:
            series_config.update(
                {
                    "large": True,
                    "largeThreshold": 2000,
                    "progressive": 2000,
                    "progressiveThreshold": 10000,
                }
            )

        series.append(series_config)

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

    if enable_large_mode:
        option.update(
            {
                "animation": False,
                "animationThreshold": 5000,
                "hoverLayerThreshold": 10000,
            }
        )

    return option
