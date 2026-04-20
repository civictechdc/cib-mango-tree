from pydantic import BaseModel


class GuiRoutes(BaseModel):
    """Container for"""

    root: str = "/"
    import_dataset: str = "/import_dataset"
    new_project: str = "/new_project"
    select_project: str = "/select_project"
    select_analyzer_fork: str = "/select_analyzer_fork"
    select_previous_analyzer: str = "/select_previous_analyzer"
    configure_analysis: str = "/configure_analysis"
    preview_dataset: str = "/preview_dataset"
    post_analysis: str = "/post_analysis"
    dashboard: str = "/dashboard"


gui_routes = GuiRoutes()
