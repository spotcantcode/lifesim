#!/bin/sh
set -eu
cd "$(dirname "$0")"
if [ ! -x .venv/bin/python ] || [ ! -d frontend/node_modules ]; then
  echo 'Install the dependencies listed in README.md first.'
  exit 1
fi
export LIFESIM_API_PORT="${LIFESIM_API_PORT:-8000}"
export LIFESIM_WEB_PORT="${LIFESIM_WEB_PORT:-5173}"
.venv/bin/python -m uvicorn backend.app.main:app --host 127.0.0.1 --port "$LIFESIM_API_PORT" --no-access-log &
backend_process=$!
cleanup() {
  kill "$backend_process" 2>/dev/null || true
  if [ -n "${frontend_process:-}" ]; then kill "$frontend_process" 2>/dev/null || true; fi
}
trap cleanup EXIT INT TERM
.venv/bin/python - <<'PY'
import os
import time
import urllib.request
port = int(os.environ['LIFESIM_API_PORT'])
for attempt in range(30):
  try:
    with urllib.request.urlopen(f'http://127.0.0.1:{port}/api/health', timeout=1) as response:
      if response.status == 200:
        break
  except OSError:
    time.sleep(.2)
else:
  raise SystemExit('LifeSim backend did not start. Check the port and terminal errors.')
PY
if ! kill -0 "$backend_process" 2>/dev/null; then
  echo 'LifeSim backend stopped. Choose an available LIFESIM_API_PORT.'
  exit 1
fi
npm --prefix frontend run dev -- --port "$LIFESIM_WEB_PORT" &
frontend_process=$!
wait "$frontend_process"
