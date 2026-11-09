"""Primary analyzer contract test for time_coordination."""

import os

import polars as pl

from cibmangotree.preprocessing.series_semantic import identifier
from cibmangotree.testing import CsvTestData
from cibmangotree.testing import context as testing_context

from .test_data import test_data_dir
from .time_coordination_base.interface import (
    COL_NORM_WEIGHT,
    COL_USER_A,
    COL_USER_B,
    COL_WEIGHT,
    OUTPUT_EDGES,
    OUTPUT_POSTS,
    PARAM_METHOD,
    PARAM_MIN_POSTS,
    PARAM_T_STEP,
    PARAM_WIN_SIZE,
)
from .time_coordination_base.main import main


def test_time_coordination_primary_writes_posts_and_edges(tmp_path):
    """Run primary and assert declared schemas + basic graph results."""
    input_csv = os.path.join(test_data_dir, "input.csv")
    input_parquet = tmp_path / "input.parquet"
    CsvTestData(
        input_csv,
        semantics={"user_id": identifier},
    ).convert_to_parquet(str(input_parquet))

    out_dir = tmp_path / "out"
    out_dir.mkdir()
    (tmp_path / "tmp").mkdir()
    ctx = testing_context.TestPrimaryAnalyzerContext(
        temp_dir=str(tmp_path / "tmp"),
        input_parquet_path=str(input_parquet),
        param_values={
            PARAM_METHOD: "sliding_window",
            PARAM_WIN_SIZE: 2,
            PARAM_T_STEP: 60,
            PARAM_MIN_POSTS: 1,
        },
        output_parquet_root_path=str(out_dir),
    )
    main(ctx)

    posts = pl.read_parquet(ctx.output_path(OUTPUT_POSTS))
    edges = pl.read_parquet(ctx.output_path(OUTPUT_EDGES))

    assert set(posts.columns) >= {
        "user_id",
        "timestamp",
        "message_text",
        "rel_timestamp",
    }
    assert len(posts) == 6
    assert set(edges.columns) == {
        COL_USER_A,
        COL_USER_B,
        COL_WEIGHT,
        COL_NORM_WEIGHT,
    }
    assert edges.height >= 1
