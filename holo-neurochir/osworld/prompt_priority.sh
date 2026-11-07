#!/usr/bin/env bash
# Give the prompt arm on confirm the capacity freed by the running arms (ares, 22:14 UTC): start it now with what fits,
# and each time orig or patched of <tag> finishes, restart it (RESUME) with the larger capacity. RAM guard on.
# Bounded by DEADLINE. Env: TAG (eager_m40), MAX_VMS (5), MIN_AVAIL_G (5), GUARD_G (4), DEADLINE (09:00 UTC).
# Usage: bash osworld/prompt_priority.sh
set -uo pipefail
HERE="$(cd "$(dirname "$0")" && pwd)"; cd "$HERE/.."
export MAX_VMS="${MAX_VMS:-5}" MIN_AVAIL_G="${MIN_AVAIL_G:-5}"; GUARD_G="${GUARD_G:-4}"
CT="${TAG:-eager_m40}"; DEADLINE="${DEADLINE:-09:00}"
end_s=$(date -u -d "$DEADLINE" +%s); [ "$end_s" -gt "$(date +%s)" ] || end_s=$(date -u -d "tomorrow $DEADLINE" +%s)
source "$HERE/arm_lib.sh"

log "prompt priority on $CT: vms<=$MAX_VMS avail>=${MIN_AVAIL_G}G guard ${GUARD_G}G deadline $DEADLINE"
ram_guard & GUARD_PID=$!; trap 'kill $GUARD_PID 2>/dev/null' EXIT
launch prompt "$CT" confirm || exit 1
for other in orig patched; do
  wait_for "$other $CT" "exited osw_val_$CT:$other $(echo $other | tr a-z A-Z)_EXIT" || break
  exited "osw_val_$CT:prompt" PROMPT_EXIT && break
  log "$other finished: restart prompt with the freed capacity"
  ( flock 9; stop_arm prompt "$CT" ) 9>"$LOCK"
  launch prompt "$CT" confirm || break
done
wait_for "prompt $CT" "exited osw_val_$CT:prompt PROMPT_EXIT"
log PRIORITY_EXIT
