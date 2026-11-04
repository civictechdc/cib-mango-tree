"""Primary entry: mapped posts → time-analysis graph → posts + edges parquet."""

from __future__ import annotations

import polars as pl

from cibmangotree.analyzer_interface.context import PrimaryAnalyzerContext

from ..graph_utils import remember_top_edges
from .analysis import METHODS, prepare_dataframe, time_overlap
from .interface import (
    COL_MESSAGE_TEXT,
    COL_NORM_WEIGHT,
    COL_REL_TIMESTAMP,
    COL_TIMESTAMP,
    COL_USER_A,
    COL_USER_B,
    COL_USER_ID,
    COL_WEIGHT,
    METHOD_TIME_OVERLAP,
    OUTPUT_EDGES,
    OUTPUT_POSTS,
    PARAM_METHOD,
    PARAM_MIN_POSTS,
    PARAM_T_STEP,
    PARAM_WIN_SIZE,
)


class _ProgressValue:
    """Adapter so legacy analysis code can assign ``progress.value``."""

    def __init__(self, reporter):
        self._reporter = reporter
        self._value = 0.0

    @property
    def value(self) -> float:
        return self._value

    @value.setter
    def value(self, v: float) -> None:
        self._value = float(v)
        self._reporter.update(self._value)


def _edges_frame(graph) -> pl.DataFrame:
    rows = [
        {
            COL_USER_A: str(u),
            COL_USER_B: str(v),
            COL_WEIGHT: float(data.get("weight", 0.0)),
            COL_NORM_WEIGHT: float(data.get("norm_weight", 0.0)),
        }
        for u, v, data in graph.edges(data=True)
    ]
    if not rows:
        return pl.DataFrame(
            schema={
                COL_USER_A: pl.Utf8,
                COL_USER_B: pl.Utf8,
                COL_WEIGHT: pl.Float64,
                COL_NORM_WEIGHT: pl.Float64,
            }
        )
    return pl.DataFrame(rows)


def main(context: PrimaryAnalyzerContext) -> None:
    method_id = str(context.params[PARAM_METHOD])
    win_size = int(context.params[PARAM_WIN_SIZE])
    t_step = int(context.params[PARAM_T_STEP])
    min_posts = int(context.params[PARAM_MIN_POSTS])
    if method_id not in METHODS:
        raise ValueError(f"Unknown time-analysis method: {method_id!r}")

    input_reader = context.input()
    with context.progress("Reading input") as read_progress:
        df_in = input_reader.preprocess(pl.read_parquet(input_reader.parquet_path))
        read_progress.update(1.0)

    pdf = df_in.select([COL_USER_ID, COL_TIMESTAMP, COL_MESSAGE_TEXT]).to_pandas()

    with context.progress("Preparing timestamps") as prep_progress:
        prepared = prepare_dataframe(
            pdf,
            time_col_name=COL_TIMESTAMP,
            user_col_name=COL_USER_ID,
            content_col_name=COL_MESSAGE_TEXT,
            progress=_ProgressValue(prep_progress),
        )
        prep_progress.finish()

    posts = pl.from_pandas(
        prepared.df[[COL_USER_ID, COL_TIMESTAMP, COL_MESSAGE_TEXT, "rel_timestamp"]]
    ).rename({"rel_timestamp": COL_REL_TIMESTAMP})
    posts.write_parquet(context.output(OUTPUT_POSTS).parquet_path)

    method = METHODS[method_id]
    with context.progress("Building graph") as build_progress:
        progress = _ProgressValue(build_progress)
        if method_id == METHOD_TIME_OVERLAP:
            graph = time_overlap(
                prepared,
                progress,
                win_size=win_size,
                t_step=t_step,
                min_posts=min_posts,
            )
        else:
            graph = method(prepared, progress, win_size=win_size, t_step=t_step)
        build_progress.finish()

    with context.progress("Ranking edges") as rank_progress:
        remember_top_edges(graph, progress=_ProgressValue(rank_progress))
        rank_progress.finish()

    _edges_frame(graph).write_parquet(context.output(OUTPUT_EDGES).parquet_path)
