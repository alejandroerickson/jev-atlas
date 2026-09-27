#!/usr/bin/env sh
# Start the Chrome that ADIT runs drive: its own DevTools port and profile, so a
# personal Chrome profile is never touched. Headless by default; `chrome.sh show`
# opens a visible window for someone to watch.
#
#   jev-atlas/chrome.sh            # headless, for counted runs
#   jev-atlas/chrome.sh show       # a visible window
#   jev-atlas/chrome.sh stop       # stop it
set -eu
HERE=$(cd "$(dirname "$0")" && pwd)
CHROME_PROFILE=""; BU_CDP_URL=""
# shellcheck disable=SC1091
. "$HERE/adit.env"
PORT=$(printf '%s\n' "$BU_CDP_URL" | sed 's#.*:\([0-9][0-9]*\).*#\1#')
MAC_CHROME="/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
BIN="${CHROME_BIN:-$(command -v google-chrome || command -v chromium || command -v chromium-browser || true)}"
[ -n "$BIN" ] || { [ -x "$MAC_CHROME" ] && BIN="$MAC_CHROME"; } || true

case "${1:-headless}" in
  stop)
    pkill -f "remote-debugging-port=$PORT" && echo "stopped" || echo "not running"; exit 0 ;;
  show) HEADLESS="" ;;
  headless) HEADLESS="--headless=new" ;;
  *) echo "usage: jev-atlas/chrome.sh [headless|show|stop]" >&2; exit 2 ;;
esac

if curl -fs "http://127.0.0.1:$PORT/json/version" >/dev/null 2>&1; then
  echo "A browser already listens on $PORT."; exit 0
fi
[ -n "$BIN" ] || { echo "No Chrome or Chromium found; set CHROME_BIN." >&2; exit 2; }
mkdir -p "$CHROME_PROFILE"
nohup "$BIN" ${HEADLESS:+"$HEADLESS"} --remote-debugging-port="$PORT" --user-data-dir="$CHROME_PROFILE" \
  --no-first-run --no-default-browser-check --disable-gpu --window-size=1280,900 about:blank \
  >/dev/null 2>&1 &
for _ in 1 2 3 4 5 6 7 8 9 10; do
  curl -fs "http://127.0.0.1:$PORT/json/version" >/dev/null 2>&1 && { echo "Chrome on $PORT (profile $CHROME_PROFILE)"; exit 0; }
  sleep 0.5
done
echo "Chrome did not come up on $PORT" >&2; exit 1
