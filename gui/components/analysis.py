from nicegui import ui

from analyzer_interface import AnalyzerParam, IntegerParam, ParamValue, TimeBinningValue


class AnalysisParamsCard:
    """
    Card component for configuring analyzer parameters.

    Displays each parameter as an individual card, matching the visual style
    of the column picker cards for consistent UX.
    """

    def __init__(
        self,
        params: list[AnalyzerParam],
        default_values: dict[str, ParamValue],
    ):
        """
        Initialize the analysis parameters card.

        Args:
            params: List of analyzer parameter specifications
            default_values: Dictionary of default parameter values
        """
        self.params = params
        self.default_values = default_values
        self.param_widgets: dict[str, tuple] = {}

        # Build the card UI
        self._build_card()

    def _build_card(self):
        """Build the parameter configuration cards in a flex-wrap row."""
        if not self.params:
            with ui.column().classes("w-full items-center"):
                ui.label("This analyzer has no configurable parameters.").classes(
                    "text-grey-7"
                )
            return

        with ui.row().classes("flex-wrap gap-6 justify-center w-full"):
            for param in self.params:
                self._build_param_card(param)

    def _build_param_card(self, param: AnalyzerParam):
        """Build an individual card for a single parameter."""
        with ui.card().classes("w-72 p-4 no-shadow border border-gray-200"):
            with ui.row().classes("items-center gap-1"):
                ui.label(param.print_name).classes("text-bold")
                if param.description:
                    with ui.icon("info").classes("text-grey-6 cursor-pointer"):
                        ui.tooltip(param.description)

            param_type = param.type
            default_value = self.default_values.get(param.id)

            if param_type.type == "integer":
                self._build_integer_control(param, param_type, default_value)
            elif param_type.type == "time_binning":
                self._build_time_binning_control(param, default_value)

    def _build_integer_control(
        self,
        param: AnalyzerParam,
        param_type: IntegerParam,
        default_value: ParamValue | None,
    ):
        """Build integer parameter control."""
        int_default = default_value if isinstance(default_value, int) else None
        number_input = ui.number(
            value=int_default if int_default is not None else param_type.min,
            min=param_type.min,
            max=param_type.max,
            step=1,
            precision=0,
            validation={
                f"Must be at least {param_type.min}": lambda v: v >= param_type.min,
                f"Must be at most {param_type.max}": lambda v: v <= param_type.max,
            },
        ).classes("w-full mt-2")

        self.param_widgets[param.id] = ("integer", number_input)

    def _build_time_binning_control(
        self, param: AnalyzerParam, default_value: ParamValue | None
    ):
        """Build time binning parameter control."""
        tb_default = (
            default_value if isinstance(default_value, TimeBinningValue) else None
        )
        with ui.row().classes("gap-2 mt-2 w-full"):
            unit_select = ui.select(
                {
                    "year": "Year",
                    "month": "Month",
                    "week": "Week",
                    "day": "Day",
                    "hour": "Hour",
                    "minute": "Minute",
                    "second": "Second",
                },
                value=tb_default.unit if tb_default else "day",
            ).classes("w-32")

            amount_input = ui.number(
                value=tb_default.amount if tb_default else 1,
                min=1,
                max=1000,
                step=1,
                precision=0,
                validation={
                    "Must be at least 1": lambda v: v >= 1,
                    "Cannot exceed 1000": lambda v: v <= 1000,
                },
            ).classes("w-24")

        self.param_widgets[param.id] = ("time_binning", unit_select, amount_input)

    def get_param_values(self) -> dict[str, ParamValue]:
        """
        Retrieve current parameter values from the UI controls.

        Returns:
            Dictionary mapping parameter IDs to their values
        """
        param_values = {}

        for param_id, widgets in self.param_widgets.items():
            param_type = widgets[0]

            if param_type == "integer":
                number_input = widgets[1]
                param_values[param_id] = int(number_input.value)

            elif param_type == "time_binning":
                unit_toggle = widgets[1]
                amount_input = widgets[2]
                param_values[param_id] = TimeBinningValue(
                    unit=unit_toggle.value, amount=int(amount_input.value)
                )

        return param_values
