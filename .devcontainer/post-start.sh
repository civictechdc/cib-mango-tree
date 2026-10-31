#!/usr/bin/env bash
# Start the native GUI once the Codespaces desktop display is ready.
set -uo pipefail

export DISPLAY="${DISPLAY:-:1}"
LOG_FILE="/tmp/cibmt.log"
PID_FILE="/tmp/cibmt.pid"

if [[ -f "${PID_FILE}" ]] && kill -0 "$(cat "${PID_FILE}")" 2>/dev/null; then
  echo "CIB Mango Tree is already running (pid $(cat "${PID_FILE}"))."
  exit 0
fi

echo "Waiting for desktop display ${DISPLAY}..."
for _ in $(seq 1 60); do
  if xdpyinfo -display "${DISPLAY}" >/dev/null 2>&1; then
    break
  fi
  sleep 1
done

if ! xdpyinfo -display "${DISPLAY}" >/dev/null 2>&1; then
  echo "Desktop display ${DISPLAY} did not become ready; open port 6080 and retry." >&2
  exit 1
fi

cd "$(dirname "$0")/.."
nohup uv run cibmt >>"${LOG_FILE}" 2>&1 &
echo $! >"${PID_FILE}"
echo "CIB Mango Tree started (pid $(cat "${PID_FILE}")). Log: ${LOG_FILE}"
