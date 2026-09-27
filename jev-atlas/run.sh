#!/usr/bin/env sh
# One unattended ADIT run of one condition: the harness driven from the command line.
# Self-contained: needs only jev-atlas/ and the harness.
#
#   jev-atlas/run.sh without                   # adit.env's DEFAULT_GOAL, no atlas
#   jev-atlas/run.sh with "some goal"          # with the atlas (once it exists)
#   ADIT_RUN_DIR=/elsewhere jev-atlas/run.sh without "goal"   # runs somewhere else
#   DRY_RUN=1 jev-atlas/run.sh without         # print, run nothing
#
# Needs the browser from jev-atlas/chrome.sh and the harness copy named by JEV_CLONE
# in adit.env (it holds TYPESAFE_API_KEY in its gitignored .env). BU_CDP_URL and
# BU_NAME are exported from adit.env, so they win over that .env's values.
set -eu
HERE=$(cd "$(dirname "$0")" && pwd)
REPO=$(cd "$HERE/.." && pwd)
abspath() { case "$1" in /*) printf '%s\n' "$1" ;; *) printf '%s\n' "$REPO/$1" ;; esac; }

[ $# -ge 1 ] || { echo "usage: jev-atlas/run.sh with|without [goal...]" >&2; exit 2; }
COND="$1"; shift
case "$COND" in with|without) ;; *) echo "condition must be with or without" >&2; exit 2 ;; esac

APP_NAME=""; START_URL=""; ATLAS=""; RUN_DIR=""; DEFAULT_GOAL=""
CLONE_ENV="${JEV_CLONE:-}"
# shellcheck disable=SC1091
. "$HERE/adit.env"
CLONE="${CLONE_ENV:-$JEV_CLONE}"

if [ $# -gt 0 ]; then GOAL="$*"; else GOAL="${GOAL:-$DEFAULT_GOAL}"; fi
[ -n "$GOAL" ] || { echo "No goal" >&2; exit 2; }

RUNS=$(abspath "${ADIT_RUN_DIR:-$RUN_DIR}")/"$COND"
if [ "$COND" = with ]; then
  ATLAS=$(abspath "$ATLAS")
  [ -f "$ATLAS" ] || [ -n "${DRY_RUN:-}" ] || { echo "No atlas at $ATLAS yet; only 'without' can run." >&2; exit 2; }
fi

if [ -n "${DRY_RUN:-}" ]; then
  echo "cd $CLONE && BU_CDP_URL=$BU_CDP_URL BU_NAME=$BU_NAME JEV_RUN_DIR='$RUNS' JEV_SHOW_TAB=${JEV_SHOW_TAB:-1} \\"
  [ "$COND" = with ] && echo "  JEV_ATLAS='$ATLAS' \\"
  echo "  uv run --env-file .env python examples/run.py --url '$START_URL' --goal '$GOAL'"
  exit 0
fi

[ -f "$CLONE/examples/run.py" ] || { echo "No harness at $CLONE" >&2; exit 2; }
curl -fs "$BU_CDP_URL/json/version" >/dev/null 2>&1 || { echo "No browser at $BU_CDP_URL; run jev-atlas/chrome.sh" >&2; exit 2; }

mkdir -p "$RUNS"
export BU_CDP_URL BU_NAME
export JEV_RUN_DIR="$RUNS"
export JEV_SHOW_TAB="${JEV_SHOW_TAB:-1}"
[ -n "${JEV_VIEWPORT:-}" ] && export JEV_VIEWPORT
if [ "$COND" = with ]; then export JEV_ATLAS="$ATLAS"; else unset JEV_ATLAS; fi

echo "${APP_NAME} — $COND"
echo "  runs:  $RUNS"
echo "  goal:  $GOAL"
cd "$CLONE"
exec uv run --env-file .env python examples/run.py --url "$START_URL" --goal "$GOAL"
