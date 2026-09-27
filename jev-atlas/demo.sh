#!/usr/bin/env sh
# Run the Jev Atlas demo (demo.py) with the harness's Python, in the visible demo Chrome.
#   jev-atlas/demo.sh all [--yes]      see demo.py for the rest
set -eu
HERE=$(cd "$(dirname "$0")" && pwd)
CHROME_PROFILE=""; BU_CDP_URL=""
# shellcheck disable=SC1091
. "$HERE/adit.env"
PY="$JEV_CLONE/.venv/bin/python"
[ -x "$PY" ] || { echo "No harness at $JEV_CLONE; run: jev-atlas/harness/bootstrap.sh $JEV_CLONE" >&2; exit 2; }
curl -fs "$BU_CDP_URL/json/version" >/dev/null 2>&1 || "$HERE/chrome.sh" show
exec "$PY" "$HERE/demo.py" "$@"
