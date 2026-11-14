"""Behavior tests for gui.theme brand constants."""

from cibmangotree.gui.theme import (
    ACCENT,
    CANCEL,
    COLOR_GREY,
    COLOR_PRIMARY,
    COLOR_RED,
    MANGO_DARK_GREEN,
    MANGO_ORANGE,
    MANGO_ORANGE_LIGHT,
    gui_colors,
    gui_constants,
    gui_props,
    gui_urls,
)


def test_gui_colors_defaults_match_brand_constants() -> None:
    assert gui_colors.primary == MANGO_DARK_GREEN
    assert gui_colors.secondary == MANGO_ORANGE_LIGHT
    assert gui_colors.cancel == CANCEL
    assert gui_colors.mango_orange == MANGO_ORANGE
    assert gui_colors.accent == ACCENT


def test_gui_props_defaults() -> None:
    assert gui_props.flat == "flat"
    assert gui_props.outline == "outline"
    assert gui_props.color_primary == f"color={COLOR_PRIMARY}"
    assert gui_props.color_grey == f"color={COLOR_GREY}"
    assert gui_props.color_red == f"color={COLOR_RED}"


def test_gui_urls_and_constants_wiring() -> None:
    assert "github.com" in gui_urls.github_url
    assert gui_constants.colors is gui_colors
    assert gui_constants.urls is gui_urls
    assert gui_constants.props is gui_props
