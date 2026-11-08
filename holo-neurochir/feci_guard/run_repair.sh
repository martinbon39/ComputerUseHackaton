#!/usr/bin/env bash
# Repair measure: the same episodes, K continuations per arm, at the recorded answer step (branch_back 0 = "t-1").
#   arm A, no guard: osworld/branch_runner.py unchanged     arm B, guard: feci_guard/repair_runner.py
# Each arm owns one VM. run_osw.sh's exact environment (derived from it, as osworld/run_branch.sh does).
# Usage: bash run_repair.sh nog|guard <out_dir> <episodes.txt> [K=2]
set -euo pipefail
ARM="$1"; OUT="$2"; EPS="$3"; K="${4:-2}"
G="$(cd "$(dirname "$0")" && pwd)"; N="$G/../osworld"
line=$(grep -o 'cd ~/osw/rtg/Env/OSWorld && export [^&]*&&' ~/osw/run_osw.sh)
[ -n "$line" ] || { echo "run_osw.sh layout changed" >&2; exit 1; }
args=""; for e in $(cat "$EPS"); do args="$args --episode $e"; done
mkdir -p "$OUT"
case "$ARM" in
  nog)   cmd="PYTHONPATH=$G/.. ~/osw/venv/bin/python $N/branch_runner.py --mode branch --k $K --branch_back 0 --server http://127.0.0.1:8000/v1=Holo-3.1-4B --out $OUT $args" ;;
  guard) cmd="~/osw/venv/bin/python $G/repair_runner.py --k $K --branch_back 0 --server http://127.0.0.1:8000/v1=Holo-3.1-4B --out $OUT $args" ;;
  *) echo "arm: nog|guard" >&2; exit 1 ;;
esac
exec ~/osw/osh "$line $cmd 2>&1 | tee -a $OUT.log"
