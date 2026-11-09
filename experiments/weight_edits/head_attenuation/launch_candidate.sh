#!/usr/bin/env bash
set -euo pipefail
name="$1"
[[ "$name" =~ ^[a-z0-9_]+$ ]]
cd /workspace/astra/moon-leak
export OMP_NUM_THREADS=2 MKL_NUM_THREADS=2 OPENBLAS_NUM_THREADS=2
checkpoint="/dev/shm/moon-leak/$name"
taskset -c 40,41 /workspace/venv/bin/python build_head_edit.py "spec_$name.json" > "build_$name.log" 2>&1
taskset -c 40,41 /workspace/venv/bin/python verify_head_edit.py "/workspace/astra/moon-leak/spec_$name.json" "$checkpoint" > "verify_$name.log" 2>&1
exec bash /workspace/osw_shared/gpu_slot.sh bash serve.sh "$checkpoint" "$name" 8030
