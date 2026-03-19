from nicegui import ui

from gui.base import GuiSession
from gui.components.toggle import ToggleButtonGroup


class AnalyzerSelectionStep:
    """Step 1: Select analyzer from available options."""

    def __init__(self, session: GuiSession):
        self.session = session
        self.button_group: ToggleButtonGroup | None = None

    @ui.refreshable_method
    def render(self) -> None:
        """Render the step content."""
        analyzers = self.session.app.context.suite.primary_anlyzers

        if not analyzers:
            ui.label("No analyzers available").classes("text-grey")
            return

        analyzer_options = {
            analyzer.name: analyzer.short_description for analyzer in analyzers
        }

        self.button_group = ToggleButtonGroup()

        with ui.row().classes("items-center justify-center gap-4"):
            for analyzer_name in analyzer_options.keys():
                self.button_group.add_button(analyzer_name)

        with ui.element().classes("pt-12"):
            DEFAULT_TEXT = "No analyzer selected. Click button above to select it."

            ui.label().bind_text_from(
                target_object=self.button_group,
                target_name="selected_text",
                backward=lambda text: analyzer_options.get(text, DEFAULT_TEXT),
            ).classes("text-center w-full")

    def is_valid(self) -> bool:
        """Check if an analyzer is selected."""
        return (
            self.button_group is not None
            and self.button_group.get_selected_text() is not None
        )

    def save_state(self) -> bool:
        """Save selection to session. Returns True if successful."""
        if not self.button_group:
            return False

        new_selection = self.button_group.get_selected_text()

        if not new_selection:
            return False

        analyzers = self.session.app.context.suite.primary_anlyzers
        selected_analyzer = next(
            (a for a in analyzers if a.name == new_selection), None
        )

        if not selected_analyzer:
            return False

        self.session.selected_analyzer = selected_analyzer
        self.session.selected_analyzer_name = new_selection
        return True
