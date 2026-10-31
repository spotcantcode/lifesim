#!/bin/bash
set -u
cd "$(dirname "$0")" || exit 1

# Finder launches Terminal with a smaller PATH than an interactive shell.
export PATH="/opt/homebrew/bin:/usr/local/bin:$PATH"
export LIFESIM_API_PORT="${LIFESIM_API_PORT:-8000}"
export LIFESIM_WEB_PORT="${LIFESIM_WEB_PORT:-5173}"

show_error() {
  printf '\n%s\n' "$1"
  read -r -p 'Press Return to close this launcher. ' _
  exit 1
}

command -v npm >/dev/null 2>&1 || show_error 'Node.js is missing. Install the version listed in README.md first.'
[ -x .venv/bin/python ] && [ -d frontend/node_modules ] || show_error 'Install the dependencies listed in README.md first.'

printf 'Starting LifeSim…\nKeep this window open while using the app. Press Control+C to stop.\n\n'
./start.sh &
app_process=$!
cleanup() {
  kill "$app_process" 2>/dev/null || true
  wait "$app_process" 2>/dev/null || true
}
trap cleanup EXIT
trap 'exit 130' INT
trap 'exit 143' TERM HUP

if ! .venv/bin/python - "$app_process" <<'PY'
import os
import sys
import time
import urllib.request

urls = [
    f"http://127.0.0.1:{os.environ['LIFESIM_API_PORT']}/api/health",
    f"http://127.0.0.1:{os.environ['LIFESIM_WEB_PORT']}/",
]
for attempt in range(100):
    try:
        os.kill(int(sys.argv[1]), 0)
    except ProcessLookupError:
        raise SystemExit(1)
    try:
        for url in urls:
            with urllib.request.urlopen(url, timeout=1) as response:
                if response.status != 200:
                    raise OSError('Server is not ready yet.')
        break
    except OSError:
        time.sleep(.2)
else:
    raise SystemExit(1)
PY
then
  show_error 'LifeSim could not start. Check the errors above; another copy may already be running.'
fi

if ! open "http://127.0.0.1:$LIFESIM_WEB_PORT"; then
  printf '\nOpen http://127.0.0.1:%s in your browser.\n' "$LIFESIM_WEB_PORT"
fi
wait "$app_process"
result=$?
if [ "$result" -ne 0 ]; then
  show_error 'LifeSim stopped with an error. See the details above.'
fi
