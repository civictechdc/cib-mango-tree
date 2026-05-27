from abc import ABC, abstractmethod
from typing import Any, Callable, Optional, Protocol, TypeVar

import polars as pl
from polars import DataFrame
from pydantic import BaseModel, ConfigDict

from .interface import SecondaryAnalyzerInterface
from .params import ParamValue


class ProgressReporterProtocol(Protocol):
    """Protocol for progress reporting during analysis steps."""

    def update(self, value: float) -> None:
        """Update progress value (0.0 to 1.0)."""
        ...

    def finish(self, done_text: str = "Done!") -> None:
        """Mark the step as complete."""
        ...

    def __enter__(self) -> "ProgressReporterProtocol": ...

    def __exit__(self, *args) -> None: ...


class NullProgressReporter:
    """No-op progress reporter for when progress reporting is disabled."""

    def __init__(self, title: str):
        self.title = title

    def update(self, value: float):
        pass

    def finish(self, done_text: str = "Done!"):
        pass

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        pass


class PrimaryAnalyzerContext(ABC, BaseModel):
    temp_dir: str
    """
  Gets the temporary directory that the module can freely write content to
  during its lifetime. This directory will not persist between runs.
  """

    @abstractmethod
    def input(self) -> "InputTableReader":
        """
        Gets the input reader context.

        **Note that this is in function form** even though one input is expected,
        in anticipation that we may want to support multiple inputs in the future.
        """
        pass

    @property
    @abstractmethod
    def params(self) -> dict[str, ParamValue]:
        """
        Gets the analysis parameters.
        """
        pass

    @abstractmethod
    def output(self, output_id: str) -> "TableWriter":
        """
        Gets the output writer context for the specified output ID.
        """
        pass


class BaseDerivedModuleContext(ABC, BaseModel):
    """
    Common interface for secondary analyzers runtime contexts.
    """

    temp_dir: str
    """
  Gets the temporary directory that the module can freely write content to
  during its lifetime. This directory will not persist between runs.
  """

    @property
    @abstractmethod
    def base_params(self) -> dict[str, ParamValue]:
        """
        Gets the primary analysis parameters.
        """
        pass

    @property
    @abstractmethod
    def base(self) -> "AssetsReader":
        """
        Gets the base primary analyzer's context, which lets you inspect and load its
        outputs.
        """
        pass

    @abstractmethod
    def dependency(
        self, secondary_interface: SecondaryAnalyzerInterface
    ) -> "AssetsReader":
        """
        Gets the context of a secondary analyzer the current module depends on, which
        lets you inspect and load its outputs.
        """
        pass


class SecondaryAnalyzerContext(BaseDerivedModuleContext):
    @abstractmethod
    def output(self, output_id: str) -> "TableWriter":
        """
        Gets the output writer context
        """
        pass


class AssetsReader(ABC):
    @abstractmethod
    def table(self, output_id: str) -> "TableReader":
        """
        Gets the table reader for the specified output.
        """
        pass


class TableReader(ABC):
    @property
    @abstractmethod
    def parquet_path(self) -> str:
        """
        Gets the path to the table's parquet file. The module should expect a parquet
        file here.
        """
        pass


PolarsDataFrameLike = TypeVar("PolarsDataFrameLike", bound=pl.DataFrame)


class InputTableReader(TableReader):
    @abstractmethod
    def preprocess[PolarsDataFrameLike](
        self, df: PolarsDataFrameLike
    ) -> PolarsDataFrameLike:
        """
        Given the manually loaded user input dataframe, apply column mapping and
        semantic transformations to give the input dataframe that the analyzer
        expects.
        """
        pass


class TableWriter(ABC):
    @property
    @abstractmethod
    def parquet_path(self) -> str:
        """
        Gets the path to the table's parquet file. The module should write a parquet
        file to it.
        """
        pass
