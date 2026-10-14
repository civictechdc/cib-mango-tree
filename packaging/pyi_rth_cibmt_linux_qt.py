"""PyInstaller runtime hook: force software Qt/WebEngine rendering on Linux.

Why this exists
---------------
The GUI is NiceGUI in a native window via pywebview + PyQt6 WebEngine. On Linux,
Qt/Chromium often require working host GPU/EGL/GLX. Many machines (and VMs) do
not provide that, which leads to silent startup failure or "Could not initialize
GLX" / EGL errors even when the onedir bundle is otherwise complete.

This hook sets environment defaults so the frozen app prefers software rendering
instead of depending on the host GPU stack. Defaults use setdefault / append so
a user or wrapper can still override them.

Do not set ``QSG_RHI_BACKEND=software`` — that value is invalid in Qt6 and causes
a fallback to the default OpenGL/GLX path (which then fails with
"Could not initialize GLX").

Where it is used
----------------
Listed in ``pyinstaller.spec`` as a Linux-only entry in ``Analysis(runtime_hooks=...)``.
PyInstaller runs it automatically when the frozen ``CIBMangoTree`` binary starts,
before application code (and before Qt) loads. It is not imported by the app at
dev time; it only ships inside the Linux onedir build.
"""

import os
import sys


def _append_chromium_flag(flag: str) -> None:
    existing = os.environ.get("QTWEBENGINE_CHROMIUM_FLAGS", "")
    parts = existing.split()
    if flag not in parts:
        parts.append(flag)
    os.environ["QTWEBENGINE_CHROMIUM_FLAGS"] = " ".join(parts)


if sys.platform.startswith("linux"):
    os.environ.setdefault("QT_QPA_PLATFORM", "xcb")
    os.environ.setdefault("QT_QUICK_BACKEND", "software")
    # Avoid GLX for the xcb platform window when no usable GL is present.
    os.environ.setdefault("QT_XCB_GL_INTEGRATION", "none")
    _append_chromium_flag("--disable-gpu")
