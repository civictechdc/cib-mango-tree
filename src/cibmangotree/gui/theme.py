from pydantic import BaseModel, ConfigDict, Field

MANGO_DARK_GREEN = "#609949"
MANGO_ORANGE = "#f3921e"
MANGO_ORANGE_LIGHT = "#f9bc30"
ACCENT = "white"
CANCEL = "#424242"

# Chart colors (ECharts option dicts)
CHART_HIGHLIGHT = "#d62728"
TAB_10_PALETTE = [
    "#1f77b4",
    "#ff7f0e",
    "#2ca02c",
    CHART_HIGHLIGHT,
    "#9467bd",
    "#8c564b",
    "#e377c2",
    "#7f7f7f",
    "#bcbd22",
    "#17becf",
]
EDGE_COLOR_PAIR = "#B0B7C3"  # N == 1 (light grey)
EDGE_COLOR_GROUP_2_5 = "#1B9E77"  # 2 <= N <= 5 (teal/green)
EDGE_COLOR_GROUP_6_10 = "#D7268A"  # 6 <= N <= 10 (magenta)
EDGE_COLOR_GROUP_11_20 = "#8B2E8B"  # N >= 11 (incl. >20)


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
CARD_MAPPING = f"p-4 {CARD_FLAT}"
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
ROW_TOOLBAR_END = "w-full gap-4 mt-4 justify-end"

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
WIDTH_FULL_H_64 = "w-full h-64"
WIDTH_FULL_H_96 = "w-full h-96"
WIDTH_TOOLTIP = "w-64"
WIDTH_UNIT_SELECT = "w-32"
WIDTH_AMOUNT = "w-24"
WIDTH_SKIP_ROWS = "w-48"
SIZE_LOGO = "size-24 mb-4"
TABLE_PROJECTS = "w-full my-sticky-table"

TEXT_HEADING = "text-h6"
TEXT_MUTED = "text-grey-8"
TEXT_SECTION_HEADING = f"{TEXT_HEADING} mb-4"
TEXT_HEADING_MUTED = f"{TEXT_HEADING} {TEXT_MUTED}"
TEXT_DIALOG_TITLE = "text-h6 mb-2"
TEXT_DIALOG_LEAD = "w-full break-words text-lg mb-2"
TEXT_DIALOG_HEADER = "text-xl font-semibold"
TEXT_TOOLTIP_BODY = "text-base leading-relaxed whitespace-normal"
TEXT_FIELD_LABEL = "text-base font-bold"
TEXT_MUTED_MB_4 = f"{TEXT_MUTED} mb-4"
TEXT_MUTED_SM = f"text-sm {TEXT_MUTED}"
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
TEXT_NEGATIVE = "text-negative"
TEXT_NEGATIVE_MB_6 = "text-negative mb-6"
TEXT_SM_NEGATIVE = "text-sm text-negative"
TEXT_ERROR_SM = "text-negative font-bold text-sm"
SPACING_MB_4 = "mb-4"

ICON_INFO = "text-grey-7 cursor-pointer"

# Layout / page-level
FLEX_CENTER = "flex items-center"
FLEX_CENTER_GAP_2 = "flex items-center gap-2"
FLEX_CENTER_GAP_3 = "flex items-center gap-3"
ROW_HEADER = "w-full items-center justify-between"
ROW_GAP_4 = "gap-4"
ROW_GAP_4_END = "gap-4 justify-end"
ROW_FULL_CENTER = "w-full justify-center"
ROW_FULL_CENTER_GAP_2 = "w-full justify-center gap-2"
ROW_FULL_GAP_4 = "w-full gap-4"
ROW_FULL_ITEMS_GAP_4 = "w-full items-center gap-4"
ROW_SPACED = "w-full justify-between items-center"
ROW_CENTER_GAP_4_FULL = "items-center justify-center gap-4 w-full"
ROW_EXPLORE = "w-full items-stretch gap-4 flex-wrap"
ROW_LEGEND = "items-center gap-4 mb-2 flex-wrap justify-center"
ROW_LOADING = "w-full items-center justify-center gap-3 mt-4"
ROW_META_MUTED = f"text-body2 {TEXT_MUTED} gap-7"
COL_CENTERED_FULL = "items-center w-full"
COL_CONTENT_CENTER = "items-center justify-center gap-8"
COL_CONTENT_START = "items-center justify-start gap-8"
COL_FULL_GAP_2 = "w-full gap-2"
COL_GAP_3 = "gap-3"
COL_LOADING = "w-full items-center justify-center"
COL_PLACEHOLDER = "items-center justify-center"
COL_DASHBOARD = "w-3/4 p-4 gap-4"
BLOCK_PT_12 = "pt-12 w-full items-center"
BLOCK_PT_6 = "pt-6 w-full items-center"
BLOCK_PT_12_CENTER = "pt-12 flex justify-center w-full"
BLOCK_ANALYZER_GRID = "w-[64rem] max-w-full"
CARD_ANALYZER_DESC = "w-[40rem] shadow-none"
CARD_FLEX_1 = "flex-1"
SCROLL_MAX_H_72 = "max-h-72"
SCROLL_PAIR = "w-full h-96 mt-4"
WIDTH_QUARTER = "w-1/4"
WIDTH_FULL_WRAP = "w-full break-words"
LINK_BRAND = "inline-flex items-center no-underline"
LINK_ICON = "inline-flex items-center justify-center text-white no-underline size-5"
LOGO_BADGE = "bg-white rounded-full p-1.5"
SIZE_ICON_SM = "size-5"
SVG_FILL_FULL = "size-full fill-current"

# Text
TEXT_LG = "text-lg"
TEXT_H5 = "text-h5"
TEXT_FOOTER = "text-sm font-bold"
TEXT_BODY_MUTED = f"text-body2 {TEXT_MUTED}"
TEXT_BODY_MUTED_MB_2 = f"text-body2 {TEXT_MUTED} mb-2"
TEXT_BODY_NEGATIVE = "text-body2 text-negative"
TEXT_CAPTION_MUTED = f"text-caption {TEXT_MUTED}"
TEXT_MUTED_MT_4 = f"{TEXT_MUTED} mt-4"
TEXT_NEGATIVE_MT_4 = "text-negative mt-4"
TEXT_PLACEHOLDER_TITLE = f"{TEXT_HEADING} {TEXT_MUTED} mt-4"
SPACING_MB_6 = "mb-6"
ICON_MUTED = "text-grey-5"


# --- Inline style constants (NiceGUI .style()) ---------------------------

STYLE_CENTERED = "max-width: 960px; margin: 0 auto;"
STYLE_LABEL_MIN_WIDTH = "min-width: 160px"
STYLE_CARD_FLEX_MIN = "flex: 1 1 0; min-width: 160px"
STYLE_IMPORT_DIALOG = "min-width: 600px; max-width: 800px"
STYLE_EXPORT_DIALOG = "min-width: 500px; max-width: 700px"
STYLE_PROGRESS_DIALOG = "width: 600px; max-width: 90vw; padding: 2rem;"
STYLE_CHART_HEIGHT = "height: 320px"
STYLE_STATUS_ACCENT = f"color: {MANGO_ORANGE}"
STYLE_PROMPT = "font-size: 1.05rem"
STYLE_SPACE_BETWEEN = "justify-content: space-between"
STYLE_HIDDEN = "display: none;"
STYLE_BLOCK = "display: block;"
STYLE_MAX_WIDTH_800 = "max-width: 800px"
STYLE_HEIGHT_300 = "height: 300px"
STYLE_HEIGHT_350 = "height: 350px"
STYLE_HEIGHT_400 = "height: 400px"
STYLE_HEIGHT_500 = "height: 500px"
STYLE_CONTENT_DEFAULT = "height: 80vh; width: 100%"
STYLE_CONTENT_AUTO_PAD_2 = "height: auto; width: 100%; padding: 2rem"
STYLE_CONTENT_NARROW = f"{STYLE_CONTENT_DEFAULT}; max-width: 800px; margin: 0 auto"
STYLE_CONTENT_WIDE_PAD_1 = (
    "height: auto; width: 100%; max-width: 1200px; margin: 0 auto; padding: 1rem"
)
STYLE_CONTENT_WIDE_PAD_2 = (
    "height: auto; width: 100%; max-width: 1200px; margin: 0 auto; padding: 2rem"
)
STYLE_EXPLORE_SIDEBAR = "flex:1 1 220px; min-width:200px; max-width:320px;"
STYLE_EXPLORE_MAIN = "flex:3 1 360px; min-width:280px;"
STYLE_EXPLORE_CHART = "display:block; width:100%; min-width:100%; height:520px;"
STYLE_CLEAR = ""


def style_legend_swatch(color: str) -> str:
    """Inline style for a legend line swatch of the given chart color."""
    return f"width:18px;height:4px;border-radius:2px;background:{color};"


# Head HTML / page-level CSS snippets (ui.add_head_html / ui.add_css)
HEAD_HTML_STICKY_TABLE = """
            <style>
                .my-sticky-table {
                /* Window height minus the page's fixed furniture (header, footer,
                    padding, logo, button row = 488px). Re-measure if any of those
                    change. Floor keeps the table usable at the minimum window size. */
                    height: max(180px, calc(100vh - 496px));
                }
                .my-sticky-table thead tr th {
                    position: sticky;
                    z-index: 1;
                    background-color: white;
                }
                .my-sticky-table thead tr:first-child th {
                    top: 0;
                }
                .my-sticky-table thead tr th,
                .my-sticky-table tbody tr td {
                    font-size: 0.85rem;
                }
            </style>
        """

CSS_HASHTAGS_GRID = """
            .ag-row {
                cursor: pointer !important;
            }
            .ag-row-hover {
                background-color: #e3f2fd !important;
            }
            """

CSS_NGRAMS_GRID = """
            .ag-tooltip {
                white-space: normal !important;
                max-width: 450px !important;
                word-wrap: break-word !important;
            }
            .clickable-user-cell:hover {
                font-weight: 600 !important;
            }
        """
