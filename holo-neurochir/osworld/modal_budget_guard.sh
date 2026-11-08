#!/usr/bin/env bash
# On orbit: every 10 min, read each Modal account's spend of the day (modal billing report); at WARN $ tell ares once,
# at STOP $ stop holo-vllm and holo-slot on that account and tell ares. Hard budget 25 $ per account. Ends after 14 h.
# Usage: nohup bash osworld/modal_budget_guard.sh [WARN=20] [STOP=24] >> ~/modal_budget_guard.log 2>&1 &
set -uo pipefail
WARN="${1:-20}"; STOP="${2:-24}"; END=$(( $(date +%s) + 14 * 3600 ))
declare -A warned stopped
while [ "$(date +%s)" -lt "$END" ]; do
  for p in emilejouannet martinbon39; do
    cost=$(MODAL_PROFILE=$p timeout 90 modal billing report --for today --json 2>/dev/null |
           python3 -c "import sys,json; print(round(sum(float(r['cost']) for r in json.load(sys.stdin)), 2))" 2>/dev/null)
    [ -z "$cost" ] && { echo "$(date -u +%T) $p billing unreadable"; continue; }
    echo "$(date -u +%T) $p $cost"
    if python3 -c "import sys; sys.exit(0 if $cost >= $STOP else 1)" && [ -z "${stopped[$p]:-}" ]; then
      MODAL_PROFILE=$p modal app stop holo-vllm -y >/dev/null 2>&1; MODAL_PROFILE=$p modal app stop holo-slot -y >/dev/null 2>&1
      stopped[$p]=1; argos send ares "modal-serve (garde-budget): compte $p à $cost \$ ≥ $STOP \$ : holo-vllm et holo-slot ARRÊTÉS sur ce compte."
    elif python3 -c "import sys; sys.exit(0 if $cost >= $WARN else 1)" && [ -z "${warned[$p]:-}" ]; then
      warned[$p]=1; argos send ares "modal-serve (garde-budget): compte $p à $cost \$ (seuil $WARN \$). Arrêt automatique à $STOP \$."
    fi
  done
  sleep 600
done
