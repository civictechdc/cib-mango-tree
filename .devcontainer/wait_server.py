#!/usr/bin/env python3
"""Temporary page on port 8000 until the real app replaces it."""

from http.server import BaseHTTPRequestHandler, HTTPServer

HTML = """<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="utf-8"/>
  <meta http-equiv="refresh" content="3"/>
  <meta name="viewport" content="width=device-width, initial-scale=1"/>
  <title>Starting CIB Mango Tree</title>
  <style>
    body {
      font-family: system-ui, sans-serif;
      display: flex;
      min-height: 100vh;
      align-items: center;
      justify-content: center;
      margin: 0;
      background: #f7f4ef;
      color: #1a1a1a;
    }
    main { max-width: 28rem; padding: 2rem; text-align: center; }
    h1 { font-size: 1.5rem; margin: 0 0 0.75rem; }
    p { margin: 0; line-height: 1.5; opacity: 0.85; }
  </style>
</head>
<body>
  <main>
    <h1>CIB Mango Tree is starting…</h1>
    <p>First-time setup can take several minutes. This page refreshes automatically — hang tight.</p>
  </main>
</body>
</html>
"""


class Handler(BaseHTTPRequestHandler):
    def do_GET(self) -> None:
        body = HTML.encode("utf-8")
        self.send_response(200)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, format: str, *args) -> None:
        return


if __name__ == "__main__":
    HTTPServer(("0.0.0.0", 8000), Handler).serve_forever()
