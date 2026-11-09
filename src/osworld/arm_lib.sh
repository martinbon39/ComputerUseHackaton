#!/usr/bin/env bash
# Shared arm control for the online-validation schedulers (night_eval.sh, prompt_priority.sh): capacity (VM cap and
# RAM floor), launch / stop / RESUME of one arm via run_patched_eval.sh, and the RAM guard. Source it after setting
# MAX_VMS, MIN_AVAIL_G, GUARD_G, end_s (deadline, epoch s); run from holo-neurochir/.
LAST=~/osw/night_last_launch; LOCK=~/osw/night.lock
log() { echo "$(date -u +%H:%M) $*"; }
vms() { ~/osw/osh "docker ps -q --filter ancestor=happysixd/osworld-docker" | wc -l; }
exited() { tmux capture-pane -pt "$1" -S -30 2>/dev/null | grep -q "$2"; }
armpat() { echo "run_(osw|osw_verify|holo|holo_verify)[.a-z]* .*results_val_$1_$2 "; }  # only the arm's own processes
running() { pgrep -f "$(armpat "$1" "$2")" >/dev/null; }
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
  (flock 9; echo "$1 $2 $3 $w ${PATCHED_URL:--} ${PATCHED_NAME:--}" > "$LAST"
   RESUME=1 WAIT=1 ARMS="$1" MIN_AVAIL_G=$((MIN_AVAIL_G + GB_PER_VM * w)) bash osworld/run_patched_eval.sh "$2" "$3" "$w") 9>"$LOCK"
}
ram_guard() {
  local low=0
  while [ "$(date +%s)" -lt "$end_s" ]; do
    if [ "$(avail)" -lt "$GUARD_G" ]; then low=$((low + 1)); else low=0; fi
    if [ $low -ge 4 ] && [ -s "$LAST" ]; then
      read -r arm tag list w purl pname < "$LAST"
      [ "$purl" = - ] || export PATCHED_URL="$purl" PATCHED_NAME="$pname"  # restart against the arm's own server
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
  local pids; pids=$(pgrep -f "$(armpat "$1" "$2")" | tr '\n' ' ')
  [ -n "$pids" ] || return 0
  log "stop $1 $2 (SIGINT $pids)"; for p in $pids; do pkill -INT -P "$p" 2>/dev/null; kill -INT "$p" 2>/dev/null; done
  for i in $(seq 1 30); do running "$1" "$2" || break; sleep 5; done
  running "$1" "$2" && { log "still running after SIGINT, TERM"; kill $(pgrep -f "$(armpat "$1" "$2")") 2>/dev/null; }
}
