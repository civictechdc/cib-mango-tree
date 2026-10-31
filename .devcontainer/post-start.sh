#!/usr/bin/env bash
# Show a starting page ASAP, then replace it with the real app when ready.
set -uo pipefail

LOG_FILE="/tmp/cibmt.log"
PID_FILE="/tmp/cibmt.pid"
WAIT_PID_FILE="/tmp/cibmt-wait.pid"
PORT=8000
ROOT="$(cd "$(dirname "$0")/.." && pwd)"

port_open() {
  (echo >/dev/tcp/127.0.0.1/"${PORT}") >/dev/null 2>&1
}

app_ready() {
  # Real app responds with NiceGUI/HTML that is not only our wait page title.
  local body
  body="$(curl -fsS --max-time 2 "http://127.0.0.1:${PORT}/" 2>/dev/null || true)"
  [[ -n "${body}" ]] && [[ "${body}" != *"CIB Mango Tree is starting"* ]]
}

stop_wait_server() {
  if [[ -f "${WAIT_PID_FILE}" ]]; then
    local wait_pid
    wait_pid="$(cat "${WAIT_PID_FILE}" 2>/dev/null || true)"
    if [[ -n "${wait_pid}" ]] && kill -0 "${wait_pid}" 2>/dev/null; then
      echo "Stopping temporary starting page (pid ${wait_pid})…"
      kill "${wait_pid}" 2>/dev/null || true
      wait "${wait_pid}" 2>/dev/null || true
    fi
    rm -f "${WAIT_PID_FILE}"
  fi
  # Ensure port is free before launching the real app.
  if port_open && ! app_ready; then
    fuser -k "${PORT}/tcp" 2>/dev/null || true
    sleep 1
  fi
}

if app_ready; then
  echo "CIB Mango Tree is already running on port ${PORT}."
  exit 0
fi

echo "CIB Mango Tree Codespaces: preparing the app…"

if ! port_open; then
  echo "Opening temporary starting page on port ${PORT}…"
  setsid python3 "${ROOT}/.devcontainer/wait_server.py" >>/tmp/cibmt-wait.log 2>&1 </dev/null &
  echo $! >"${WAIT_PID_FILE}"
fi

if [[ ! -f "${PID_FILE}" ]] || ! kill -0 "$(cat "${PID_FILE}" 2>/dev/null)" 2>/dev/null; then
  echo "Waiting for Python environment…"
  for i in $(seq 1 180); do
    if [[ -x "${ROOT}/.venv/bin/python" ]]; then
      echo "Python environment ready."
      break
    fi
    if (( i % 10 == 0 )); then
      echo "Still waiting for environment… (${i}s)"
    fi
    sleep 1
  done

  if [[ ! -x "${ROOT}/.venv/bin/python" ]]; then
    echo "Timed out waiting for .venv after postCreate." >&2
    exit 1
  fi

  stop_wait_server

  cd "${ROOT}"
  : >"${LOG_FILE}"
  export PYTHONUNBUFFERED=1
  echo "Starting CIB Mango Tree (this can take a minute)…"
  setsid uv run cibmt >>"${LOG_FILE}" 2>&1 </dev/null &
  echo $! >"${PID_FILE}"
  echo "App process started (pid $(cat "${PID_FILE}"))."
fi

echo "Waiting for the app to become ready on port ${PORT}…"
for i in $(seq 1 180); do
  if app_ready; then
    echo "CIB Mango Tree is ready — open port ${PORT} in the browser if it did not open automatically."
    exit 0
  fi
  if (( i % 10 == 0 )); then
    echo "Still starting… (${i}s). Browser may show the starting page until the app is ready."
  fi
  sleep 1
done

echo "Timed out waiting for the app. Log:" >&2
tail -n 80 "${LOG_FILE}" >&2 || true
exit 1
