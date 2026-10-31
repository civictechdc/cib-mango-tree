"""
Main GUI workflow including all pages.
"""

import os

from nicegui import app as nicegui_app
from nicegui import ui

from cibmangotree.app import App
from cibmangotree.gui.context import GUIContext
from cibmangotree.gui.dashboards import PlaceholderDashboard, get_dashboard
from cibmangotree.gui.pages import (
    AnalysisConfigAndRunPage,
    ImportDatasetPage,
    PostAnalysisPage,
    PreviewDatasetPage,
    SelectAnalyzerForkPage,
    SelectPreviousAnalyzerPage,
    StartPage,
)
from cibmangotree.gui.routes import gui_routes
from cibmangotree.gui.session import GuiSession


def register_pages(app: App) -> GuiSession:
    """Register the real GUI routes and return the session they share.

    Split from gui_main so UI tests can open these pages without starting the
    native window. gui_main still calls this and then ui.run.
    """
    gui_context = GUIContext(app=app)
    gui_session = GuiSession(context=gui_context)

    @ui.page(gui_routes.root)
    def start_page():
        """Main/home page using GuiPage abstraction."""
        page = StartPage(session=gui_session)
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

    return gui_session


def gui_main(app: App):
    """
    Launch the NiceGUI interface with a minimal single screen.

    Args:
        app: The initialized App instance with storage and suite
    """
    register_pages(app)

    # GitHub Codespaces: serve in the browser (no native/pywebview desktop).
    if os.environ.get("CODESPACES") == "true":
        ui.run(
            native=False,
            host="0.0.0.0",
            port=8000,
            title="CIB Mango Tree",
            favicon="🥭",
            reload=False,
            show=False,
        )
        return

    nicegui_app.native.window_args["min_size"] = (1024, 710)
    ui.run(
        native=True,
        title="CIB Mango Tree",
        favicon="🥭",
        reload=False,
        window_size=(1060, 720),
    )
