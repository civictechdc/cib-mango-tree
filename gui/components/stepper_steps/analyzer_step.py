from nicegui import ui

from gui.components.toggle import ToggleButtonGroup
from gui.session import GuiSession


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
        analyzer_long_descriptions = {
            analyzer.name: analyzer.long_description for analyzer in analyzers
        }

        self.button_group = ToggleButtonGroup()

        with ui.column().classes("items-center w-full"):
            with ui.element().classes("w-[64rem] max-w-full"):
                with ui.row().classes("items-center justify-center gap-4 w-full"):
                    for analyzer_name in analyzer_options.keys():
                        self.button_group.add_button(analyzer_name)

                with ui.element().classes("pt-12 flex justify-center w-full"):
                    DEFAULT_TEXT = (
                        "No analyzer selected. Click button above to select it."
                    )

                    with ui.card().classes("w-[40rem] shadow-none"):
                        with ui.scroll_area().classes("max-h-48"):
                            ui.label().bind_text_from(
                                target_object=self.button_group,
                                target_name="selected_text",
                                backward=lambda text: analyzer_long_descriptions.get(
                                    text, DEFAULT_TEXT
                                ),
                            ).classes("text-grey")

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
