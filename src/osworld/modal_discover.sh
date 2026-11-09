#!/usr/bin/env bash
# On orbit: every 60 s, list holo-models:/ckpt on both Modal accounts and queue every new checkpoint matching <regex>
# (one that has no ~/modal_queue/<ckpt>.log yet) with modal_serve_when_ready.sh: its own account first, then the
# other one; priority 1 if the name matches <prio1-regex>, else 2. Ends after 10 h.
# Usage: nohup bash osworld/modal_discover.sh '^merge_' '_l1223_' >> ~/modal_queue/discover.log 2>&1 &
set -uo pipefail
cd "$(dirname "$0")/.."
PATTERN="$1"; PRIO1="$2"; Q=~/modal_queue; END=$(( $(date +%s) + 10 * 3600 ))
while [ "$(date +%s)" -lt "$END" ]; do
  for a in 1 2; do
    p=$([ "$a" = 1 ] && echo emilejouannet || echo martinbon39); other=$([ "$a" = 1 ] && echo 2 || echo 1)
    for c in $(MODAL_PROFILE=$p modal volume ls holo-models /ckpt --json 2>/dev/null |
               python3 -c "import sys,json; print(' '.join(x['filename'].split('/')[-1] for x in json.load(sys.stdin)))"); do
      [[ "$c" =~ $PATTERN ]] || continue
      [ -e "$Q/$c.log" ] && continue
      prio=2; [[ "$c" =~ $PRIO1 ]] && prio=1
      setsid nohup bash osworld/modal_serve_when_ready.sh "$c" "$a,$other" "$prio,$prio" > "$Q/$c.log" 2>&1 < /dev/null &
      echo "$(date -u +%T) queued $c (accounts $a,$other, prio $prio)"
    done
  done
  sleep 60
done
