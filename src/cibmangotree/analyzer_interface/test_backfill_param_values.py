from cibmangotree.analyzer_interface import (
    AnalyzerInput,
    AnalyzerInterface,
    AnalyzerParam,
    IntegerParam,
    backfill_param_values,
)


def _spec_with_int_param(*, backfill_value: int = 5) -> AnalyzerInterface:
    return AnalyzerInterface(
        id="__backfill_test__",
        version="0.0.0",
        name="Backfill test",
        short_description="test",
        long_description="test",
        input=AnalyzerInput(columns=[]),
        params=[
            AnalyzerParam(
                id="count",
                type=IntegerParam(min=-100, max=100),
                default=1,
                backfill_value=backfill_value,
            )
        ],
        outputs=[],
    )


def test_backfill_preserves_zero():
    spec = _spec_with_int_param(backfill_value=5)
    assert backfill_param_values({"count": 0}, spec)["count"] == 0


def test_backfill_preserves_false_for_truthy_backfill():
    spec = AnalyzerInterface(
        id="__backfill_bool__",
        version="0.0.0",
        name="Backfill bool test",
        short_description="test",
        long_description="test",
        input=AnalyzerInput(columns=[]),
        params=[
            AnalyzerParam(
                id="flag",
                type=IntegerParam(min=0, max=1),
                default=1,
                backfill_value=1,
            )
        ],
        outputs=[],
    )
    # 0 is falsy but must not be replaced by backfill_value
    assert backfill_param_values({"flag": 0}, spec)["flag"] == 0


def test_backfill_fills_missing_and_none():
    spec = _spec_with_int_param(backfill_value=5)
    assert backfill_param_values({}, spec)["count"] == 5
    assert backfill_param_values({"count": None}, spec)["count"] == 5
