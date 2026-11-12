from pydantic import BaseModel, ConfigDict, Field

MANGO_DARK_GREEN = "#609949"
MANGO_ORANGE = "#f3921e"
MANGO_ORANGE_LIGHT = "#f9bc30"
ACCENT = "white"
CANCEL = "#424242"


class GuiColors(BaseModel):
    """Mango Tree brand colors"""

    model_config = ConfigDict(frozen=True)

    primary: str = Field(default=MANGO_DARK_GREEN, description="Mango dark green")
    secondary: str = Field(default=MANGO_ORANGE_LIGHT, description="Mango orange light")
    accent: str = Field(default=ACCENT, description="Accent color")
    cancel: str = Field(default=CANCEL, description="Cancel/back/close action color")

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
CARD_DIALOG_FULL = "w-full"
CARD_DIALOG_PADDED = "w-full p-3"
CARD_DIALOG_NARROW = "w-80 items-center"
CARD_DIALOG_MD = "w-96"
CARD_PROGRESS = "items-center justify-center gap-6"

ROW_CENTERED = "w-full items-center"
ROW_CENTERED_GAP = "items-center gap-1"
ROW_LAYOUT = f"{ROW_CENTERED} gap-2 mb-2"
ROW_ACTIONS = "w-full justify-end gap-2"
ROW_ACTIONS_MT_3 = f"{ROW_ACTIONS} mt-3"
ROW_ACTIONS_MT_4 = f"{ROW_ACTIONS} mt-4"
ROW_WRAP_CENTER = "flex-wrap gap-6 justify-center w-full"
ROW_GAP_2 = "gap-2"
ROW_GAP_MT = "gap-2 mt-2 w-full"
ROW_GAP_MT_4 = "gap-4 mt-4"
ROW_INLINE = "items-center gap-2"
ROW_STATUS = "items-center gap-2 mb-4"

COL_STACK = "w-full gap-1"
COL_STACK_MB_4 = f"{COL_STACK} mb-4"
COL_STACK_MT_2 = f"{COL_STACK} mt-2"
COL_STACK_MT_4 = f"{COL_STACK} mt-4"
COL_STEP_BODY = "w-full items-center gap-6"
COL_GAP_2 = "gap-2"
COL_FULL = "w-full"

WIDTH_FULL = "w-full"
WIDTH_FULL_MT_2 = "w-full mt-2"
WIDTH_FULL_MB_4 = "w-full mb-4"
WIDTH_TOOLTIP = "w-64"
WIDTH_UNIT_SELECT = "w-32"
WIDTH_AMOUNT = "w-24"
WIDTH_SKIP_ROWS = "w-48"

TEXT_HEADING = "text-h6"
TEXT_SECTION_HEADING = f"{TEXT_HEADING} mb-4"
TEXT_DIALOG_TITLE = "text-h6 mb-2"
TEXT_DIALOG_LEAD = "w-full break-words text-lg mb-2"
TEXT_DIALOG_HEADER = "text-xl font-semibold"
TEXT_TOOLTIP_BODY = "text-base leading-relaxed whitespace-normal"
TEXT_FIELD_LABEL = "text-base font-bold"
TEXT_MUTED = "text-grey-8"
TEXT_STEP_TITLE = "text-lg font-bold mb-4"
TEXT_SUBTITLE_BOLD_MT = "text-subtitle2 font-bold mt-2"
TEXT_CENTER_MB_4 = "text-center mb-4"
TEXT_STATUS = "text-base font-medium"
TEXT_BASE = "text-base"
TEXT_BASE_MB_4 = "text-base mb-4"
TEXT_SM = "text-sm"
TEXT_HINT_SM = "mb-4 text-sm"
TEXT_MUTED_SM_MB_2 = f"text-sm {TEXT_MUTED} mb-2"
TEXT_MUTED_SM_MT_2 = f"text-sm {TEXT_MUTED} mt-2"
TEXT_BOLD = "font-bold"
TEXT_WEIGHT_MEDIUM = "font-medium"
TEXT_ERROR_SM = "text-negative font-bold text-sm"
SPACING_MB_4 = "mb-4"

ICON_INFO = "text-grey-7 cursor-pointer"


# --- Inline style constants (NiceGUI .style()) ---------------------------

STYLE_CENTERED = "max-width: 960px; margin: 0 auto;"
STYLE_LABEL_MIN_WIDTH = "min-width: 160px"
STYLE_IMPORT_DIALOG = "min-width: 600px; max-width: 800px"
STYLE_EXPORT_DIALOG = "min-width: 500px; max-width: 700px"
STYLE_PROGRESS_DIALOG = "width: 600px; max-width: 90vw; padding: 2rem;"
STYLE_STATUS_ACCENT = f"color: {MANGO_ORANGE}"
STYLE_CLEAR = ""
