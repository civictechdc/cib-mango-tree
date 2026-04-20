from pydantic import BaseModel, ConfigDict, Field

MANGO_DARK_GREEN = "#609949"
MANGO_ORANGE = "#f3921e"
MANGO_ORANGE_LIGHT = "#f9bc30"
ACCENT = "white"


class GuiColors(BaseModel):
    """Mango Tree brand colors"""

    model_config = ConfigDict(frozen=True)

    primary: str = Field(default=MANGO_DARK_GREEN, description="Mango dark green")
    secondary: str = Field(default=MANGO_ORANGE_LIGHT, description="Mango orange light")
    accent: str = Field(default=ACCENT, description="Accent color")

    # Additional colors for reference
    mango_orange: str = Field(default=MANGO_ORANGE, description="Mango orange")


# Class for Managing Constants (colors and links)
class GuiURLS(BaseModel):
    """UI URL constants."""

    model_config = ConfigDict(frozen=True)

    # External URLs
    github_url: str = Field(
        default="https://github.com/civictechdc/cib-mango-tree",
        description="GitHub repository URL",
    )
    instagram_url: str = Field(
        default="https://www.instagram.com/cibmangotree",
        description="Instagram profile URL",
    )


class GuiConstants(BaseModel):
    """Container for both colors and urls"""

    model_config = ConfigDict(arbitrary_types_allowed=True)

    colors: GuiColors
    urls: GuiURLS


# Singleton instances for easy access in other modules
gui_colors = GuiColors()
gui_urls = GuiURLS()
gui_constants = GuiConstants(colors=gui_colors, urls=gui_urls)
