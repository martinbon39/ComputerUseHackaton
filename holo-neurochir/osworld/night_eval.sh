#!/usr/bin/env bash
# Night plan (ares, 2026-11-07): after the confirm arms of <confirm_tag> free their VMs, run the TEST split
# (split_test.json, never opened) with the best patched arm and the original arm, rescale the survivor when one ends,
# use spare capacity for the prompt arm on confirm, and send the reports. Every wait is bounded; stops at DEADLINE.
# RAM guard: if available RAM stays under GUARD_G (4) for 2 min, the last launched arm is restarted (RESUME) with one
# worker less. Launches and restarts are serialised by a lock.
# Env: BEST_URL BEST_NAME (patched server for test), MAX_VMS (5), MIN_AVAIL_G (5), DEADLINE (UTC HH:MM, 09:00),
#      CONFIRM_TAG (eager_m40), TEST_TAG (night_test), POOL (1 if the test patched ckpt == the confirm patched ckpt).
# Usage: BEST_URL=http://127.0.0.1:8001/v1 BEST_NAME=Holo-3.1-4B-patched bash osworld/night_eval.sh
set -uo pipefail
HERE="$(cd "$(dirname "$0")" && pwd)"; cd "$HERE/.."
: "${BEST_URL:?}" "${BEST_NAME:?}"
export MAX_VMS="${MAX_VMS:-5}" MIN_AVAIL_G="${MIN_AVAIL_G:-5}" PATCHED_URL="$BEST_URL" PATCHED_NAME="$BEST_NAME"
GUARD_G="${GUARD_G:-4}"
DEADLINE="${DEADLINE:-09:00}"; CT="${CONFIRM_TAG:-eager_m40}"; TT="${TEST_TAG:-night_test}"; POOL="${POOL:-0}"
end_s=$(date -u -d "$DEADLINE" +%s); [ "$end_s" -gt "$(date +%s)" ] || end_s=$(date -u -d "tomorrow $DEADLINE" +%s)
source "$HERE/arm_lib.sh"
report() {  # $1 = title
  local p="patched=" o="orig=" args
  log "report: $1"
  out=$( {
    echo "== confirm ($CT)"; PYTHONPATH=. ~/osw/venv/bin/python osworld/compare_val.py --origin other --subsets confirm \
      patched=$HOME/osw/results_val_patched_$CT prompt=$HOME/osw/results_val_prompt_$CT orig=$HOME/osw/results_val_orig_$CT
    echo "== test ($TT)"; PYTHONPATH=. ~/osw/venv/bin/python osworld/compare_val.py --origin other --subsets all \
      patched=$HOME/osw/results_val_patched_$TT orig=$HOME/osw/results_val_orig_$TT
    if [ "$POOL" = 1 ]; then echo "== pooled confirm+test (stratified)"; PYTHONPATH=. ~/osw/venv/bin/python osworld/compare_val.py \
      --origin other --strata confirm,test --subsets split:confirm,split:test,pooled \
      patched=$HOME/osw/results_val_patched_$CT,$HOME/osw/results_val_patched_$TT \
      orig=$HOME/osw/results_val_orig_$CT,$HOME/osw/results_val_orig_$TT; fi
  } 2>&1 | grep -v Warn)
  echo "$out" > ~/osw/night_report_$(date -u +%H%M).txt
  argos send ares "online-eval night: $1
$out"
}

log "night plan: best=$BEST_NAME@$BEST_URL caps vms<=$MAX_VMS avail>=${MIN_AVAIL_G}G deadline $DEADLINE pool=$POOL"
tmux kill-session -t "osw_val_followup_$CT" 2>/dev/null && log "prompt follow-up cancelled (prompt only if capacity remains)"
ram_guard & GUARD_PID=$!; trap 'kill $GUARD_PID 2>/dev/null' EXIT

wait_for "orig confirm" "exited osw_val_$CT:orig ORIG_EXIT" || { report "deadline before test start"; exit 1; }
launch patched "$TT" test || exit 1
tmux new-session -d -s "osw_val_watch_$TT" "SUBSETS=all bash osworld/watch_val.sh $TT other ares 10; exec bash" 2>/dev/null

wait_for "patched confirm" "exited osw_val_$CT:patched PATCHED_EXIT"
report "confirm arms finished (orig + lm40)"
launch orig "$TT" test || exit 1

# rescale the survivor when one test arm ends (kill + RESUME with the freed capacity)
wait_for "a test arm to finish" "exited osw_val_$TT:patched PATCHED_EXIT || exited osw_val_$TT:orig ORIG_EXIT"
for arm in patched orig; do
  U=$(echo $arm | tr a-z A-Z)_EXIT
  if ! exited "osw_val_$TT:$arm" "$U" && running "$arm" "$TT"; then
    ( flock 9; stop_arm "$arm" "$TT" ) 9>"$LOCK"
    launch "$arm" "$TT" test
  fi
done
wait_for "both test arms" "exited osw_val_$TT:patched PATCHED_EXIT && exited osw_val_$TT:orig ORIG_EXIT"
report "TEST arms finished"

# spare capacity until the deadline: prompt arm on confirm (resumes its finished tasks)
if [ $(( end_s - $(date +%s) )) -gt 3600 ]; then
  launch prompt "$CT" confirm && wait_for "prompt confirm" "exited osw_val_$CT:prompt PROMPT_EXIT"
fi
running prompt "$CT" && stop_arm prompt "$CT"
report "night plan done"
log NIGHT_EXIT
