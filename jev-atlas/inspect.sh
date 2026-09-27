#!/usr/bin/env sh
# Start the jev-ultrafast inspector (what people watch) for ADIT: without the
# atlas, with it, or both side by side. Self-contained: needs only jev-atlas/ and the harness.
#
#   jev-atlas/inspect.sh                # both if the atlas exists, else only "without"
#   jev-atlas/inspect.sh without        # the baseline only (port PORT_WITHOUT)
#   jev-atlas/inspect.sh with           # the atlas only (port PORT_WITH); refuses without an atlas
#   DRY_RUN=1 jev-atlas/inspect.sh      # print, start nothing
#
# Start the browser first: jev-atlas/chrome.sh show (visible) or jev-atlas/chrome.sh.
# Ctrl-C stops every inspector this script started.
set -eu
HERE=$(cd "$(dirname "$0")" && pwd)
REPO=$(cd "$HERE/.." && pwd)
abspath() { case "$1" in /*) printf '%s\n' "$1" ;; *) printf '%s\n' "$REPO/$1" ;; esac; }

WHICH="${1:-both}"
case "$WHICH" in with|without|both) ;; *) echo "usage: jev-atlas/inspect.sh [with|without|both]" >&2; exit 2 ;; esac

CLONE_ENV="${JEV_CLONE:-}"
APP_NAME=""; START_URL=""; ATLAS=""; RUN_DIR=""; DEFAULT_GOAL=""; PORT_WITHOUT=""; PORT_WITH=""
# shellcheck disable=SC1091
. "$HERE/adit.env"
CLONE="${CLONE_ENV:-$JEV_CLONE}"
RUNS=$(abspath "${ADIT_RUN_DIR:-$RUN_DIR}")
ATLAS=$(abspath "$ATLAS")
LOG_DIR="$RUNS/logs"

if [ ! -f "$ATLAS" ]; then
  case "$WHICH" in
    with) echo "No atlas at $ATLAS yet. The 'with' inspector needs it; build it (jev-atlas/docs/BUILDING-A-SHIM.md), or run: jev-atlas/inspect.sh without" >&2; exit 2 ;;
    both) echo "note: no atlas at $ATLAS yet, so only the 'without' inspector starts." >&2; WHICH=without ;;
  esac
fi

if [ -z "${DRY_RUN:-}" ]; then
  [ -f "$CLONE/pyproject.toml" ] || { echo "No harness at $CLONE" >&2; exit 2; }
  curl -fs "$BU_CDP_URL/json/version" >/dev/null 2>&1 || { echo "No browser at $BU_CDP_URL; run jev-atlas/chrome.sh show" >&2; exit 2; }
fi

PIDS=""
start_one() {
  cond="$1"; port="$2"; run_dir="$RUNS/$cond"; log="$LOG_DIR/inspector-$cond.log"
  if [ -n "${DRY_RUN:-}" ]; then
    echo "cd $CLONE && BU_CDP_URL=$BU_CDP_URL BU_NAME=$BU_NAME-$cond TYPESAFE_DEMO_PORT=$port JEV_DEMO_URL='$START_URL' JEV_RUN_DIR='$run_dir' JEV_SHOW_TAB=1 $( [ "$cond" = with ] && echo "JEV_ATLAS='$ATLAS' ")uv run --env-file .env jev"
    return 0
  fi
  mkdir -p "$run_dir" "$LOG_DIR"
  (
    cd "$CLONE" || exit 1
    # One browser daemon per inspector, so the two never share (or restart) a CDP session.
    BU_NAME="$BU_NAME-$cond"; export BU_CDP_URL BU_NAME
    [ -n "${JEV_VIEWPORT:-}" ] && export JEV_VIEWPORT
    if [ "$cond" = with ]; then export JEV_ATLAS="$ATLAS"; else unset JEV_ATLAS; fi
    # Every Start demo resets ADIT's demonstration data first, so each run starts from the
    # same state (signed in as Marguerite). ADIT_RESET_ON_START=0 keeps the data as it is.
    if [ "${ADIT_RESET_ON_START:-1}" != 0 ]; then
      JEV_BEFORE_RUN="'$CLONE/.venv/bin/python' '$HERE/goals/check.py' reset"; export JEV_BEFORE_RUN
    else unset JEV_BEFORE_RUN; fi
    TYPESAFE_DEMO_PORT="$port" JEV_DEMO_URL="$START_URL" JEV_RUN_DIR="$run_dir" \
    JEV_SHOW_TAB="${JEV_SHOW_TAB:-1}" exec uv run --env-file .env jev
  ) >>"$log" 2>&1 &
  PIDS="$PIDS $!"
  echo "  $cond   http://127.0.0.1:$port   log: $log"
}
stop_all() { trap - INT TERM; [ -n "$PIDS" ] && kill $PIDS 2>/dev/null || true; exit 0; }

echo "$APP_NAME — inspector (harness $CLONE, browser $BU_CDP_URL)"
trap stop_all INT TERM
case "$WHICH" in
  both)    start_one without "$PORT_WITHOUT"; start_one with "$PORT_WITH" ;;
  with)    start_one with "$PORT_WITH" ;;
  without) start_one without "$PORT_WITHOUT" ;;
esac
[ -n "${DRY_RUN:-}" ] && exit 0
echo ""
echo "Type the goal, Start demo, then Run automatically. Start demo resets the demo data"
echo "first (ADIT_RESET_ON_START=0 to keep it). A run repeating itself is stopped (LOOP)."
[ -n "$DEFAULT_GOAL" ] && echo "Goal to paste: $DEFAULT_GOAL"
echo "Ctrl-C stops the inspector(s)."
wait
