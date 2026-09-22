from pydantic import BaseModel, ConfigDict, Field

MANGO_DARK_GREEN = "#609949"
MANGO_ORANGE = "#f3921e"
MANGO_ORANGE_LIGHT = "#f9bc30"
ACCENT = "white"
CANCEL_RED = "#d32f2f"
PAGE_BACKGROUND = "#ffffff"
CHART_HIGHLIGHT = "#d62728"


class GuiColors(BaseModel):
    """Mango Tree brand colors"""

    model_config = ConfigDict(frozen=True)

    primary: str = Field(default=MANGO_DARK_GREEN, description="Mango dark green")
    secondary: str = Field(default=MANGO_ORANGE_LIGHT, description="Mango orange light")
    accent: str = Field(default=ACCENT, description="Accent color")

    cancel: str = Field(
        default=CANCEL_RED, description="Cancel/back/close action color"
    )

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
    website_url: str = Field(
        default="https://cibmangotree.org",
        description="Official website URL",
    )


class GuiConstants(BaseModel):
    """Container for both colors and urls"""

    model_config = ConfigDict(arbitrary_types_allowed=True)

    colors: GuiColors = Field(...)
    urls: GuiURLS = Field(...)


# Singleton instances for easy access in other modules
gui_colors = GuiColors()
gui_urls = GuiURLS()
gui_constants = GuiConstants(colors=gui_colors, urls=gui_urls)

# --- Class-string constants (NiceGUI .classes()) -------------------------

CARD_FLAT = "shadow-none border border-gray-200"
CARD_CONTENT = f"w-full p-4 {CARD_FLAT}"
CARD_PARAM = f"w-72 p-4 {CARD_FLAT}"

ROW_CENTERED = "w-full items-center"
ROW_LAYOUT = f"{ROW_CENTERED} gap-2 mb-2"
ROW_ACTIONS = "w-full justify-end gap-2"
ROW_LABEL_ICON = "items-center gap-1"
COL_STACK = "w-full gap-1"

TEXT_MUTED = "text-grey-8"
TEXT_HEADING = "text-h6"
TEXT_SECTION_HEADING = f"{TEXT_HEADING} mb-4"
TEXT_TOOLTIP_BODY = "text-base leading-relaxed whitespace-normal"
TEXT_FIELD_LABEL = "text-base font-bold"
TEXT_STEP_TITLE = "text-lg font-bold mb-4"
TEXT_HINT = f"text-body2 {TEXT_MUTED}"
TEXT_WARNING_NOTE = "text-warning mb-6"
ICON_INFO = "text-grey-7 cursor-pointer"
ICON_DECORATIVE = "text-grey-5"


# --- Inline style constants (NiceGUI .style()) ---------------------------

STYLE_CENTERED = "max-width: 960px; margin: 0 auto;"
STYLE_LABEL_GUTTER = "min-width: 160px"
