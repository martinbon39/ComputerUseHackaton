#!/usr/bin/env bash
# Progress reports of a run_patched_eval.sh run: every <every> new paired tasks (and at the end), compare_val on the
# confirm subset is sent to <agent> with argos send. Ends when both arms printed their EXIT line, or after 6 h.
# Usage: bash osworld/watch_val.sh <tag> <origin stuck|other> [agent=ares] [every=10]
set -uo pipefail
TAG="$1"; ORIGIN="$2"; AGENT="${3:-ares}"; EVERY="${4:-10}"
HERE="$(cd "$(dirname "$0")" && pwd)"; cd "$HERE/.."
RES_P=~/osw/results_val_patched_$TAG; RES_O=~/osw/results_val_orig_$TAG
count() { find "$1" -name result.txt 2>/dev/null | sed 's|.*/\([^/]*/[^/]*\)/result.txt|\1|' | sort; }
report() {
  local n="$1" why="$2" out
  out=$(PYTHONPATH=. ~/osw/venv/bin/python osworld/compare_val.py "$RES_P" "$RES_O" --origin "$ORIGIN" \
        --out ~/osw/val_${TAG}_compare.json 2>&1 | awk '/^\[confirm\]/{p=1} /^\[confirm:/{p=0} p')
  argos send "$AGENT" "online-eval [$TAG] $why: $n paired tasks; patched $(count "$RES_P" | wc -l), orig $(count "$RES_O" | wc -l) scored.
$out"
}
last=0; start=$(date +%s)
while :; do
  n=$(comm -12 <(count "$RES_P") <(count "$RES_O") | wc -l)
  done_p=$(tmux capture-pane -pt "osw_val_$TAG:patched" -S -20 2>/dev/null | grep -c PATCHED_EXIT)
  done_o=$(tmux capture-pane -pt "osw_val_$TAG:orig" -S -20 2>/dev/null | grep -c ORIG_EXIT)
  if [ "$done_p" -gt 0 ] && [ "$done_o" -gt 0 ]; then report "$n" "FINISHED"; exit 0; fi
  if [ "$n" -ge $((last + EVERY)) ]; then report "$n" "progress"; last=$n; fi
  if [ $(( $(date +%s) - start )) -gt 21600 ]; then report "$n" "watch stopped after 6 h (run not finished)"; exit 1; fi
  sleep 120
done
