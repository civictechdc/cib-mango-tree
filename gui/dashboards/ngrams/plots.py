"""
Framework-agnostic ECharts figure builders for the n-grams analyzer.

These functions accept a Polars DataFrame and return an ECharts option dict.
They have no dependency on Shiny, Dash, or NiceGUI.
"""

import numpy as np
import polars as pl
from pydantic import BaseModel

from analyzers.ngrams.ngrams_base.interface import COL_NGRAM_ID, COL_NGRAM_LENGTH
from analyzers.ngrams.ngrams_stats.interface import (
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


def plot_scatter_echart(
    data: pl.DataFrame,
    enable_large_mode: bool = True,
) -> dict:
    rng = np.random.default_rng(seed=42)
    jitter_factor = 0.05

    data = data.with_columns(
        (
            pl.col(COL_NGRAM_TOTAL_REPS)
            * (1 + rng.uniform(-jitter_factor, jitter_factor, len(data)))
        ).alias("total_reps_jittered")
    )

    n_values = (
        data.select(pl.col(COL_NGRAM_LENGTH).unique().sort()).to_series().to_list()
    )

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
                    "color": "#d62728",
                    "opacity": 1.0,
                    "borderColor": "white",
                    "borderWidth": 1,
                    "shadowBlur": 10,
                    "shadowColor": "rgba(0, 0, 0, 0.3)",
                },
                "scale": 1.5,
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
