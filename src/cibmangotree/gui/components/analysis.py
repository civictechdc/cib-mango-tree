from collections.abc import Callable

from nicegui import ui

from cibmangotree.analyzer_interface import (
    AnalyzerParam,
    ChoiceParam,
    IntegerParam,
    ParamValue,
    TimeBinningValue,
)
from cibmangotree.gui.theme import (
    CARD_PARAM,
    ICON_INFO,
    ROW_CENTERED,
    ROW_CENTERED_GAP,
    ROW_GAP_MT,
    ROW_WRAP_CENTER,
    TEXT_BOLD,
    TEXT_MUTED,
    TEXT_TOOLTIP_BODY,
    WIDTH_AMOUNT,
    WIDTH_FULL_MT_2,
    WIDTH_TOOLTIP,
    WIDTH_UNIT_SELECT,
)


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
        *,
        on_change: Callable[[], None] | None = None,
    ):
        """
        Initialize the analysis parameters card.

        Args:
            params: List of analyzer parameter specifications
            default_values: Dictionary of default parameter values
            on_change: Called when a time-binning amount or unit changes
        """
        self.params = params
        self.default_values = default_values
        self._on_change = on_change
        self.param_widgets: dict[str, tuple] = {}

        # Build the card UI
        self._build_card()

    def _build_card(self):
        """Build the parameter configuration cards in a flex-wrap row."""
        if not self.params:
            with ui.column().classes(ROW_CENTERED):
                ui.label("This analyzer has no configurable parameters.").classes(
                    TEXT_MUTED
                )
            return

        with ui.row().classes(ROW_WRAP_CENTER):
            for param in self.params:
                self._build_param_card(param)

    def _build_param_card(self, param: AnalyzerParam):
        """Build an individual card for a single parameter."""
        with ui.card().classes(CARD_PARAM):
            with ui.row().classes(ROW_CENTERED_GAP):
                ui.label(param.print_name).classes(TEXT_BOLD)
                if param.description:
                    with ui.icon("info").classes(ICON_INFO):
                        with ui.tooltip().classes(WIDTH_TOOLTIP):
                            ui.label(param.description).classes(TEXT_TOOLTIP_BODY)

            param_type = param.type
            default_value = self.default_values.get(param.id)

            if param_type.type == "integer":
                self._build_integer_control(param, param_type, default_value)
            elif param_type.type == "choice":
                self._build_choice_control(param, param_type, default_value)
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
        ).classes(WIDTH_FULL_MT_2)

        self.param_widgets[param.id] = ("integer", number_input)

    def _build_choice_control(
        self,
        param: AnalyzerParam,
        param_type: ChoiceParam,
        default_value: ParamValue | None,
    ):
        """Build labeled single-choice control."""
        options = {opt.value: opt.label for opt in param_type.options}
        allowed = set(options)
        if isinstance(default_value, str) and default_value in allowed:
            selected = default_value
        else:
            selected = param_type.options[0].value

        select = ui.select(
            options,
            value=selected,
            on_change=self._notify_change,
        ).classes(WIDTH_FULL_MT_2)

        self.param_widgets[param.id] = ("choice", select)

    def _build_time_binning_control(
        self, param: AnalyzerParam, default_value: ParamValue | None
    ):
        """Build time binning parameter control."""
        tb_default = (
            default_value if isinstance(default_value, TimeBinningValue) else None
        )
        with ui.row().classes(ROW_GAP_MT):
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
                on_change=self._notify_change,
            ).classes(WIDTH_UNIT_SELECT)

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
                on_change=self._notify_change,
            ).classes(WIDTH_AMOUNT)

        self.param_widgets[param.id] = ("time_binning", unit_select, amount_input)

    def _notify_change(self, _event=None) -> None:
        if self._on_change is not None:
            self._on_change()

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

            elif param_type == "choice":
                select = widgets[1]
                param_values[param_id] = str(select.value)

            elif param_type == "time_binning":
                unit_toggle = widgets[1]
                amount_input = widgets[2]
                param_values[param_id] = TimeBinningValue(
                    unit=unit_toggle.value, amount=int(amount_input.value)
                )

        return param_values
