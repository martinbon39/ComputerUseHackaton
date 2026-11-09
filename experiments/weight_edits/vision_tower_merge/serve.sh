#!/usr/bin/env bash
set -euo pipefail
arm="$1"
checkpoint="$2"
state=/workspace/astra/moon-vision
export HF_HOME=/workspace/hf HF_HUB_OFFLINE=1 OMP_NUM_THREADS=2 MKL_NUM_THREADS=2 OPENBLAS_NUM_THREADS=2 TOKENIZERS_PARALLELISM=false
export VLLM_CACHE_ROOT="$state/cache/vllm" CUDA_CACHE_PATH="$state/cache/cuda"
export TORCHINDUCTOR_CACHE_DIR="$state/cache/inductor" TRITON_CACHE_DIR="$state/cache/triton"
mkdir -p "$VLLM_CACHE_ROOT" "$CUDA_CACHE_PATH" "$TORCHINDUCTOR_CACHE_DIR" "$TRITON_CACHE_DIR"
for cache in "$VLLM_CACHE_ROOT" "$CUDA_CACHE_PATH" "$TORCHINDUCTOR_CACHE_DIR" "$TRITON_CACHE_DIR"; do
  if findmnt -n -o OPTIONS --target "$cache" | tr ',' '\n' | grep -qx noexec; then
    printf 'Executable compiler cache required: %s\n' "$cache" >&2
    exit 2
  fi
done
export PATH="/workspace/vllm-venv/bin:$PATH"
printf '%s\n' "$$" > "$state/server_${arm}.pid"
exec /workspace/vllm-venv/bin/python -m vllm.entrypoints.openai.api_server \
 --model "$checkpoint" --served-model-name "moon_vision_${arm}" \
 --dtype bfloat16 --max-model-len 32768 --max-num-seqs 32 \
 --gpu-memory-utilization 0.15 --kv-cache-memory-bytes 8G \
 --limit-mm-per-prompt '{"image":5}' --reasoning-parser qwen3 \
 --enable-prefix-caching --host 127.0.0.1 --port 8028
