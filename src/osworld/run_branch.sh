#!/usr/bin/env bash
# Run branch_runner.py in a fresh login (docker + kvm), with run_osw.sh's exact environment (derived from it).
# Usage: [MODAL_KEY=1] bash osworld/run_branch.sh <log> <branch_runner args...>
#   MODAL_KEY=1 exports MODAL_HDR from ~/.holo_modal_key inside the login, for --server URL=NAME=MODAL_HDR.
set -euo pipefail
LOG="$1"; shift
HERE="$(cd "$(dirname "$0")" && pwd)"
line=$(grep -o 'cd ~/osw/rtg/Env/OSWorld && export [^&]*&&' ~/osw/run_osw.sh)
[ -n "$line" ] || { echo "run_osw.sh layout changed" >&2; exit 1; }
key=""; [ "${MODAL_KEY:-0}" = 1 ] && key='export MODAL_HDR="Authorization: Bearer $(cat ~/.holo_modal_key)" && '
exec ~/osw/osh "$line ${key}PYTHONPATH=$HERE/.. ~/osw/venv/bin/python $HERE/branch_runner.py $* 2>&1 | tee -a $LOG"
