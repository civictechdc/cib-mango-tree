from tempfile import TemporaryDirectory

from nicegui import ui

from context import InputColumnProvider, PrimaryAnalyzerDefaultParametersContext
from gui.components import AnalysisParamsCard
from gui.session import GuiSession


class ParamsConfigStep:
    """Step 3: Configure analyzer parameters."""

    def __init__(self, session: GuiSession):
        self.session = session
        self.params_card: AnalysisParamsCard | None = None
        self._param_values: dict = {}

    @ui.refreshable_method
    def render(self) -> None:
        """Render parameter configuration or 'no params' message."""
        analyzer = self.session.selected_analyzer
        project = self.session.current_project
        column_mapping = self.session.column_mapping

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
                params=analyzer.params, default_values=self._param_values
            )

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

    def has_params(self) -> bool:
        """Check if analyzer has configurable parameters."""
        analyzer = self.session.selected_analyzer
        return analyzer is not None and len(analyzer.params) > 0
