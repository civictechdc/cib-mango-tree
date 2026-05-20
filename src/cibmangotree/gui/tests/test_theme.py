"""Behavior tests for gui.theme brand constants."""

from gui.theme import (
    ACCENT,
    MANGO_DARK_GREEN,
    MANGO_ORANGE,
    gui_colors,
    gui_constants,
    gui_urls,
)


def test_gui_colors_defaults_match_brand_constants() -> None:
    assert gui_colors.primary == MANGO_DARK_GREEN
    assert gui_colors.mango_orange == MANGO_ORANGE
    assert gui_colors.accent == ACCENT


def test_gui_urls_and_constants_wiring() -> None:
    assert "github.com" in gui_urls.github_url
    assert gui_constants.colors is gui_colors
    assert gui_constants.urls is gui_urls
