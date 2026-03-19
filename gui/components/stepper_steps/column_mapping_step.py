import polars as pl
from nicegui import ui

from analyzer_interface import column_automap, get_data_type_compatibility_score
from gui.base import GuiSession


class ColumnMappingStep:
    """Step 2: Map user columns to analyzer input columns."""

    def __init__(self, session: GuiSession):
        self.session = session
        self.column_dropdowns: dict = {}
        self.preview_container = None

    def render(self) -> None:
        """Render the step content with column cards and preview."""
        analyzer = self.session.selected_analyzer
        project = self.session.current_project

        if not analyzer or not project:
            ui.label("No analyzer or project selected").classes("text-grey")
            return

        input_columns = analyzer.input.columns
        user_columns = project.columns

        draft_column_mapping = column_automap(user_columns, input_columns)

        with (
            ui.column()
            .classes("w-full items-center gap-6")
            .style("max-width: 960px; margin: 0 auto;")
        ):
            ui.label("Map Your Data Columns").classes("text-lg font-bold mb-4")

            with ui.row().classes("flex-wrap gap-6 justify-center w-full"):
                for input_col in input_columns:
                    self._build_column_card(
                        input_col, user_columns, draft_column_mapping
                    )

            self.preview_container = ui.column().classes("w-full")
            self._update_preview()

    def _build_column_card(self, input_col, user_columns, draft_column_mapping) -> None:
        """Build a single column mapping card."""
        with ui.card().classes("w-52 p-4 no-shadow border border-gray-200"):
            with ui.row().classes("items-center gap-1"):
                ui.label(input_col.human_readable_name_or_fallback()).classes(
                    "text-bold"
                )
                if input_col.description:
                    with ui.icon("info").classes("text-grey-6 cursor-pointer"):
                        ui.tooltip(input_col.description)

            compatible_columns = [
                user_col
                for user_col in user_columns
                if get_data_type_compatibility_score(
                    input_col.data_type, user_col.data_type
                )
                is not None
            ]

            dropdown_options = {
                f"{user_col.name}": user_col.name for user_col in compatible_columns
            }

            default_value = None
            if input_col.name in draft_column_mapping:
                mapped_col_name = draft_column_mapping[input_col.name]
                default_value = next(
                    (k for k, v in dropdown_options.items() if v == mapped_col_name),
                    None,
                )

            dropdown = (
                ui.select(
                    options=list(dropdown_options.keys()),
                    value=default_value,
                    on_change=lambda: self._update_preview(),
                )
                .classes("w-full mt-2")
                .props("use-chips")
            )

            self.column_dropdowns[input_col.name] = (dropdown, dropdown_options)

    def _build_preview_df(self) -> pl.DataFrame:
        """Build preview DataFrame with currently mapped columns."""
        analyzer = self.session.selected_analyzer
        project = self.session.current_project

        if not analyzer or not project:
            return pl.DataFrame()

        current_mapping = {}
        for input_col_name, (dropdown, options) in self.column_dropdowns.items():
            if dropdown.value:
                current_mapping[input_col_name] = options[dropdown.value]

        tmp_col = list(project.column_dict.values())[0]
        N_PREVIEW_ROWS = min(5, tmp_col.data.len())

        preview_data = {}
        for analyzer_col in analyzer.input.columns:
            col_name = analyzer_col.human_readable_name_or_fallback()
            user_col_name = current_mapping.get(analyzer_col.name)

            if user_col_name and user_col_name in project.column_dict:
                user_col = project.column_dict[user_col_name]
                preview_data[col_name] = user_col.head(
                    N_PREVIEW_ROWS
                ).apply_semantic_transform()
            else:
                preview_data[col_name] = [None] * N_PREVIEW_ROWS

        return pl.DataFrame(preview_data)

    def _update_preview(self) -> None:
        """Rebuild preview when dropdown changes."""
        if self.preview_container is None:
            return

        self.preview_container.clear()
        with self.preview_container:
            preview_df = self._build_preview_df()
            preview_title = (
                "Data Preview (first 5 rows)"
                if len(preview_df) > 5
                else "Data Preview (all rows)"
            )
            ui.label(preview_title).classes("text-sm text-grey-7")

            grid = ui.aggrid.from_polars(
                preview_df,
                theme="quartz",
                auto_size_columns=True,
            ).classes("w-full h-64")
            grid.on(
                "firstDataRendered",
                lambda: grid.run_grid_method("sizeColumnsToFit"),
            )

    def is_valid(self) -> bool:
        """Check if all required columns are mapped."""
        analyzer = self.session.selected_analyzer
        if not analyzer:
            return False

        required_columns = [col.name for col in analyzer.input.columns]
        mapped_columns = [
            col_name
            for col_name, (dropdown, _) in self.column_dropdowns.items()
            if dropdown.value
        ]

        return all(col in mapped_columns for col in required_columns)

    def save_state(self) -> bool:
        """Save column mapping to session."""
        final_mapping = {}
        for input_col_name, (dropdown, options) in self.column_dropdowns.items():
            if dropdown.value:
                final_mapping[input_col_name] = options[dropdown.value]

        self.session.column_mapping = final_mapping
        return True
