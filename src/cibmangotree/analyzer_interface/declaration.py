from typing import Callable

from .context import (
    PrimaryAnalyzerContext,
    SecondaryAnalyzerContext,
)
from .interface import (
    AnalyzerInterface,
    SecondaryAnalyzerInterface,
)
from .params import ParamValue


class AnalyzerDeclaration(AnalyzerInterface):
    entry_point: Callable[[PrimaryAnalyzerContext], None]
    default_params: Callable[[PrimaryAnalyzerContext], dict[str, ParamValue]]
    is_distributed: bool

    def __init__(
        self,
        interface: AnalyzerInterface,
        main: Callable,
        *,
        is_distributed: bool = False,
        default_params: Callable[[PrimaryAnalyzerContext], dict[str, ParamValue]] = (
            lambda _: dict()
        ),
    ):
        """Creates a primary analyzer declaration

        Args:
          interface (AnalyzerInterface): The metadata interface for the primary analyzer.

          main (Callable):
            The entry point function for the primary analyzer. This function should
            take a single argument of type `PrimaryAnalyzerContext` and should ensure
            that the outputs specified in the interface are generated.

          is_distributed (bool):
            Set this explicitly to `True` once the analyzer is ready to be shipped
            to end users; it will make the analyzer available in the distributed
            executable.
        """
        super().__init__(
            **interface.model_dump(),
            entry_point=main,
            default_params=default_params,
            is_distributed=is_distributed,
        )


class SecondaryAnalyzerDeclaration(SecondaryAnalyzerInterface):
    entry_point: Callable[["SecondaryAnalyzerContext"], None]

    def __init__(self, interface: SecondaryAnalyzerInterface, main: Callable):
        """Creates a secondary analyzer declaration

        Args:
          interface (SecondaryAnalyzerInterface): The metadata interface for the secondary analyzer.

          main (Callable):
            The entry point function for the secondary analyzer. This function should
            take a single argument of type `SecondaryAnalyzerContext` and should ensure
            that the outputs specified in the interface are generated.
        """
        super().__init__(**interface.model_dump(), entry_point=main)
