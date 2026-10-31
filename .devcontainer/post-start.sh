#!/usr/bin/env bash
# Start the app in the background; Codespaces opens forwarded port 8000.
set -uo pipefail

LOG_FILE="/tmp/cibmt.log"
PID_FILE="/tmp/cibmt.pid"

if [[ -f "${PID_FILE}" ]] && kill -0 "$(cat "${PID_FILE}")" 2>/dev/null; then
  echo "CIB Mango Tree is already running (pid $(cat "${PID_FILE}"))."
  exit 0
fi

cd "$(dirname "$0")/.."
nohup uv run cibmt >>"${LOG_FILE}" 2>&1 &
echo $! >"${PID_FILE}"
echo "CIB Mango Tree started (pid $(cat "${PID_FILE}")). Open port 8000 in the browser."
