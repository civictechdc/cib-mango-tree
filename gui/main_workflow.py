"""
Main GUI workflow including all pages.
"""

from nicegui import ui

from app import App
from gui.base import GuiSession, gui_routes
from gui.context import GUIContext
from gui.dashboards import BaseDashboardPage, NgramsDashboardPage
from gui.pages import (
    AnalysisConfigPage,
    ConfigureAnalaysisParams,
    ConfigureAnalysisDatasetPage,
    ImportDatasetPage,
    NewProjectPage,
    PostAnalysisPage,
    PreviewDatasetPage,
    RunAnalysisPage,
    SelectAnalyzerForkPage,
    SelectNewAnalyzerPage,
    SelectPreviousAnalyzerPage,
    SelectProjectPage,
    StartPage,
)

# Maps primary analyzer IDs to their dashboard page classes.
# Add an entry here when a new dashboard is implemented.
_DASHBOARD_REGISTRY: dict[str, type[BaseDashboardPage]] = {
    "ngrams": NgramsDashboardPage,
}


def _render_dashboard_placeholder(session: GuiSession) -> None:
    """
    Fallback page shown when the selected analyzer has no dashboard yet.

    Reuses GuiPage infrastructure by creating a minimal inline page.
    """

    class _PlaceholderDashboard(BaseDashboardPage):
        def render_content(self) -> None:
            with (
                ui.column()
                .classes("items-center justify-center")
                .style("height: 80vh; width: 100%")
            ):
                ui.icon("bar_chart", size="4rem").classes("text-grey-5")
                ui.label("Dashboard coming soon").classes("text-h6 text-grey-6 q-mt-md")
                ui.label(
                    "A results dashboard for this analyzer is not yet available."
                ).classes("text-grey-5")

    page = _PlaceholderDashboard(session=session)
    page.render()


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
        page = AnalysisConfigPage(session=gui_session)
        page.render()

    @ui.page(gui_routes.select_analyzer)
    def select_analyzer():
        """New analyzer selection page using GuiPage abstraction."""
        page = SelectNewAnalyzerPage(session=gui_session)
        page.render()

    @ui.page(gui_routes.select_previous_analyzer)
    def select_previous_analyzer():
        """Previous analyzer selection page using GuiPage abstraction."""
        page = SelectPreviousAnalyzerPage(session=gui_session)
        page.render()

    @ui.page(gui_routes.configure_analysis_dataset)
    def configure_analysis_dataset():
        """Renders page where user selects dataset columns and previews."""
        page = ConfigureAnalysisDatasetPage(session=gui_session)
        page.render()

    @ui.page(gui_routes.configure_analysis_parameters)
    def configure_analysis_parameters():
        """Render page to allow user to configure analysis parameters."""
        page = ConfigureAnalaysisParams(session=gui_session)
        page.render()

    @ui.page(gui_routes.run_analysis)
    def run_analysis():
        """Render page that runs the analysis with selected parameters."""
        page = RunAnalysisPage(session=gui_session)
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
        dashboard_class = _DASHBOARD_REGISTRY.get(analyzer_id) if analyzer_id else None

        if dashboard_class is not None:
            page = dashboard_class(session=gui_session)
            page.render()
        else:
            # Placeholder shown while a dashboard for this analyzer is not yet built
            _render_dashboard_placeholder(gui_session)

    # Launch in native mode
    ui.run(
        native=True,
        title="CIB Mango Tree",
        favicon="🥭",
        reload=False,
    )
