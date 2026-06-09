"""
GUI context - similar to ViewContext but for NiceGUI.
"""

from pydantic import BaseModel, ConfigDict, Field

from cibmangotree.app import App


class GUIContext(BaseModel):
    """Context for GUI mode, wrapping the App instance."""

    app: App = Field(...)
    model_config = ConfigDict(arbitrary_types_allowed=True)
