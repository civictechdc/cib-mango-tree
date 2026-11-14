"""GUI styling authority: brand colors, Quasar roles/props, Tailwind classes, CSS.

IMPORT CONSTANTS FROM HERE; DO NOT HARD-CODE STYLE STRINGS IN GUI MODULES.

See docs/guides/contributing/styling.md.
"""

from pydantic import BaseModel, ConfigDict, Field

# ---------------------------------------------------------------------------
# Brand hexes — fed into GuiColors / ui.colors(); also used directly where
# NiceGUI/ECharts need a raw color (icons, chart series, mark lines).
# ---------------------------------------------------------------------------
MANGO_DARK_GREEN = "#609949"  # export/run success icons; GuiColors.primary
MANGO_ORANGE = "#f3921e"  # hashtag plots/window preview; GuiColors.mango_orange
MANGO_ORANGE_LIGHT = "#f9bc30"  # GuiColors.secondary only
ACCENT = "white"  # GuiColors.accent (header icon buttons)
CANCEL = "#424242"  # GuiColors.cancel; hashtag window-preview dashed lines

# ---------------------------------------------------------------------------
# Chart hexes — ECharts option dicts in analyzer dashboards (not Quasar slots).
# ---------------------------------------------------------------------------
# Shared red for highlights (hashtags Gini/plots, ngrams plots).
CHART_HIGHLIGHT = "#d62728"
CHART_LINE = "black"  # hashtags default series stroke/fill
CHART_BORDER = "white"  # ngrams scatter point borders
CHART_SHADOW = "rgba(0, 0, 0, 0.3)"  # hashtags/ngrams hover shadow
# Classic Tableau/matplotlib tab10 categorical palette for ngrams series colors
# (dashboards/ngrams/plots.py). Fourth entry reuses CHART_HIGHLIGHT.
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
# Time-coordination network edge colors by group size
# (dashboards/time_coordination/chart_utils.py).
EDGE_COLOR_PAIR = "#B0B7C3"  # N == 1 (light grey)
EDGE_COLOR_GROUP_2_5 = "#1B9E77"  # 2 <= N <= 5 (teal/green)
EDGE_COLOR_GROUP_6_10 = "#D7268A"  # 6 <= N <= 10 (magenta)
EDGE_COLOR_GROUP_11_20 = "#8B2E8B"  # N >= 11 (incl. >20)


class GuiColors(BaseModel):
    """Mango Tree brand colors registered with NiceGUI via GuiPage._setup_colors."""

    model_config = ConfigDict(frozen=True)

    primary: str = Field(default=MANGO_DARK_GREEN, description="Mango dark green")
    secondary: str = Field(default=MANGO_ORANGE_LIGHT, description="Mango orange light")
    accent: str = Field(default=ACCENT, description="Accent color")
    cancel: str = Field(default=CANCEL, description="Cancel/back/close action color")

    # Additional colors for reference
    mango_orange: str = Field(default=MANGO_ORANGE, description="Mango orange")


class GuiURLS(BaseModel):
    """External links rendered in the page footer (base.py)."""

    model_config = ConfigDict(frozen=True)

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


# ---------------------------------------------------------------------------
# Quasar color roles — NiceGUI color=... on buttons, icons, notifies.
# Names match slots registered in GuiPage._setup_colors (negative is built-in).
# Used across pages/, components/, and dashboard action chrome.
# ---------------------------------------------------------------------------
COLOR_PRIMARY = "primary"
COLOR_SECONDARY = "secondary"
COLOR_ACCENT = "accent"
COLOR_CANCEL = "cancel"
COLOR_MANGO_ORANGE = "mango-orange"
COLOR_NEGATIVE = "negative"
COLOR_GREY = "grey"  # toggle inactive (group mode)
COLOR_RED = "red"  # toggle inactive (standalone mode)


class GuiProps(BaseModel):
    """Quasar / NiceGUI .props(...) presentation flags."""

    model_config = ConfigDict(frozen=True)

    flat: str = Field(
        default="flat",
        description="Header/back/exit dialogs; stepper Back; ngrams cancel",
    )
    outline: str = Field(
        default="outline",
        description="Cancel/close buttons in dialogs and export/import",
    )
    unelevated: str = Field(
        default="unelevated",
        description="Time-coordination dashboard chrome",
    )
    no_caps: str = Field(
        default="no-caps",
        description="Dataset preview action buttons",
    )
    dense: str = Field(
        default="dense",
        description="Time-coordination controls",
    )
    flat_round_dense: str = Field(
        default="flat round dense",
        description="Ngrams dialog close icon button",
    )
    outline_dense: str = Field(
        default="outline dense",
        description="Ngrams secondary actions",
    )
    disable: str = Field(
        default="disable",
        description="Start page Open/Delete until a row is selected",
    )
    persistent: str = Field(
        default="persistent",
        description="Analysis run progress dialog",
    )
    use_chips: str = Field(
        default="use-chips",
        description="Column mapping step selects",
    )
    color_primary: str = Field(
        default=f"color={COLOR_PRIMARY}",
        description="Toggle active",
    )
    color_grey: str = Field(
        default=f"color={COLOR_GREY}",
        description="Toggle inactive (group)",
    )
    color_red: str = Field(
        default=f"color={COLOR_RED}",
        description="Toggle inactive (standalone)",
    )
    instant_feedback: str = Field(
        default="instant-feedback",
        description="Export progress bar",
    )
    stepper: str = Field(
        default="horizontal animated",
        description="Analysis config and run stepper",
    )
    clearable_off: str = Field(
        default='clearable autocomplete="off"',
        description="Ngrams search input",
    )
    tooltip_offset: str = Field(
        default='anchor="bottom middle" self="top middle" :offset="[210, 8]"',
        description="Import options info tooltips",
    )
    table_sticky: str = Field(
        default="flat bordered separator='horizontal' sticky-header",
        description="Start page projects table",
    )


class GuiConstants(BaseModel):
    """Container for colors, urls, and props."""

    model_config = ConfigDict(arbitrary_types_allowed=True)

    colors: GuiColors = Field(...)
    urls: GuiURLS = Field(...)
    props: GuiProps = Field(...)


# Singletons — used by base.py / GUI modules; gui_constants for tests.
gui_colors = GuiColors()
gui_urls = GuiURLS()
gui_props = GuiProps()
gui_constants = GuiConstants(colors=gui_colors, urls=gui_urls, props=gui_props)

# ---------------------------------------------------------------------------
# Tailwind / Quasar class strings — NiceGUI .classes(...)
# Grouped by layout role. Prefer composing related CARD_/ROW_/COL_ values.
# ---------------------------------------------------------------------------

SPACING_MB_4 = "mb-4"
SPACING_MB_6 = "mb-6"

# Cards — analysis workflow, dialogs, progress UI
CARD_FLAT = "shadow-none border border-gray-200"
CARD_CONTENT = f"w-full p-4 {CARD_FLAT}"  # run_step summary
CARD_PARAM = f"w-72 p-4 {CARD_FLAT}"  # analysis.py param cards
CARD_MAPPING = f"p-4 {CARD_FLAT}"  # column_mapping_step cards
CARD_DIALOG_FULL = "w-full"  # export / manage-analyses dialogs
CARD_DIALOG_PADDED = "w-full p-3"  # import_options dialog
CARD_DIALOG_MD = "w-96"  # new_project_dialog

# Rows — shared action/toolbars and form rows (components + workflow steps)
ITEMS_CENTER = "items-center"
JUSTIFY_CENTER = "justify-center"
CARD_DIALOG_NARROW = f"w-80 {ITEMS_CENTER}"  # exit_confirmation
CARD_PROGRESS = f"{ITEMS_CENTER} {JUSTIFY_CENTER} gap-6"  # run_step progress dialog
ROW_CENTERED = f"w-full {ITEMS_CENTER}"
ROW_CENTERED_GAP = f"{ITEMS_CENTER} gap-1"
ROW_LAYOUT = f"{ROW_CENTERED} gap-2 mb-2"  # import_options labeled rows
ROW_ACTIONS = "w-full justify-end gap-2"  # dialog footers
ROW_ACTIONS_MT_3 = f"{ROW_ACTIONS} mt-3"
ROW_ACTIONS_MT_4 = f"{ROW_ACTIONS} mt-4"
ROW_WRAP_CENTER = f"flex-wrap gap-6 {JUSTIFY_CENTER} w-full"  # param/column card grids
ROW_GAP_2 = "gap-2"
ROW_GAP_MT = f"{ROW_GAP_2} mt-2 w-full"  # analysis time-binning controls
ROW_GAP_MT_4 = "gap-4 mt-4"  # run_step dialog actions
ROW_INLINE = f"{ITEMS_CENTER} gap-2"  # export/run status rows
ROW_STATUS = f"{ROW_INLINE} {SPACING_MB_4}"  # export complete header
ROW_TOOLBAR_END = "w-full gap-4 mt-4 justify-end"  # start page Open/Delete

# Columns — stacks and step bodies
COL_STACK = "w-full gap-1"
COL_STACK_MB_4 = f"{COL_STACK} {SPACING_MB_4}"  # export checkbox/status stacks
COL_STACK_MT_2 = f"{COL_STACK} mt-2"  # run_step log list
COL_STACK_MT_4 = f"{COL_STACK} mt-4"  # run_step step list
COL_STEP_BODY = f"w-full {ITEMS_CENTER} gap-6"  # column/params/run step shells
COL_GAP_2 = "gap-2"
COL_FULL = "w-full"

# Widths / sizes — inputs, grids, start-page chrome
WIDTH_FULL = "w-full"
WIDTH_FULL_MT_2 = f"{WIDTH_FULL} mt-2"
WIDTH_FULL_MB_4 = f"{WIDTH_FULL} {SPACING_MB_4}"
WIDTH_FULL_H_64 = f"{WIDTH_FULL} h-64"  # preview/previous/dataset grids
WIDTH_FULL_H_96 = f"{WIDTH_FULL} h-96"  # manage_analyses grid
WIDTH_TOOLTIP = "w-64"
WIDTH_UNIT_SELECT = "w-32"  # analysis time-binning unit
WIDTH_AMOUNT = "w-24"  # analysis time-binning amount
WIDTH_SKIP_ROWS = "w-48"  # import_options skip-rows input
SIZE_LOGO = f"size-24 {SPACING_MB_4}"  # start page hero logo
TABLE_PROJECTS = (
    "w-full my-sticky-table"  # start page; pairs with HEAD_HTML_STICKY_TABLE
)

# Typography / muted / error text — workflow steps, dialogs, forms
TEXT_HEADING = "text-h6"
TEXT_MUTED = "text-grey-8"
TEXT_BASE = "text-base"
TEXT_BODY2 = "text-body2"
TEXT_SM = "text-sm"
TEXT_BOLD = "font-bold"
TEXT_WEIGHT_MEDIUM = "font-medium"
TEXT_NEGATIVE = "text-negative"
TEXT_SECTION_HEADING = f"{TEXT_HEADING} {SPACING_MB_4}"
TEXT_HEADING_MUTED = f"{TEXT_HEADING} {TEXT_MUTED}"  # start "Projects"
TEXT_DIALOG_TITLE = f"{TEXT_HEADING} mb-2"  # import_options
TEXT_DIALOG_LEAD = "w-full break-words text-lg mb-2"
TEXT_DIALOG_HEADER = "text-xl font-semibold"  # run_step analyzer name
TEXT_TOOLTIP_BODY = f"{TEXT_BASE} leading-relaxed whitespace-normal"
TEXT_FIELD_LABEL = f"{TEXT_BASE} {TEXT_BOLD}"
TEXT_MUTED_MB_4 = f"{TEXT_MUTED} {SPACING_MB_4}"
TEXT_MUTED_SM = f"{TEXT_SM} {TEXT_MUTED}"
TEXT_STEP_TITLE = f"text-lg {TEXT_BOLD} {SPACING_MB_4}"  # workflow step titles
TEXT_SUBTITLE_BOLD_MT = f"text-subtitle2 {TEXT_BOLD} mt-2"  # export sections
TEXT_CENTER_MB_4 = f"text-center {SPACING_MB_4}"  # exit_confirmation message
TEXT_STATUS = f"{TEXT_BASE} {TEXT_WEIGHT_MEDIUM}"  # run_step status line
TEXT_BASE_MB_4 = f"{TEXT_BASE} {SPACING_MB_4}"
TEXT_HINT_SM = f"{SPACING_MB_4} {TEXT_SM}"
TEXT_MUTED_SM_MB_2 = f"{TEXT_SM} {TEXT_MUTED} mb-2"
TEXT_MUTED_SM_MT_2 = f"{TEXT_SM} {TEXT_MUTED} mt-2"
TEXT_NEGATIVE_MB_6 = f"{TEXT_NEGATIVE} {SPACING_MB_6}"  # delete confirmations
TEXT_SM_NEGATIVE = f"{TEXT_SM} {TEXT_NEGATIVE}"
TEXT_ERROR_SM = f"{TEXT_NEGATIVE} {TEXT_BOLD} {TEXT_SM}"  # run_step errors

ICON_INFO = "text-grey-7 cursor-pointer"  # param/import/column info icons

# ---------------------------------------------------------------------------
# Page- and dashboard-level class layouts (base header/footer, dashboards,
# analyzer select, choice forks). More specific than the shared ROW_/COL_ set.
# ---------------------------------------------------------------------------
FLEX_CENTER = f"flex {ITEMS_CENTER}"  # base.py header/footer clusters
FLEX_CENTER_GAP_2 = f"{FLEX_CENTER} {ROW_GAP_2}"
FLEX_CENTER_GAP_3 = f"{FLEX_CENTER} gap-3"
ROW_HEADER = f"{WIDTH_FULL} {ITEMS_CENTER} justify-between"  # base.py header
ROW_GAP_4 = "gap-4"  # choice_fork / analysis_post / analyzer_previous
ROW_GAP_4_END = f"{ROW_GAP_4} justify-end"  # ngrams confirm dialog
ROW_FULL_CENTER = f"{WIDTH_FULL} {JUSTIFY_CENTER}"  # hashtags/ngrams dashboard shells
ROW_FULL_CENTER_GAP_2 = f"{ROW_FULL_CENTER} {ROW_GAP_2}"  # dataset_preview
ROW_FULL_GAP_4 = f"{WIDTH_FULL} {ROW_GAP_4}"
ROW_FULL_ITEMS_GAP_4 = f"{WIDTH_FULL} {ITEMS_CENTER} {ROW_GAP_4}"
ROW_SPACED = f"{WIDTH_FULL} justify-between {ITEMS_CENTER}"
ROW_CENTER_GAP_4_FULL = (
    f"{ITEMS_CENTER} {JUSTIFY_CENTER} {ROW_GAP_4} {WIDTH_FULL}"  # analyzer_step
)
ROW_EXPLORE = f"{WIDTH_FULL} items-stretch {ROW_GAP_4} flex-wrap"  # time-coordination
ROW_LEGEND = f"{ITEMS_CENTER} {ROW_GAP_4} mb-2 flex-wrap {JUSTIFY_CENTER}"
ROW_LOADING = f"{WIDTH_FULL} {ITEMS_CENTER} {JUSTIFY_CENTER} gap-3 mt-4"  # compare_page
ROW_META_MUTED = f"{TEXT_BODY2} {TEXT_MUTED} gap-7"  # ngrams meta row
COL_CENTERED_FULL = f"{ITEMS_CENTER} {WIDTH_FULL}"
COL_CONTENT_CENTER = (
    f"{ITEMS_CENTER} {JUSTIFY_CENTER} gap-8"  # GuiPage.centered_content
)
COL_CONTENT_START = f"{ITEMS_CENTER} justify-start gap-8"
COL_FULL_GAP_2 = f"{WIDTH_FULL} {ROW_GAP_2}"
COL_GAP_3 = "gap-3"
COL_LOADING = f"{WIDTH_FULL} {ITEMS_CENTER} {JUSTIFY_CENTER}"  # base_dashboard loading
COL_PLACEHOLDER = f"{ITEMS_CENTER} {JUSTIFY_CENTER}"
COL_DASHBOARD = f"w-3/4 p-4 {ROW_GAP_4}"  # hashtags/ngrams main column
BLOCK_PT_12 = f"pt-12 {WIDTH_FULL} {ITEMS_CENTER}"  # analysis_config_and_run
BLOCK_PT_6 = f"pt-6 {WIDTH_FULL} {ITEMS_CENTER}"
BLOCK_PT_12_CENTER = f"pt-12 flex {JUSTIFY_CENTER} {WIDTH_FULL}"  # analyzer_step
BLOCK_ANALYZER_GRID = "w-[64rem] max-w-full"
CARD_ANALYZER_DESC = "w-[40rem] shadow-none"
CARD_FLEX_1 = "flex-1"  # hashtags side panels
SCROLL_MAX_H_72 = "max-h-72"  # analyzer_step description
SCROLL_PAIR = f"{WIDTH_FULL_H_96} mt-4"  # time-coordination compare posts
WIDTH_QUARTER = "w-1/4"  # ngrams sidebar
WIDTH_FULL_WRAP = f"{WIDTH_FULL} break-words"
LINK_BRAND = f"inline-flex {ITEMS_CENTER} no-underline"  # base footer
LINK_ICON = (
    f"inline-flex {ITEMS_CENTER} {JUSTIFY_CENTER} text-white no-underline size-5"
)
LOGO_BADGE = "bg-white rounded-full p-1.5"
SIZE_ICON_SM = "size-5"
SVG_FILL_FULL = "size-full fill-current"

# Dashboard / page secondary typography (beyond the shared TEXT_* set above)
TEXT_LG = "text-lg"
TEXT_H5 = "text-h5"  # time-coordination titles
TEXT_FOOTER = f"{TEXT_SM} {TEXT_BOLD}"  # base.py footer labels
TEXT_BODY_MUTED = f"{TEXT_BODY2} {TEXT_MUTED}"
TEXT_BODY_MUTED_MB_2 = f"{TEXT_BODY2} {TEXT_MUTED} mb-2"
TEXT_BODY_NEGATIVE = f"{TEXT_BODY2} {TEXT_NEGATIVE}"
TEXT_CAPTION_MUTED = f"text-caption {TEXT_MUTED}"
TEXT_MUTED_MT_4 = f"{TEXT_MUTED} mt-4"
TEXT_NEGATIVE_MT_4 = "text-negative mt-4"
TEXT_PLACEHOLDER_TITLE = f"{TEXT_HEADING} {TEXT_MUTED} mt-4"
ICON_MUTED = "text-grey-5"  # placeholder dashboard

# ---------------------------------------------------------------------------
# Inline CSS — NiceGUI .style(...)
# ---------------------------------------------------------------------------
STYLE_CENTERED = "max-width: 960px; margin: 0 auto;"  # workflow steps + start
STYLE_LABEL_MIN_WIDTH = "min-width: 160px"  # import_options labels
STYLE_CARD_FLEX_MIN = "flex: 1 1 0; min-width: 160px"  # column_mapping cards
STYLE_IMPORT_DIALOG = "min-width: 600px; max-width: 800px"
STYLE_EXPORT_DIALOG = "min-width: 500px; max-width: 700px"
STYLE_PROGRESS_DIALOG = "width: 600px; max-width: 90vw; padding: 2rem;"  # run_step
STYLE_CHART_HEIGHT = "height: 320px"  # params_step window preview
STYLE_STATUS_ACCENT = f"color: {MANGO_ORANGE}"  # run_step status text
STYLE_PROMPT = "font-size: 1.05rem"  # choice_fork / analysis_post prompts
STYLE_SPACE_BETWEEN = "justify-content: space-between"  # base footer
STYLE_HIDDEN = "display: none;"  # base_dashboard loading swap
STYLE_BLOCK = "display: block;"
STYLE_MAX_WIDTH_800 = "max-width: 800px"  # ngrams
STYLE_HEIGHT_300 = "height: 300px"  # hashtags charts
STYLE_HEIGHT_350 = "height: 350px"
STYLE_HEIGHT_400 = "height: 400px"  # ngrams
STYLE_HEIGHT_500 = "height: 500px"  # base_dashboard / ngrams
STYLE_CONTENT_DEFAULT = "height: 80vh; width: 100%"  # GuiPage.centered_content
STYLE_CONTENT_AUTO_PAD_2 = "height: auto; width: 100%; padding: 2rem"  # start
STYLE_CONTENT_NARROW = f"{STYLE_CONTENT_DEFAULT}; max-width: 800px; margin: 0 auto"
STYLE_CONTENT_WIDE_PAD_1 = "height: auto; width: 100%; max-width: 1200px; margin: 0 auto; padding: 1rem"  # dataset_preview
STYLE_CONTENT_WIDE_PAD_2 = "height: auto; width: 100%; max-width: 1200px; margin: 0 auto; padding: 2rem"  # analysis_config_and_run
# Time-coordination explore layout
STYLE_EXPLORE_SIDEBAR = "flex:1 1 220px; min-width:200px; max-width:320px;"
STYLE_EXPLORE_MAIN = "flex:3 1 360px; min-width:280px;"
STYLE_EXPLORE_CHART = "display:block; width:100%; min-width:100%; height:520px;"
STYLE_CLEAR = ""  # clear prior inline style (run_step step labels)


def style_legend_swatch(color: str) -> str:
    """Inline style for a legend line swatch (time_coordination dashboard)."""
    return f"width:18px;height:4px;border-radius:2px;background:{color};"


# ---------------------------------------------------------------------------
# Page-level CSS blobs — ui.add_head_html / ui.add_css (not .style()).
# ---------------------------------------------------------------------------
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
        """  # pages/start.py projects table

CSS_HASHTAGS_GRID = """
            .ag-row {
                cursor: pointer !important;
            }
            .ag-row-hover {
                background-color: #e3f2fd !important;
            }
            """  # dashboards/hashtags/dashboard.py

CSS_NGRAMS_GRID = """
            .ag-tooltip {
                white-space: normal !important;
                max-width: 450px !important;
                word-wrap: break-word !important;
            }
            .clickable-user-cell:hover {
                font-weight: 600 !important;
            }
        """  # dashboards/ngrams/dashboard.py
