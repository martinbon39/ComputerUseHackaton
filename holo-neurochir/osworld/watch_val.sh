#!/usr/bin/env bash
# Progress reports of a run_patched_eval.sh run: every <every> new tasks paired between patched (else prompt) and orig,
# and at the end, the confirm block of compare_val over all arms present is sent
# to <agent> with argos send. Ends when every window of tmux osw_val_<tag> printed its EXIT line and no launcher of
# that tag is still waiting (WAIT=1), or after 8 h.
# ORIG_TAG=<tag>: take the orig arm from ~/osw/results_val_orig_<tag> (an arm paired with another tag's orig run).
# Usage: [SUBSETS=confirm|all] [ORIG_TAG=<tag>] bash osworld/watch_val.sh <tag> <origin stuck|other> [agent=ares] [every=10]
set -uo pipefail
TAG="$1"; ORIGIN="$2"; AGENT="${3:-ares}"; EVERY="${4:-10}"
HERE="$(cd "$(dirname "$0")" && pwd)"; cd "$HERE/.."
count() { find "$1" -name result.txt 2>/dev/null | sed 's|.*/\([^/]*/[^/]*\)/result.txt|\1|' | sort; }
dir() { if [ "$1" = orig ]; then echo ~/osw/results_val_orig_${ORIG_TAG:-$TAG}; else echo ~/osw/results_val_$1_$TAG; fi; }
present() { for a in patched prompt orig; do [ -d "$(dir $a)" ] && echo "$a"; done; }
report() {
  local why="$1" args=() scored="" out
  for a in $(present); do args+=("$a=$(dir $a)"); scored+="$a $(count "$(dir $a)" | wc -l), "; done
  [ ${#args[@]} -ge 2 ] || return 0
  out=$(PYTHONPATH=. ~/osw/venv/bin/python osworld/compare_val.py --origin "$ORIGIN" --subsets "${SUBSETS:-confirm}" \
        --out ~/osw/val_${TAG}_compare.json "${args[@]}" 2>&1 | grep -v '^scored:')
  argos send "$AGENT" "online-eval [$TAG] $why — scored: ${scored%, }
$out"
}
last=0; start=$(date +%s)
while :; do
  arms=($(present))
  n=0
  ref=${arms[-1]:-}; [ ${#arms[@]} -ge 2 ] && n=$(comm -12 <(count "$(dir ${arms[0]})") <(count "$(dir $ref)") | wc -l)
  wins=$(tmux list-windows -t "osw_val_$TAG" -F '#W' 2>/dev/null); finished=1
  for w in $wins; do
    tmux capture-pane -pt "osw_val_$TAG:$w" -S -20 | grep -q "$(echo "$w" | tr a-z A-Z)_EXIT" || finished=0
  done
  pgrep -f "run_patched_eval.sh $TAG " >/dev/null && finished=0  # an arm still waiting for its preflight
  if [ -n "$wins" ] && [ $finished = 1 ]; then report "FINISHED"; exit 0; fi
  if [ "$n" -ge $((last + EVERY)) ]; then report "progress ($n pairs ${arms[0]}/$ref)"; last=$n; fi
  if [ $(( $(date +%s) - start )) -gt 28800 ]; then report "watch stopped after 8 h (run not finished)"; exit 1; fi
  sleep 120
done
