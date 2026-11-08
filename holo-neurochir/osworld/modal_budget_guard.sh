#!/usr/bin/env bash
# On orbit: every 10 min, read each Modal account's spend of the day (modal billing report); at WARN $ tell ares once,
# at STOP $ stop holo-vllm and holo-slot on that account, close the jury gate, and tell ares. Hard budget 25 $ per
# account. Spend = full days since START (UTC) + today so far (the report omits the current partial interval). Ends after 14 h.
# Usage: nohup bash osworld/modal_budget_guard.sh [WARN=20] [STOP=24] [START=2026-11-01] >> ~/modal_budget_guard.log 2>&1 &
set -uo pipefail
WARN="${1:-20}"; STOP="${2:-24}"; START="${3:-2026-11-01}"; END=$(( $(date +%s) + 14 * 3600 ))
declare -A warned stopped fails
report() { MODAL_PROFILE=$1 timeout 90 modal billing report "${@:2}" --json 2>/dev/null |
           python3 -c "import sys,json; print(sum(float(r['cost']) for r in json.load(sys.stdin)))" 2>/dev/null; }
while [ "$(date +%s)" -lt "$END" ]; do
  for p in emilejouannet martinbon39; do
    a=$(report "$p" --start "$START"); b=$(report "$p" --for today)
    cost=$([ -n "$a" ] && [ -n "$b" ] && python3 -c "print(round($a + $b, 2))")
    if [ -z "$cost" ]; then
      fails[$p]=$(( ${fails[$p]:-0} + 1 )); echo "$(date -u +%T) $p billing unreadable (${fails[$p]} in a row)"
      [ "${fails[$p]}" -eq 3 ] && bash "$(dirname "$0")/modal_jury_gate.sh" close >/dev/null 2>&1 &&
        argos send ares "modal-serve (garde-budget): facturation de $p illisible 3 fois de suite, porte du jury fermée par prudence."
      continue
    fi
    fails[$p]=0
    echo "$(date -u +%T) $p $cost"
    if python3 -c "import sys; sys.exit(0 if $cost >= $STOP else 1)" && [ -z "${stopped[$p]:-}" ]; then
      MODAL_PROFILE=$p modal app stop holo-vllm -y >/dev/null 2>&1; MODAL_PROFILE=$p modal app stop holo-slot -y >/dev/null 2>&1
      bash "$(dirname "$0")/modal_jury_gate.sh" close >/dev/null 2>&1
      stopped[$p]=1; argos send ares "modal-serve (garde-budget): compte $p à $cost \$ ≥ $STOP \$ : holo-vllm et holo-slot ARRÊTÉS sur ce compte, porte du jury fermée."
    elif python3 -c "import sys; sys.exit(0 if $cost >= $WARN else 1)" && [ -z "${warned[$p]:-}" ]; then
      warned[$p]=1; argos send ares "modal-serve (garde-budget): compte $p à $cost \$ (seuil $WARN \$). Arrêt automatique à $STOP \$."
    fi
  done
  sleep 600
done
