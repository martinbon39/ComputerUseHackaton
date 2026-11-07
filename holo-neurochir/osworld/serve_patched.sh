#!/usr/bin/env bash
# On the GPU pod: serve a patched Holo-3.1-4B checkpoint (scripts/make_patched_ckpt.py) next to production vLLM:8000.
# Small GPU share (memory is shared with production); same serving flags as serve_vllm.sh otherwise. The KV size is
# fixed: vLLM's profiling reads global free GPU memory, so jobs starting meanwhile made 0.15 alone yield KV < 0.
# Pod port 8011: the pod's 8001 is Runpod's nginx proxy. orbit reaches it as 127.0.0.1:8001 (tmux osw_tunnel2).
# Usage: bash serve_patched.sh <ckpt_dir> [port=8011] [served_name=Holo-3.1-4B-patched]   -> tmux vllm_<port>
# Stop:  tmux kill-session -t vllm_<port>
set -e
CKPT="$1"; PORT="${2:-8011}"; NAME="${3:-Holo-3.1-4B-patched}"
[ -f "$CKPT/model.safetensors.index.json" ] || { echo "no checkpoint in $CKPT" >&2; exit 1; }
! tmux has-session -t "vllm_$PORT" 2>/dev/null || { echo "tmux vllm_$PORT already running" >&2; exit 1; }
! ss -ltn | awk '{print $4}' | grep -q ":$PORT\$" || { echo "port $PORT already in use" >&2; exit 1; }
tmux new-session -d -s "vllm_$PORT" "env HF_HOME=/workspace/hf HF_HUB_OFFLINE=1 PATH=/workspace/vllm-venv/bin:\$PATH \
  /workspace/vllm-venv/bin/python -m vllm.entrypoints.openai.api_server --model $CKPT --served-model-name $NAME \
  --dtype bfloat16 --max-model-len 32768 --max-num-seqs 16 --gpu-memory-utilization 0.15 --kv-cache-memory-bytes 6G \
  --limit-mm-per-prompt '{\"image\": 5}' --reasoning-parser qwen3 --enable-prefix-caching \
  --host 0.0.0.0 --port $PORT > /workspace/logs/vllm_$PORT.log 2>&1"
for i in $(seq 1 90); do
  curl -sf "http://127.0.0.1:$PORT/v1/models" | grep -q "\"$NAME\"" && { echo "vllm_$PORT ready ($NAME <- $CKPT)"; exit 0; }
  tmux has-session -t "vllm_$PORT" 2>/dev/null || { echo "vllm_$PORT died, see /workspace/logs/vllm_$PORT.log" >&2; exit 1; }
  sleep 5
done
echo "vllm_$PORT not ready after 450 s, see /workspace/logs/vllm_$PORT.log" >&2; exit 1
