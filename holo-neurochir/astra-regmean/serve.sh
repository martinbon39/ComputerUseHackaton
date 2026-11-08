#!/usr/bin/env bash
set -euo pipefail
checkpoint=/dev/shm/regmean_cua_centered
state=/dev/shm/astra-regmean
test -f "$checkpoint/regmean_manifest.json"
test -f "$state/VERIFY_CHECKPOINT.json"
OMP_NUM_THREADS=2 MKL_NUM_THREADS=2 OPENBLAS_NUM_THREADS=2 python3 - "$state/VERIFY_CHECKPOINT.json" <<'PY'
import json, sys
v = json.load(open(sys.argv[1]))
assert v['status'] == 'PASSED'
assert v['target'] == '/dev/shm/regmean_cua_centered'
PY
if ss -lnt '( sport = :8023 )' | tail -n +2 | read -r _; then
  exit 1
fi
export HF_HOME=/workspace/hf HF_HUB_OFFLINE=1 OMP_NUM_THREADS=2 MKL_NUM_THREADS=2 OPENBLAS_NUM_THREADS=2
export PATH="/workspace/vllm-venv/bin:$PATH"
printf '%s\n' "$$" > "$state/server.pid"
exec /workspace/vllm-venv/bin/python -m vllm.entrypoints.openai.api_server \
  --model "$checkpoint" --served-model-name regmean_cua_centered \
  --dtype bfloat16 --max-model-len 32768 --max-num-seqs 64 \
  --gpu-memory-utilization 0.15 --kv-cache-memory-bytes 4G \
  --limit-mm-per-prompt '{"image":5}' --reasoning-parser qwen3 \
  --enable-prefix-caching --host 0.0.0.0 --port 8023
