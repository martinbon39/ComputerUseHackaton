#!/usr/bin/env bash
set -euo pipefail
arm="${1:?arm required}"
[[ "$arm" =~ ^[a-z0-9_]+$ ]]
cd /workspace/astra/moon-leak
trap 'bash stop_server.sh "$arm"' EXIT
ready=0
for attempt in $(seq 1 150); do
  if curl -fsS http://127.0.0.1:8030/health >/dev/null 2>&1; then
    ready=1
    break
  fi
  sleep 2
done
[[ "$ready" == 1 ]]
bash run_evaluation.sh "$arm"
env OMP_NUM_THREADS=2 MKL_NUM_THREADS=2 OPENBLAS_NUM_THREADS=2 taskset -c 40,41 \
  /workspace/venv/bin/python summarize_screen.py "$arm"
