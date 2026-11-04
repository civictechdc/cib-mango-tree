from pydantic import BaseModel


class GuiRoutes(BaseModel):
    """NiceGUI page path constants."""

    root: str = "/"
    import_dataset: str = "/import_dataset"
    select_analyzer_fork: str = "/select_analyzer_fork"
    select_previous_analyzer: str = "/select_previous_analyzer"
    configure_analysis: str = "/configure_analysis"
    preview_dataset: str = "/preview_dataset"
    post_analysis: str = "/post_analysis"
    dashboard: str = "/dashboard"
    # Time-analysis-only drill-down (Explore → Compare users)
    dashboard_time_analysis_compare: str = "/dashboard/time_analysis/compare"


gui_routes = GuiRoutes()
