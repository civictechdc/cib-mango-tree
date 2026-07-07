import os
import subprocess
import sys


def is_wsl() -> bool:
    """Check if the environment is WSL2."""
    try:
        with open("/proc/version", "r") as f:
            return "microsoft" in f.read().lower()
    except FileNotFoundError:
        return False


def open_directory_explorer(path: str):
    if os.name == "nt":
        # Windows platform
        subprocess.run(["explorer", os.path.normpath(path)])
    elif os.name == "posix":
        if sys.platform == "darwin":
            # macOS
            subprocess.run(["open", path])
        elif sys.platform == "linux":
            if is_wsl():
                # WSL2 environment
                windows_path = subprocess.run(
                    ["wslpath", "-w", path], capture_output=True, text=True
                ).stdout.strip()
                subprocess.run(["explorer.exe", windows_path])
            else:
                # Native Linux
                subprocess.run(["xdg-open", path])
        else:
            raise OSError(f"Unsupported POSIX platform: {sys.platform}")
    else:
        raise OSError(f"Unsupported operating system: {os.name}")


def _remove_motw():

    FILES = [
        "pythonnet/runtime/Python.Runtime.dll",
        "webview/lib/Microsoft.Web.WebView2.Core.dll",
        "webview/lib/Microsoft.Web.WebView2.WinForms.dll",
        "webview/lib/WebBrowserInterop.x64.dll",
        "webview/lib/WebBrowserInterop.x86.dll",
    ]

    for x in FILES:
        path = f"{os.path.dirname(sys.argv[0])}/_internal/{x}:Zone.Identifier"
        if os.path.exists(path):
            os.unlink(path)
