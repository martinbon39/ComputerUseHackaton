#!/usr/bin/env bash
# Exploratory sensitivity: wait until the given registered arm has finished (24 branches, process gone), then run the
# guard arm with --max_new 30 on refused episodes not yet taken by another slot. Usage: sens_launch.sh nog|guard <slot>
set -euo pipefail
ARM="$1"; SLOT="$2"; R=$HOME/osw/feci_repair; G="$(cd "$(dirname "$0")/.." && pwd)"
pat=$([ "$ARM" = nog ] && echo "osworld/branch_runner.py --mode branch" || echo "feci_guard/repair_runner.py --k 2 --branch_back 0 --server http://127.0.0.1:8000/v1=Holo-3.1-4B --out $R/guard ")
while [ "$(wc -l < $R/$ARM/branches.jsonl)" -lt 24 ] || pgrep -f "$pat" >/dev/null; do sleep 30; done
[ "$(date -u +%H%M)" -lt 1045 ] || { echo "too late, no sensitivity on slot $SLOT"; exit 0; }
python3 - "$R" "$G/repair/episodes.txt" "$R/sens_$SLOT.txt" <<'EOP'
import json, sys, glob
R, eps_file, out = sys.argv[1:]
refused = {json.loads(l)["task"] for l in open(f"{R}/guard/branches.jsonl")
           if (json.loads(l).get("guard") or {}).get("refusals")}
taken = {l.strip() for f in glob.glob(f"{R}/sens_*.txt") for l in open(f)}
eps = [e.strip() for e in open(eps_file) if any(e.strip().endswith(t) for t in refused) and e.strip() not in taken]
open(out, "w").write("".join(e + "\n" for e in eps)); print(len(eps), "episodes for slot", out)
EOP
[ -s "$R/sens_$SLOT.txt" ] || { echo "nothing left"; exit 0; }
exec bash "$G/run_repair.sh" guard "$R/sens30_$SLOT" "$R/sens_$SLOT.txt" 2 --max_new 30
