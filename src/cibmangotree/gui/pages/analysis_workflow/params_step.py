from tempfile import TemporaryDirectory

import polars as pl
from nicegui import ui

from cibmangotree.analyzer_interface.params import TimeBinningValue
from cibmangotree.analyzers.hashtags.hashtags_base.interface import (
    PARAM_TIME_WINDOW,
)
from cibmangotree.analyzers.hashtags.hashtags_base.interface import (
    interface as hashtags_interface,
)
from cibmangotree.context import (
    InputColumnProvider,
    PrimaryAnalyzerDefaultParametersContext,
)
from cibmangotree.gui.components import AnalysisParamsCard
from cibmangotree.gui.dashboards.hashtags.data import load_mapped_timestamps
from cibmangotree.gui.dashboards.hashtags.window_preview import (
    activity_bins,
    plot_activity_echart,
    window_count_text,
    window_edges,
)
from cibmangotree.gui.session import GuiSession
from cibmangotree.gui.theme import ICON_INFO, ROW_CENTERED_GAP, TEXT_TOOLTIP_BODY


class ParamsConfigStep:
    """Step 3: Configure analyzer parameters."""

    def __init__(self, session: GuiSession):
        self.session = session
        self.params_card: AnalysisParamsCard | None = None
        self._param_values: dict = {}
        self._preview_timestamps: pl.Series | None = None
        self._preview_bins: pl.DataFrame | None = None
        self._preview_chart: ui.echart | None = None
        self._preview_count: ui.label | None = None
        self._preview_note: ui.label | None = None

    @ui.refreshable_method
    def render(self) -> None:
        """Render parameter configuration or 'no params' message."""
        analyzer = self.session.selected_analyzer
        project = self.session.current_project
        column_mapping = self.session.column_mapping
        self._preview_timestamps = None
        self._preview_bins = None
        self._preview_chart = None
        self._preview_count = None
        self._preview_note = None

        if not analyzer:
            ui.label("Please select an analyzer first").classes("text-grey")
            return

        if not analyzer.params:
            ui.label("This analyzer has no configurable parameters.").classes(
                "text-grey-7"
            )
            self.session.analysis_params = {}
            return

        if not project or not column_mapping:
            ui.label("Please map columns first").classes("text-grey")
            return

        with TemporaryDirectory() as temp_dir:
            default_parameters_context = PrimaryAnalyzerDefaultParametersContext(
                analyzer=analyzer,
                store=self.session.app.context.storage,
                temp_dir=temp_dir,
                input_columns={
                    analyzer_column_name: InputColumnProvider(
                        user_column_name=user_column_name,
                        semantic=project.column_dict[user_column_name].semantic,
                    )
                    for analyzer_column_name, user_column_name in column_mapping.items()
                },
            )

            analyzer_decl = self.session.app.context.suite.get_primary_analyzer(
                analyzer.id
            )

            if not analyzer_decl:
                ui.label(f"Analyzer `{analyzer.id}` not found").classes("text-negative")
                return

            param_values = {
                **{
                    param_spec.id: static_param_default_value
                    for param_spec in analyzer_decl.params
                    if (static_param_default_value := param_spec.default) is not None
                },
                **analyzer_decl.default_params(default_parameters_context),
            }
            param_values = {
                param_id: param_value
                for param_id, param_value in param_values.items()
                if param_value is not None
            }

            self._param_values = param_values

        with (
            ui.column()
            .classes("w-full items-center gap-6")
            .style("max-width: 960px; margin: 0 auto;")
        ):
            ui.label(f"Configure {analyzer.name} Parameters").classes(
                "text-lg font-bold mb-4"
            )

            self.params_card = AnalysisParamsCard(
                params=analyzer.params,
                default_values=self._param_values,
                on_change=self._update_window_preview,
            )
            if analyzer.id == hashtags_interface.id:
                self._mount_window_preview()

    def _mount_window_preview(self) -> None:
        """Draw post activity for the hashtag time window. Timestamps load once."""
        try:
            self._preview_timestamps = load_mapped_timestamps(self.session)
            self._preview_bins = activity_bins(self._preview_timestamps)
        except (OSError, ValueError, pl.exceptions.PolarsError):
            ui.label("Could not load timestamps.").classes("text-grey")
            return

        if self._preview_bins.height == 0:
            ui.label("No timestamps to preview.").classes("text-grey")
            return

        with ui.row().classes(ROW_CENTERED_GAP):
            ui.label("Post activity").classes("text-base font-bold")
            with ui.icon("info").classes(ICON_INFO):
                with ui.tooltip().classes("w-64"):
                    ui.label(
                        "Orange lines show how many posts occurred over time. "
                        "The space between gray dashed lines is how big each window is."
                    ).classes(TEXT_TOOLTIP_BODY)
        self._preview_count = ui.label("").classes("text-grey-7")
        self._preview_note = ui.label("Too many windows to draw.").classes(
            "text-grey-7"
        )
        self._preview_note.set_visibility(False)
        self._preview_chart = ui.echart({}).classes("w-full").style("height: 320px")
        self._update_window_preview()

    def _update_window_preview(self) -> None:
        """Redraw window lines from the cached activity series."""
        if (
            self._preview_chart is None
            or self._preview_bins is None
            or self._preview_timestamps is None
            or self._preview_count is None
            or self._preview_note is None
            or self.params_card is None
        ):
            return

        try:
            window = self.params_card.get_param_values().get(PARAM_TIME_WINDOW)
            if not isinstance(window, TimeBinningValue):
                return
            edges = window_edges(self._preview_timestamps, window)
            option = plot_activity_echart(self._preview_bins, edges)
        except (TypeError, ValueError, pl.exceptions.PolarsError):
            self._preview_note.set_text("Could not draw the time windows.")
            self._preview_note.set_visibility(True)
            return

        self._preview_count.set_text(window_count_text(edges.count))
        self._preview_note.set_text("Too many windows to draw.")
        self._preview_note.set_visibility(edges.starts is None)

        already_drawn = "series" in self._preview_chart.options
        self._preview_chart.options.clear()
        self._preview_chart.options.update(option)
        self._preview_chart.update()
        if already_drawn:
            self._preview_chart.run_chart_method("setOption", option, True)

    def is_valid(self) -> bool:
        """Always valid - params are optional."""
        return True

    def save_state(self) -> bool:
        """Save params to session."""
        if self.params_card:
            self.session.analysis_params = self.params_card.get_param_values()
        else:
            self.session.analysis_params = {}
        return True
