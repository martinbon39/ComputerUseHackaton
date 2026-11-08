#!/usr/bin/env bash
set -euo pipefail

checkpoint="${1:?usage: serve.sh CHECKPOINT ARM [PORT]}"
arm="${2:?usage: serve.sh CHECKPOINT ARM [PORT]}"
port="${3:-8030}"
if [[ ! "$arm" =~ ^[A-Za-z0-9_.-]+$ ]]; then
  echo "invalid arm" >&2
  exit 2
fi
if [[ ! -d "$checkpoint" ]]; then
  echo "checkpoint directory does not exist: $checkpoint" >&2
  exit 2
fi
if [[ ! "$port" =~ ^[0-9]+$ ]] || (( port < 1 || port > 65535 )); then
  echo "invalid port: $port" >&2
  exit 2
fi

state=/workspace/astra/moon-leak
mkdir -p "$state"
export HF_HOME=/workspace/hf
export HF_HUB_OFFLINE=1
export OMP_NUM_THREADS=2
export MKL_NUM_THREADS=2
export OPENBLAS_NUM_THREADS=2
export TOKENIZERS_PARALLELISM=false
export PATH="/workspace/vllm-venv/bin:$PATH"

printf '%s\n' "$$" > "$state/server_${arm}.pid"
exec /workspace/vllm-venv/bin/python -m vllm.entrypoints.openai.api_server \
  --model "$(realpath "$checkpoint")" \
  --served-model-name "moon_leak_${arm}" \
  --dtype bfloat16 \
  --max-model-len 32768 \
  --max-num-seqs 32 \
  --gpu-memory-utilization 0.15 \
  --kv-cache-memory-bytes 6G \
  --limit-mm-per-prompt '{"image":5}' \
  --reasoning-parser qwen3 \
  --enable-prefix-caching \
  --host 127.0.0.1 \
  --port "$port"
