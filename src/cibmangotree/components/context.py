from pydantic import BaseModel, ConfigDict

from cibmangotree.app import App
from cibmangotree.terminal_tools.inception import TerminalContext


class ViewContext(BaseModel):
    terminal: TerminalContext
    app: App
    model_config = ConfigDict(arbitrary_types_allowed=True)
