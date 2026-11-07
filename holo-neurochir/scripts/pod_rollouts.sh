#!/usr/bin/env bash
# Run sharded rollouts on the GPU pod, one tmux session per shard (survives SSH drops).
# Usage: bash scripts/pod_rollouts.sh <model_id> <N_shards> <rollouts.py args...>
# e.g.   bash scripts/pod_rollouts.sh Hcompany/Holo-3.1-4B 8 --tag diag4b --tasks "$(cat runs_pilot_tasks.txt)" --seeds 0-7
set -e
MODEL="$1"; N="$2"; shift 2
cd /workspace/projet
export HF_HOME=/workspace/hf PLAYWRIGHT_BROWSERS_PATH=/workspace/pw HF_HUB_OFFLINE=1 HOLO_MODEL="$MODEL"
export MINIWOB_URL=http://127.0.0.1:8765/miniwob/ PYTHONUNBUFFERED=1 HOLO_RUNS=${HOLO_RUNS:-/workspace/runs}
# MiniWoB static server (idempotent)
if ! curl -s -o /dev/null http://127.0.0.1:8765/miniwob/click-button.html; then
  tmux new-session -d -s miniwob "cd /workspace/miniwob-plusplus/miniwob/html && /workspace/venv/bin/python -m http.server 8765 --bind 127.0.0.1"
  sleep 2
fi
SESSION="ro_$(date +%H%M%S)"
ARGS=$(printf '%q ' "$@")
mkdir -p /workspace/logs
for i in $(seq 0 $((N-1))); do
  tmux new-session -d -s "${SESSION}_s$i" \
    "/workspace/venv/bin/python -m holo.rollouts $ARGS --shard $i/$N > /workspace/logs/${SESSION}_s$i.out 2>&1"
done
echo "$SESSION"
