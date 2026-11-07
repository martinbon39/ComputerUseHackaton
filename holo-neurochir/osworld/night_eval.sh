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
GUARD_G="${GUARD_G:-4}"; LAST=~/osw/night_last_launch; LOCK=~/osw/night.lock
DEADLINE="${DEADLINE:-09:00}"; CT="${CONFIRM_TAG:-eager_m40}"; TT="${TEST_TAG:-night_test}"; POOL="${POOL:-0}"
end_s=$(date -u -d "$DEADLINE" +%s); [ "$end_s" -gt "$(date +%s)" ] || end_s=$(date -u -d "tomorrow $DEADLINE" +%s)
log() { echo "$(date -u +%H:%M) $*"; }
vms() { ~/osw/osh "docker ps -q --filter ancestor=happysixd/osworld-docker" | wc -l; }
exited() { tmux capture-pane -pt "$1" -S -30 2>/dev/null | grep -q "$2"; }
running() { pgrep -f "results_val_$1_$2 " >/dev/null; }
GB_PER_VM=4  # measured 3.7-3.9 G RSS per OSWorld VM on orbit
capacity() {  # VMs that fit under MAX_VMS and still leave MIN_AVAIL_G available after they boot; at most 3 per arm
  local c=$((MAX_VMS - $(vms))) r=$(( ($(free -g | awk '/^Mem:/ {print $7}') - MIN_AVAIL_G) / GB_PER_VM ))
  [ $r -lt $c ] && c=$r; [ $c -gt 3 ] && c=3; echo $c
}
wait_for() {  # $1 = description, $2 = condition command; bounded by DEADLINE
  until eval "$2"; do [ "$(date +%s)" -lt "$end_s" ] || { log "deadline while waiting for $1"; return 1; }; sleep 120; done
}
avail() { free -g | awk '/^Mem:/ {print $7}'; }
launch() {  # $1 = arm, $2 = tag, $3 = list, [$4 = workers, else the free capacity]
  local w="${4:-}"
  if [ -z "$w" ]; then
    w=$(capacity)
    until [ "$w" -ge 1 ]; do [ "$(date +%s)" -lt "$end_s" ] || return 1; sleep 120; w=$(capacity); done
  fi
  log "launch $1 $2 ($3) workers=$w"
  tmux kill-window -t "osw_val_$2:$1" 2>/dev/null
  (flock 9; echo "$1 $2 $3 $w" > "$LAST"
   RESUME=1 WAIT=1 ARMS="$1" MIN_AVAIL_G=$((MIN_AVAIL_G + GB_PER_VM * w)) bash osworld/run_patched_eval.sh "$2" "$3" "$w") 9>"$LOCK"
}
ram_guard() {
  local low=0
  while [ "$(date +%s)" -lt "$end_s" ]; do
    if [ "$(avail)" -lt "$GUARD_G" ]; then low=$((low + 1)); else low=0; fi
    if [ $low -ge 4 ] && [ -s "$LAST" ]; then
      read -r arm tag list w < "$LAST"
      log "RAM guard: $(avail)G < ${GUARD_G}G for 2 min -> $arm $tag from $w to $((w - 1)) workers"
      ( flock 9; stop_arm "$arm" "$tag"; tmux kill-window -t "osw_val_$tag:$arm" 2>/dev/null; : > "$LAST" ) 9>"$LOCK"
      [ "$w" -gt 1 ] && launch "$arm" "$tag" "$list" $((w - 1))
      argos send ares "online-eval night: RAM guard fired, $arm $tag restarted with $((w - 1)) workers (RESUME)"
      low=0; sleep 180
    fi
    sleep 30
  done
}
stop_arm() {  # SIGINT lets run_holo's workers close their VMs (finally: env.close())
  local pids; pids=$(pgrep -f "results_val_$1_$2 " | tr '\n' ' ')
  [ -n "$pids" ] || return 0
  log "stop $1 $2 (SIGINT $pids)"; for p in $pids; do pkill -INT -P "$p" 2>/dev/null; kill -INT "$p" 2>/dev/null; done
  for i in $(seq 1 30); do running "$1" "$2" || break; sleep 5; done
  running "$1" "$2" && { log "still running after SIGINT, TERM"; kill $(pgrep -f "results_val_$1_$2 ") 2>/dev/null; }
}
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
