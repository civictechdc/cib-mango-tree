from io import BytesIO
from pathlib import Path

from pydantic import BaseModel, ConfigDict

from analyzer_interface import AnalyzerInterface, ParamValue
from app.project_context import ProjectContext
from gui.context import GUIContext
from importing.importer import ImporterSession
from storage import AnalysisModel


# Class for handling information that
# must persist throught a session
class GuiSession(BaseModel):
    """
    Application-wide session state container.

    Replaces module-level global variables with a type-safe,
    validated state container. Provides access to
    application context and workflow state.

    Attributes:
        context: Application context wrapping App instance
        current_project: Currently selected/active project
        selected_file_path: Path to file selected for import
        new_project_name: Name for project being created
        import_session: Active importer session for data preview
        selected_analyzer: ID of selected primary analyzer
        current_analysis: Currently selected/active analysis

    Example:
        ```python
        context = GUIContext(app=app)
        session = GuiSession(context=context)

        # Set project
        session.current_project = project

        # Access app
        projects = session.app.list_projects()
        ```
    """

    # Core context
    context: GUIContext

    # Workflow state - project creation
    current_project: ProjectContext | None = None
    selected_file_path: Path | None = None
    selected_file_name: str | None = None
    selected_file: BytesIO | None = None
    selected_file_content_type: str | None = None
    new_project_name: str | None = None
    import_session: ImporterSession | None = None

    # Workflow state - analysis
    selected_analyzer: AnalyzerInterface | None = None
    selected_analyzer_name: str | None = None
    column_mapping: dict[str, str] | None = None
    current_analysis: AnalysisModel | None = None
    analysis_params: dict[str, ParamValue] | None = None

    # Allow arbitrary types (for NiceGUI components, ImporterSession, etc.)
    model_config = ConfigDict(arbitrary_types_allowed=True)

    @property
    def app(self):
        """Access underlying App instance."""
        return self.context.app

    def reset_project_workflow(self) -> None:
        """Clear project creation workflow state."""
        self.new_project_name = None
        self.selected_file_path = None
        self.import_session = None

    def reset_analysis_workflow(self) -> None:
        """Clear analysis workflow state."""
        self.selected_analyzer = None
        self.selected_analyzer_name = None
        self.column_mapping = None
        self.current_analysis = None

    def validate_project_selected(self) -> bool:
        """Check if a project is currently selected."""
        return self.current_project is not None

    def validate_file_selected(self) -> bool:
        """Check if a file is currently selected."""
        return self.selected_file_path is not None

    def validate_project_name_set(self) -> bool:
        """Check if new project name is set."""
        return bool(self.new_project_name and self.new_project_name.strip())
