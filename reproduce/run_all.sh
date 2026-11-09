#!/usr/bin/env bash
# CPU checks of the paper's headline numbers: no GPU, no key, no VM, Python >= 3.9 standard library only.
# Exit 0 = every number below recomputed from committed data and equal to the value reported in the paper.
set -euo pipefail
cd "$(dirname "$0")/.."
PY="${PYTHON:-python3}"
export PYTHONDONTWRITEBYTECODE=1

echo "== (1) OSWorld paired comparisons of the weight edits, recomputed from per-task scores =="
"$PY" reproduce/verify_results.py

echo; echo "== (2) Feci Guard replayed on 268 recorded episodes (frozen decision code, recorded verdicts) =="
"$PY" reproduce/replay_guard.py --show 1

echo; echo "== (3) the three judges recounted from their raw responses =="
"$PY" reproduce/recount_judges.py | tail -6

echo; echo "== (4) online Feci Guard test, 120 OSWorld tasks =="
"$PY" reproduce/verify_online_guard.py

echo; echo "ALL CHECKS OK: (1)-(4) match the numbers reported in the paper."
