from typing import Literal, Union

from pydantic import BaseModel, ConfigDict, Field

TimeBinningUnit = Literal[
    "year",
    "month",
    "week",
    "day",
    "hour",
    "minute",
    "second",
]


class IntegerParam(BaseModel):
    """
    Represents an integer value

    The corresponding value will be of type `int`.
    """

    type: Literal["integer"] = "integer"
    min: int
    max: int


class ChoiceOption(BaseModel):
    """One selectable option for a ``ChoiceParam``."""

    value: str
    label: str


class ChoiceParam(BaseModel):
    """
    Represents a single choice from a fixed list of labeled options.

    The corresponding value will be of type ``str`` (the selected option's
    ``value``).
    """

    type: Literal["choice"] = "choice"
    options: list[ChoiceOption] = Field(min_length=1)


class TimeBinningParam(BaseModel):
    """
    Represents a time bin.

    The corresponding value will be of type `TimeBinningValue`.
    """

    type: Literal["time_binning"] = "time_binning"


class TimeBinningValue(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True)

    unit: TimeBinningUnit
    amount: int

    def to_polars_truncate_spec(self) -> str:
        """
        Converts the value to a string that can be used in Polars truncate spec.
        See https://docs.pola.rs/api/python/stable/reference/expressions/api/polars.Expr.dt.truncate.html
        """
        amount = self.amount
        unit = self.unit
        if unit == "year":
            return f"{amount}y"
        if unit == "month":
            return f"{amount}mo"
        if unit == "week":
            return f"{amount}w"
        if unit == "day":
            return f"{amount}d"
        if unit == "hour":
            return f"{amount}h"
        if unit == "minute":
            return f"{amount}m"
        if unit == "second":
            return f"{amount}s"

        raise ValueError("Invalid time binning value")


ParamType = Union[TimeBinningParam, IntegerParam, ChoiceParam]

ParamValue = Union[TimeBinningValue, int, str]
