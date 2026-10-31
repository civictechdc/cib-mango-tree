#!/usr/bin/env bash
set -euo pipefail

uv sync

# noVNC opens as the port root (index.html). Enable autoconnect so Codespaces
# "openBrowser" on 6080 does not require a Connect click or password.
shopt -s nullglob
for f in /usr/local/novnc/noVNC-*/index.html /usr/local/novnc/noVNC-*/vnc.html; do
  sed -i \
    -e "s/initSetting('autoconnect', false)/initSetting('autoconnect', true)/" \
    -e "s/initSetting('resize', 'off')/initSetting('resize', 'remote')/" \
    "$f"
done
