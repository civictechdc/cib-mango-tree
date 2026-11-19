import textwrap

from nicegui import ui

from cibmangotree.gui.components.toggle import ToggleButtonGroup
from cibmangotree.gui.session import GuiSession
from cibmangotree.gui.theme import (
    BLOCK_ANALYZER_GRID,
    BLOCK_PT_12_CENTER,
    CARD_ANALYZER_DESC,
    COL_CENTERED_FULL,
    ROW_CENTER_GAP_4_FULL,
    SCROLL_MAX_H_72,
    TEXT_MUTED,
)


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
            ui.label("No analyzers available").classes(TEXT_MUTED)
            return

        analyzer_options = {
            analyzer.name: analyzer.short_description for analyzer in analyzers
        }
        analyzer_long_descriptions = {
            analyzer.name: analyzer.long_description for analyzer in analyzers
        }

        self.button_group = ToggleButtonGroup()

        with ui.column().classes(COL_CENTERED_FULL):
            with ui.element().classes(BLOCK_ANALYZER_GRID):
                with ui.row().classes(ROW_CENTER_GAP_4_FULL):
                    for analyzer_name in analyzer_options.keys():
                        self.button_group.add_button(analyzer_name)

                with ui.element().classes(BLOCK_PT_12_CENTER):
                    DEFAULT_TEXT = (
                        "No analyzer selected. Click button above to select it."
                    )

                    def _description_markdown(selected: str | None) -> str:
                        raw = analyzer_long_descriptions.get(
                            selected or "", DEFAULT_TEXT
                        )
                        return textwrap.dedent(raw or DEFAULT_TEXT).strip()

                    with ui.card().classes(CARD_ANALYZER_DESC):
                        # Taller than before so method lists are readable.
                        with ui.scroll_area().classes(SCROLL_MAX_H_72):
                            ui.markdown().bind_content_from(
                                target_object=self.button_group,
                                target_name="selected_text",
                                backward=_description_markdown,
                            ).classes(TEXT_MUTED)

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
