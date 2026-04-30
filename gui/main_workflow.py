"""
Main GUI workflow including all pages.
"""

from nicegui import ui

from app import App
from gui.context import GUIContext
from gui.dashboards import PlaceholderDashboard, get_dashboard
from gui.pages import (
    AnalysisConfigAndRunPage,
    ImportDatasetPage,
    NewProjectPage,
    PostAnalysisPage,
    PreviewDatasetPage,
    SelectAnalyzerForkPage,
    SelectPreviousAnalyzerPage,
    SelectProjectPage,
    StartPage,
)
from gui.routes import gui_routes
from gui.session import GuiSession


# maing GUI entry point
def gui_main(app: App):
    """
    Launch the NiceGUI interface with a minimal single screen.

    Args:
        app: The initialized App instance with storage and suite
    """

    # Initialize GUI session for state management
    gui_context = GUIContext(app=app)
    gui_session = GuiSession(context=gui_context)

    @ui.page(gui_routes.root)
    def start_page():
        """Main/home page using GuiPage abstraction."""
        page = StartPage(session=gui_session)
        page.render()

    @ui.page(gui_routes.select_project)
    def select_project_page():
        """Sub-page showing list of existing projects using GuiPage abstraction."""
        page = SelectProjectPage(session=gui_session)
        page.render()

    @ui.page(gui_routes.new_project)
    def new_project():
        """Sub-page for creating a new project name before importing dataset"""
        page = NewProjectPage(session=gui_session)
        page.render()

    @ui.page(gui_routes.import_dataset)
    def dataset_importing():
        """Sub-page for importing dataset using GuiPage abstraction."""
        page = ImportDatasetPage(session=gui_session)
        page.render()

    @ui.page(gui_routes.preview_dataset)
    def preview_dataset():
        """Sub-page for rendering preview of the imported dataset"""
        page = PreviewDatasetPage(session=gui_session)
        page.render()

    @ui.page(gui_routes.select_analyzer_fork)
    def select_analyzer_fork():
        page = SelectAnalyzerForkPage(session=gui_session)
        page.render()

    @ui.page(gui_routes.configure_analysis)
    def configure_analysis():
        """Combined analysis configuration page with stepper."""
        page = AnalysisConfigAndRunPage(session=gui_session)
        page.render()

    @ui.page(gui_routes.select_previous_analyzer)
    def select_previous_analyzer():
        """Previous analyzer selection page using GuiPage abstraction."""
        page = SelectPreviousAnalyzerPage(session=gui_session)
        page.render()

    @ui.page(gui_routes.post_analysis)
    def post_analysis():
        """Show options once analysis completes."""
        page = PostAnalysisPage(session=gui_session)
        page.render()

    @ui.page(gui_routes.dashboard)
    def dashboard():
        """
        Results dashboard page.

        Dispatches to the correct analyzer-specific dashboard based on
        the currently selected analyzer stored in the session.
        Falls back to a 'not yet available' notice for analyzers that
        do not have a dashboard implemented yet.
        """
        analyzer_id = (
            gui_session.selected_analyzer.id if gui_session.selected_analyzer else None
        )
        dashboard_class = get_dashboard(analyzer_id)

        if dashboard_class is not None:
            page = dashboard_class(session=gui_session)
            page.render()
        else:
            PlaceholderDashboard(session=gui_session).render()

    # Launch in native mode
    ui.run(
        native=True,
        title="CIB Mango Tree",
        favicon="🥭",
        reload=False,
    )
