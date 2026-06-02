import os
import sys


def remove_motw():
    files = [
        "pythonnet/runtime/Python.Runtime.dll",
        "webview/lib/Microsoft.Web.WebView2.Core.dll",
        "webview/lib/Microsoft.Web.WebView2.WinForms.dll",
        "webview/lib/WebBrowserInterop.x64.dll",
        "webview/lib/WebBrowserInterop.x86.dll",
    ]
    for x in files:
        path = f"{os.path.dirname(sys.argv[0])}/_internal/{x}:Zone.Identifier"
        if os.path.exists(path):
            os.unlink(path)
