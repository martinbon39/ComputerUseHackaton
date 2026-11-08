#!/usr/bin/env bash
set -euo pipefail
arm="${1:?arm required}"
[[ "$arm" =~ ^[a-z0-9_]+$ ]]
cd /workspace/astra/moon-leak
exec env OMP_NUM_THREADS=2 MKL_NUM_THREADS=2 OPENBLAS_NUM_THREADS=2 taskset -c 40,41 \
 /workspace/vllm-venv/bin/python evaluate.py "/dev/shm/moon-leak/$arm" "$arm"
