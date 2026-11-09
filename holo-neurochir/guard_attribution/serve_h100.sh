#!/usr/bin/env bash
# Serve Holo-3.1-4B (pinned revision) with the pinned vLLM args, one server per GPU, on 127.0.0.1:8000+i.
# Dry run by default (prints the commands). --go downloads the model and starts the servers.
# Usage: bash serve_h100.sh [--gpus 8] [--venv DIR] [--go]
# The key: export HOLO_VLLM_KEY=... before --go (servers require it; runner.py reads it with --api-key-env).
set -euo pipefail
HERE="$(cd "$(dirname "$0")" && pwd)"
GPUS=8; VENV="$HOME/vllm-venv"; GO=0
while [ $# -gt 0 ]; do case "$1" in
  --gpus) GPUS="$2"; shift 2;; --venv) VENV="$2"; shift 2;; --go) GO=1; shift;; *) echo "unknown $1"; exit 2;; esac; done
read -r REPO REV NAME < <(python3 -c "import json;p=json.load(open('$HERE/pins.json'));m=p['model'];print(m['hf_repo'],m['revision'],m['study_served_model_name'])")
mapfile -t ARGS < <(python3 -c "import json;[print(a) for a in json.load(open('$HERE/pins.json'))['vllm']['args']]")
PIP=$(python3 -c "import json;print(' '.join(json.load(open('$HERE/pins.json'))['vllm']['pip']))")
run() { if [ "$GO" = 1 ]; then "$@"; else echo "DRY: $*"; fi; }
echo "# 1. environment (python 3.12, CUDA 12.8 driver >= 570)"
[ -x "$VENV/bin/python" ] || run python3.12 -m venv "$VENV"
run "$VENV/bin/pip" install $PIP "huggingface_hub[hf_transfer]"
echo "# 2. weights at the pinned revision, then sha256 check"
run env HF_HUB_ENABLE_HF_TRANSFER=1 "$VENV/bin/huggingface-cli" download "$REPO" --revision "$REV"
SNAP="${HF_HOME:-$HOME/.cache/huggingface}/hub/models--${REPO/\//--}/snapshots/$REV"
run python3 "$HERE/check_weights.py" "$SNAP"
echo "# 3. one server per GPU"
[ "$GO" = 1 ] && : "${HOLO_VLLM_KEY:?export HOLO_VLLM_KEY first}"
mkdir -p "$HERE/logs" 2>/dev/null || true
for i in $(seq 0 $((GPUS-1))); do
  port=$((8000+i))
  if [ "$GO" = 1 ]; then
    CUDA_VISIBLE_DEVICES=$i HF_HUB_OFFLINE=1 nohup "$VENV/bin/python" -m vllm.entrypoints.openai.api_server \
      --model "$SNAP" --served-model-name "$NAME" "${ARGS[@]}" --api-key "$HOLO_VLLM_KEY" \
      --host 127.0.0.1 --port "$port" > "$HERE/logs/vllm_gpu$i.log" 2>&1 &
    echo "gpu $i -> http://127.0.0.1:$port/v1 (pid $!)"
  else
    echo "DRY: CUDA_VISIBLE_DEVICES=$i HF_HUB_OFFLINE=1 $VENV/bin/python -m vllm.entrypoints.openai.api_server --model $SNAP --served-model-name $NAME ${ARGS[*]} --api-key \$HOLO_VLLM_KEY --host 127.0.0.1 --port $port"
  fi
done
echo "# base urls: $(seq -s, -f 'http://127.0.0.1:%g/v1' 8000 $((8000+GPUS-1)))"
