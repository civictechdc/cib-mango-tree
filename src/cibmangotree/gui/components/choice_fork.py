from typing import Callable

from nicegui import ui

from cibmangotree.gui.theme import (
    COLOR_PRIMARY,
    ROW_GAP_4,
    SPACING_MB_6,
    STYLE_PROMPT,
)


def two_button_choice_fork_content(
    prompt: str,
    left_button_label: str,
    left_button_on_click: Callable[[], None],
    left_button_icon: str,
    right_button_label: str,
    right_button_on_click: Callable[[], None],
    right_button_icon: str,
) -> None:
    # Prompt label
    ui.label(prompt).classes(SPACING_MB_6).style(STYLE_PROMPT)

    # Action buttons row
    with ui.row().classes(ROW_GAP_4):
        ui.button(
            left_button_label,
            on_click=left_button_on_click,
            icon=left_button_icon,
            color=COLOR_PRIMARY,
        )

        ui.button(
            right_button_label,
            on_click=right_button_on_click,
            icon=right_button_icon,
            color=COLOR_PRIMARY,
        )
