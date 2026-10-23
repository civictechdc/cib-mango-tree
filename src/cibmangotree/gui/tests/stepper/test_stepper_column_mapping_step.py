"""Behavior tests for gui.pages.analysis_workflow.column_mapping_step.ColumnMappingStep."""

from unittest.mock import MagicMock

from nicegui import ui
from nicegui.testing import User

from cibmangotree.analyzer_interface import InputColumn
from cibmangotree.gui.pages.analysis_workflow.column_mapping_step import (
    ColumnMappingStep,
)
from cibmangotree.gui.session import GuiSession

_UNMATCHED_WARNING = "No column matched this type. Choose one manually."


def _user_column(name: str, data_type: str) -> MagicMock:
    column = MagicMock()
    column.name = name
    column.data_type = data_type
    column.data.len.return_value = 3
    column.head.return_value.apply_semantic_transform.return_value = ["a", "b", "c"]
    return column


def _session_for_mapping(
    gui_session: GuiSession, columns: list[MagicMock], input_type: str
) -> GuiSession:
    analyzer = MagicMock()
    analyzer.input.columns = [
        InputColumn(
            name="timestamp",
            human_readable_name="Timestamp",
            data_type=input_type,
        )
    ]
    project = MagicMock()
    project.columns = columns
    project.column_dict = {column.name: column for column in columns}
    gui_session.selected_analyzer = analyzer
    gui_session.current_project = project
    return gui_session


async def test_column_mapping_prompts_when_no_analyzer(
    user: User, gui_session: GuiSession
) -> None:
    step = ColumnMappingStep(gui_session)

    @ui.page("/map-step")
    def page() -> None:
        step.render()

    await user.open("/map-step")
    await user.should_see("Please select an analyzer first")


async def test_unmatched_input_lists_every_column(
    user: User, gui_session: GuiSession
) -> None:
    created_at = _user_column("Createdat", "text")
    _session_for_mapping(gui_session, [created_at], "datetime")
    step = ColumnMappingStep(gui_session)

    @ui.page("/map-step-unmatched")
    def page() -> None:
        step.render()

    await user.open("/map-step-unmatched")
    await user.should_see(_UNMATCHED_WARNING)
    dropdown, options = step.column_dropdowns["timestamp"]
    assert options == {"Createdat": "Createdat"}

    dropdown.set_value("Createdat")
    await user.should_not_see(_UNMATCHED_WARNING)

    dropdown.set_value(None)
    await user.should_see(_UNMATCHED_WARNING)


async def test_matched_input_lists_only_compatible_columns(
    user: User, gui_session: GuiSession
) -> None:
    created_at = _user_column("createdAt", "datetime")
    author = _user_column("author", "identifier")
    _session_for_mapping(gui_session, [created_at, author], "datetime")
    step = ColumnMappingStep(gui_session)

    @ui.page("/map-step-matched")
    def page() -> None:
        step.render()

    await user.open("/map-step-matched")
    await user.should_not_see(_UNMATCHED_WARNING)
    _dropdown, options = step.column_dropdowns["timestamp"]
    assert options == {"createdAt": "createdAt"}
