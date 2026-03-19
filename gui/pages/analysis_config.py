from typing import Any

from nicegui import ui

from gui.base import GuiPage, GuiSession, gui_routes
from gui.components.stepper_steps import (
    AnalyzerSelectionStep,
    ColumnMappingStep,
    ParamsConfigStep,
    RunAnalysisStep,
)


class AnalysisConfigPage(GuiPage):
    """Combined analysis configuration using a stepper."""

    stepper: Any = None
    steps: dict = {}

    def __init__(self, session: GuiSession):
        config_title = "Configure Analysis"
        super().__init__(
            session=session,
            route=gui_routes.configure_analysis,
            title=(
                f"{session.current_project.display_name}: {config_title}"
                if session.current_project is not None
                else config_title
            ),
            show_back_button=True,
            back_route=gui_routes.select_analyzer_fork,
            show_footer=True,
        )

    def render_content(self) -> None:
        """Render the stepper with all configuration steps."""
        if not self.session.current_project:
            self.notify_warning("No project selected. Redirecting...")
            self.navigate_to(gui_routes.select_project)
            return

        with (
            ui.column()
            .classes("items-center justify-start gap-6")
            .style("width: 100%; max-width: 1200px; margin: 0 auto; padding: 2rem;")
        ):
            with ui.stepper().props("vertical animated").classes("w-full") as stepper:
                self.stepper = stepper

                self._render_analyzer_step()
                self._render_column_mapping_step()
                self._render_params_step()
                self._render_run_step()

    def _render_analyzer_step(self) -> None:
        """Render Step 1: Analyzer Selection."""
        with ui.step("Select Analyzer", icon="science"):
            self.steps["analyzer"] = AnalyzerSelectionStep(self.session)
            self.steps["analyzer"].render()

            with ui.stepper_navigation():
                ui.button(
                    "Next",
                    icon="arrow_forward",
                    color="primary",
                    on_click=self._on_next_analyzer,
                )

    def _render_column_mapping_step(self) -> None:
        """Render Step 2: Column Mapping."""
        with ui.step("Map Columns", icon="table"):
            self.steps["columns"] = ColumnMappingStep(self.session)
            self.steps["columns"].render()

            with ui.stepper_navigation():
                ui.button(
                    "Next",
                    icon="arrow_forward",
                    color="primary",
                    on_click=self._on_next_columns,
                )
                ui.button("Back", on_click=self.stepper.previous).props("flat")

    def _render_params_step(self) -> None:
        """Render Step 3: Parameter Configuration."""
        with ui.step("Configure Parameters", icon="tune"):
            self.steps["params"] = ParamsConfigStep(self.session)
            self.steps["params"].render()

            with ui.stepper_navigation():
                ui.button(
                    "Next",
                    icon="arrow_forward",
                    color="primary",
                    on_click=self._on_next_params,
                )
                ui.button("Back", on_click=self.stepper.previous).props("flat")

    def _render_run_step(self) -> None:
        """Render Step 4: Run Analysis."""
        with ui.step("Run Analysis", icon="play_arrow"):
            self.steps["run"] = RunAnalysisStep(
                session=self.session,
                notify_success=self.notify_success,
                notify_warning=self.notify_warning,
                notify_error=self.notify_error,
                navigate_to=self.navigate_to,
            )
            self.steps["run"].render()

            with ui.stepper_navigation():
                ui.button("Back", on_click=self.stepper.previous).props("flat")

    def _on_next_analyzer(self) -> None:
        """Handle Next from analyzer selection step."""
        step = self.steps.get("analyzer")
        if not step:
            return

        if not step.is_valid():
            self.notify_warning("Please select an analyzer")
            return

        if step.save_state():
            self.stepper.next()

    def _on_next_columns(self) -> None:
        """Handle Next from column mapping step."""
        step = self.steps.get("columns")
        if not step:
            return

        if not step.is_valid():
            self.notify_warning("Please map all required columns")
            return

        if step.save_state():
            self.stepper.next()

    def _on_next_params(self) -> None:
        """Handle Next from parameters step."""
        step = self.steps.get("params")
        if not step:
            return

        if step.save_state():
            self.stepper.next()
