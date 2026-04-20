"""
Base abstractions for GUI pages using Pydantic and ABC.

This module provides:
- GuiPage: Abstract base class for all GUI pages
- format_file_size: Utility for human-readable file sizes
- present_separator: Utility for displaying separator characters
"""

import abc
from pathlib import Path
from typing import Callable

from nicegui import ui
from pydantic import BaseModel, ConfigDict

from gui.session import GuiSession
from gui.theme import gui_colors, gui_urls


class GuiPage(BaseModel, abc.ABC):
    """
    Abstract base class for all GUI pages.

    Provides common page structure and lifecycle using the Template Method
    pattern. Subclasses implement `render_content()` for page-specific UI
    while inheriting consistent header/footer rendering.

    Attributes:
        session: Session state container with app context
        route: URL route for this page (e.g., "/", "/projects")
        title: Page title shown in header
        show_back_button: Whether to show back navigation button
        back_route: Route to navigate when back button clicked
        back_icon: Icon for back button (default: "arrow_back")
        back_text: Optional text label for back button
        on_page_exit: Optional callback invoked before navigation (back/home buttons)
        show_footer: Whether to render footer

    Usage:
        ```python
        class MyPage(GuiPage):
            def __init__(self, session: GuiSession):
                super().__init__(
                    session=session,
                    route="/my_page",
                    title="My Page",
                    show_back_button=True,
                    back_route="/",
                )

            def render_content(self) -> None:
                with ui.column().classes("items-center"):
                    ui.label("My page content")

        # Register with NiceGUI
        @ui.page("/my_page")
        def my_page():
            page = MyPage(session)
            page.render()
        ```
    """

    # Link to main session state/variables
    session: GuiSession

    # Page configuration
    route: str = "/"
    title: str = "CIB Mango Tree"

    # Navigation configuration
    show_back_button: bool = False
    back_route: str | None = None
    back_icon: str = "arrow_back"
    back_text: str | None = None
    on_page_exit: Callable[[], None] | None = None

    # Footer configuration
    show_footer: bool = True

    # Allow arbitrary types
    model_config = ConfigDict(arbitrary_types_allowed=True)

    # main rendering function
    def render(self) -> None:
        """
        Main rendering method implementing template pattern.

        Call this method from the NiceGUI @ui.page decorator to render
        the complete page with header, content, and footer.

        Lifecycle:
        1. Setup colors
        2. Render header
        3. Render content (abstract - implemented by subclasses)
        4. Render footer
        """
        self._setup_colors()
        self._render_header()
        self.render_content()
        if self.show_footer:
            self._render_footer()

    @abc.abstractmethod
    def render_content(self) -> None:
        """
        Render page-specific content.

        Subclasses MUST implement this method to provide the main
        page content. This is called automatically by render().

        Example:
            ```python
            def render_content(self) -> None:
                with ui.column().classes("items-center"):
                    ui.label("Welcome")
                    ui.button("Click me", on_click=self._handle_click)
            ```
        """
        raise NotImplementedError

    def _setup_colors(self) -> None:
        """Setup Mango Tree brand colors for NiceGUI."""
        ui.colors(
            primary=gui_colors.primary,
            secondary=gui_colors.secondary,
            accent=gui_colors.accent,
        )

    def _render_header(self) -> None:
        """
        Render standardized header with 3-column layout.

        Layout:
        - Left: Back button (if show_back_button=True)
        - Center: Page title
        - Right: Home button (if not on home page)
        """
        with ui.header(elevated=True):
            with ui.row().classes("w-full items-center justify-between"):
                # Left: Back button or spacer
                with ui.element("div").classes("flex items-center"):
                    if self.show_back_button and self.back_route:
                        # Build button parameters conditionally
                        btn_kwargs = {
                            "icon": self.back_icon,
                            "color": "accent",
                            "on_click": self._handle_back_click,
                        }
                        if self.back_text:
                            btn_kwargs["text"] = self.back_text
                        ui.button(**btn_kwargs).props("flat")

                # Center: Title
                ui.label(self.title).classes("text-h6")

                # Right: Home button (if not on home page)
                with ui.element("div").classes("flex items-center"):
                    if self.show_back_button:  # Not on home if back button shown
                        ui.button(
                            icon="home",
                            color="accent",
                            on_click=self._handle_home_click,
                        ).props("flat")

    def _handle_back_click(self) -> None:
        """Handle back button click with optional page exit callback."""
        if self.on_page_exit:
            self.on_page_exit()

        if self.back_route:
            self.navigate_to(self.back_route)

    def _handle_home_click(self) -> None:
        """Handle home button click with optional page exit callback."""
        if self.on_page_exit:
            self.on_page_exit()
        self.navigate_to("/")

    def _render_footer(self) -> None:
        """
        Render standardized footer with 3-column layout.

        Layout:
        - Left: License information
        - Center: Project attribution
        - Right: External links (GitHub, Instagram)
        """
        with ui.footer(elevated=True):
            with (
                ui.row()
                .classes("w-full items-center")
                .style("justify-content: space-between")
            ):
                # Left: License
                with ui.element("div").classes("flex items-center"):
                    ui.label("MIT License").classes("text-sm text-bold")

                # Center: Project attribution
                ui.label("A Civic Tech DC Project").classes("text-sm text-bold")

                # Right: External links
                self._render_footer_links()

    def _render_footer_links(self) -> None:
        """Render social media links in footer."""
        with ui.element("div").classes("flex items-center gap-3"):
            # GitHub button
            with ui.link(target=gui_urls.github_url, new_tab=True).classes(
                "inline-flex items-center justify-center text-white no-underline size-5"
            ):
                ui.html(self._load_svg_icon("github"), sanitize=False).classes(
                    "size-full fill-current"
                )
                ui.tooltip("Visit our GitHub")

            with ui.link(target=gui_urls.instagram_url, new_tab=True).classes(
                "inline-flex items-center justify-center text-white no-underline size-5"
            ):
                ui.html(self._load_svg_icon("instagram"), sanitize=False).classes(
                    "size-full fill-current"
                )
                ui.tooltip("Follow us on Instagram")

    # Navigation helpers
    def navigate_to(self, route: str) -> None:
        """
        Navigate to another page in the application.

        Args:
            route: Target route path (e.g., "/projects", "/new_project")
        """
        ui.navigate.to(route)

    def navigate_to_external(self, url: str) -> None:
        """
        Navigate to external URL in new tab.

        Args:
            url: External URL to open
        """
        ui.navigate.to(url, new_tab=True)

    def go_back(self) -> None:
        """Navigate to the configured back route."""
        if self.back_route:
            self.navigate_to(self.back_route)

    def go_home(self) -> None:
        """Navigate to home page."""
        self.navigate_to("/")

    # utilities
    def _load_svg_icon(self, icon_name: str) -> str:
        """
        Load SVG icon from the icons directory.

        Args:
            icon_name: Name of icon file (without .svg extension)

        Returns:
            SVG content as string
        """
        icon_path = Path(__file__).parent / "icons" / f"{icon_name}.svg"
        return icon_path.read_text()

    def notify_success(self, message: str) -> None:
        """Show success notification."""
        ui.notify(message, type="positive", color="secondary")

    def notify_warning(self, message: str) -> None:
        """Show warning notification."""
        ui.notify(message, type="warning")

    def notify_error(self, message: str) -> None:
        """Show error notification."""
        ui.notify(message, type="negative")


# standalone uitility functions
def format_file_size(size_bytes: int) -> str:
    """
    Format file size in human-readable format.

    Args:
        size_bytes: File size in bytes

    Returns:
        Formatted string (e.g., "1.5 MB", "3.2 GB")

    Example:
        >>> format_file_size(1536)
        '1.5 KB'
        >>> format_file_size(1048576)
        '1.0 MB'
    """
    output_size: float = float(size_bytes)

    for unit in ["B", "KB", "MB", "GB", "TB"]:
        if output_size < 1024:
            return f"{output_size:.1f} {unit}"

        output_size /= 1024

    return f"{output_size:.1f} PB"


def present_separator(value: str) -> str:
    """
    Format separator/quote character for display.

    Args:
        value: Separator character

    Returns:
        Human-readable representation

    Example:
        >>> present_separator("\\t")
        'Tab'
        >>> present_separator(",")
        ', (Comma)'
    """
    mapping = {
        "\t": "Tab",
        " ": "Space",
        ",": ", (Comma)",
        ";": "; (Semicolon)",
        "'": "' (Single quote)",
        '"': '" (Double quote)',
        "|": "| (Pipe)",
    }
    return mapping.get(value, value)
