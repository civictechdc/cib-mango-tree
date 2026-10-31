#!/usr/bin/env bash
# Detach and start the web UI; wait until port 8000 accepts connections.
set -uo pipefail

LOG_FILE="/tmp/cibmt.log"
PID_FILE="/tmp/cibmt.pid"
PORT=8000
ROOT="$(cd "$(dirname "$0")/.." && pwd)"

port_open() {
  (echo >/dev/tcp/127.0.0.1/"${PORT}") >/dev/null 2>&1
}

if port_open; then
  echo "CIB Mango Tree already listening on port ${PORT}."
  exit 0
fi

if [[ ! -f "${PID_FILE}" ]] || ! kill -0 "$(cat "${PID_FILE}" 2>/dev/null)" 2>/dev/null; then
  for _ in $(seq 1 180); do
    if [[ -x "${ROOT}/.venv/bin/python" ]]; then
      break
    fi
    sleep 1
  done

  if [[ ! -x "${ROOT}/.venv/bin/python" ]]; then
    echo "Timed out waiting for .venv after postCreate." >&2
    exit 1
  fi

  cd "${ROOT}"
  : >"${LOG_FILE}"
  export PYTHONUNBUFFERED=1
  # setsid detaches from the Codespaces postStart session so the server is not reaped.
  setsid uv run cibmt >>"${LOG_FILE}" 2>&1 </dev/null &
  echo $! >"${PID_FILE}"
  echo "Started CIB Mango Tree (pid $(cat "${PID_FILE}"))."
fi

for _ in $(seq 1 180); do
  if port_open; then
    echo "CIB Mango Tree is ready on port ${PORT}."
    exit 0
  fi
  sleep 1
done

echo "Timed out waiting for port ${PORT}. Log:" >&2
tail -n 80 "${LOG_FILE}" >&2 || true
exit 1
