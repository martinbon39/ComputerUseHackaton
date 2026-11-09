#!/usr/bin/env bash
set -euo pipefail
arm=${1:?original or candidate}
state=/dev/shm/astra-regmean
case "$arm" in
  original)
    checkpoint=/workspace/hf/hub/models--Hcompany--Holo-3.1-4B/snapshots/8c88265a5a159bfd1492db9243733dd2e6e04a6e
    model_name=regmean_original_fp16
    ;;
  candidate)
    checkpoint=/dev/shm/regmean_cua_centered_fp16
    model_name=regmean_cua_centered_fp16
    python3 - "$state/VERIFY_CHECKPOINT_FP16.json" "$checkpoint" <<'PY'
import json, sys
v = json.load(open(sys.argv[1]))
assert v['status'] == 'PASSED'
assert v['target'] == sys.argv[2]
PY
    ;;
  *) exit 2 ;;
esac
if ss -lnt '( sport = :8023 )' | tail -n +2 | read -r _; then
  exit 1
fi
export HF_HOME=/workspace/hf HF_HUB_OFFLINE=1 OMP_NUM_THREADS=2 MKL_NUM_THREADS=2 OPENBLAS_NUM_THREADS=2
export PATH="/workspace/vllm-venv/bin:$PATH"
printf '%s\n' "$$" > "$state/server.pid"
exec /workspace/vllm-venv/bin/python -m vllm.entrypoints.openai.api_server \
  --model "$checkpoint" --served-model-name "$model_name" \
  --dtype float16 --max-model-len 32768 --max-num-seqs 64 \
  --gpu-memory-utilization 0.15 --kv-cache-memory-bytes 4G \
  --limit-mm-per-prompt '{"image":5}' --reasoning-parser qwen3 \
  --enable-prefix-caching --host 0.0.0.0 --port 8023
