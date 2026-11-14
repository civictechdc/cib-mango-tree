"""Behavior tests for gui.theme brand constants."""

from cibmangotree.gui.theme import (
    gui_colors,
    gui_constants,
    gui_props,
    gui_urls,
)


def test_gui_colors_defaults_match_brand_constants() -> None:
    assert gui_colors.brand_primary == "#2a4a23"
    assert gui_colors.brand_secondary == "#4e823b"
    assert gui_colors.brand_accent == "#f7ba2d"
    assert gui_colors.brand_dark == "#2a4a23"
    assert gui_colors.brand_cancel == "#424242"
    assert gui_colors.brand_progress == "#f3921e"
    assert gui_colors.status_positive == "#4e823b"
    assert gui_colors.status_negative == "#bc3a11"
    assert gui_colors.status_warning == "#f7ba2d"
    assert gui_colors.status_info == "#9fb8e0"
    assert gui_colors.grey == "#9e9e9e"
    assert gui_colors.red == "#f44336"
    assert gui_colors.chart_color_1 == "#325caa"
    assert gui_colors.chart_color_2 == "#b8bec8"
    assert gui_colors.chart_color_3 == "#b0c860"
    assert gui_colors.chart_color_4 == "#d42483"
    assert gui_colors.chart_color_5 == "#ca6c38"
    assert gui_colors.chart_highlight == "#d62728"
    assert gui_colors.chart_line == "black"
    assert gui_colors.chart_border == "white"
    assert gui_colors.chart_shadow == "rgba(0, 0, 0, 0.3)"
    assert gui_colors.tab_10_palette_0 == "#1f77b4"
    assert gui_colors.tab_10_palette_3 == gui_colors.chart_highlight
    assert len(gui_colors.tab_10_palette) == 10
    assert gui_colors.tab_10_palette[3] == gui_colors.chart_highlight


def test_gui_props_defaults() -> None:
    assert gui_props.flat == "flat"
    assert gui_props.outline == "outline"


def test_gui_urls_and_constants_wiring() -> None:
    assert "github.com" in gui_urls.github_url
    assert gui_constants.colors is gui_colors
    assert gui_constants.urls is gui_urls
    assert gui_constants.props is gui_props
