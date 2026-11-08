#!/usr/bin/env bash
# Live duel page (orbit). One entry point:
#   bash duel.sh serve [pod|modal]   start the page server (tmux duel_server, devcap 1G) on 127.0.0.1:8765
#   bash duel.sh list                recorded duels (id, task, verdicts)
#   bash duel.sh replay <id|last>    URL that replays a recorded duel at real speed in the same page
#   bash duel.sh stop                STOP every running duel (both VMs closed)
# From another machine: ssh -L 8765:127.0.0.1:8765 orbit, then open http://127.0.0.1:8765/
set -euo pipefail
HERE="$(cd "$(dirname "$0")" && pwd)"; PORT=8765; ROOT="$HOME/osw/duels"
up() { curl -sf -m 3 "127.0.0.1:$PORT/api/config" > /dev/null; }
case "${1:-}" in
  serve)
    up && { echo "already serving: http://127.0.0.1:$PORT/"; exit 0; }
    tmux new-session -d -s duel_server "cd $HERE && devcap --mem 1G ~/osw/venv/bin/python duel_server.py --port $PORT --preset ${2:-pod} 2>&1 | tee -a ~/osw/duel_server.log"
    for _ in $(seq 20); do up && { echo "http://127.0.0.1:$PORT/"; exit 0; }; sleep 0.5; done
    echo "server did not start, see ~/osw/duel_server.log" >&2; exit 1 ;;
  list)
    up || { echo "server down: bash $0 serve" >&2; exit 1; }
    curl -s "127.0.0.1:$PORT/api/duels" | python3 -c '
import json, sys
for d in json.load(sys.stdin):
    c = lambda s: ("ok" if s["verdict"]["score"] >= 1 else "FAIL" + (" (claimed done)" if s["verdict"]["claimed_done"] else "")) if s["verdict"] else (s["last_phase"] or "-")
    print(d["id"], "| original:", c(d["sides"]["left"]), "| modified:", c(d["sides"]["right"]), "| running" if d["running"] else "")' ;;
  replay)
    up || { echo "server down: bash $0 serve" >&2; exit 1; }
    id="${2:?duel id or last}"; [ "$id" = last ] && id=$(ls -t "$ROOT" | head -1)
    [ -f "$ROOT/$id/meta.json" ] || { echo "no duel $id in $ROOT" >&2; exit 1; }
    echo "http://127.0.0.1:$PORT/?replay=$id" ;;
  stop)
    curl -s -X POST "127.0.0.1:$PORT/api/stop" -d '{"side":"all"}'; echo ;;
  *) sed -n 2,7p "$0"; exit 2 ;;
esac
