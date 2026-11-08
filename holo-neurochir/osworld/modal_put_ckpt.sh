#!/usr/bin/env bash
# On the GPU pod: upload a weight-edited checkpoint (HF layout: config.json, *.safetensors, tokenizer + processor
# files) to the Modal Volume holo-models as /ckpt/<name>, ready for HOLO_CKPT=<name> modal deploy osworld/modal_vllm.py.
# Token comes from /root/.modal_env (account 1, emilejouannet) or /root/.modal_env2 (account 2, martinbon39), both 600,
# written from orbit, never printed. Modal client in /workspace/modal-venv.
# Usage: bash modal_put_ckpt.sh <ckpt_dir> <name> [1|2]   (default 2: the astra-free edits go to account 2)
set -euo pipefail
DIR="$1"; NAME="$2"; ACCOUNT="${3:-2}"
for f in config.json tokenizer_config.json tokenizer.json preprocessor_config.json chat_template.jinja; do
  [ -f "$DIR/$f" ] || { echo "missing $DIR/$f (copy every non-weight file of the base snapshot)"; exit 1; }
done
if [ "$ACCOUNT" = 1 ]; then source /root/.modal_env; else source /root/.modal_env2; fi
t=$(date +%s)
/workspace/modal-venv/bin/modal volume put --force holo-models "$DIR" "/ckpt/$NAME"
echo "uploaded $(du -sh "$DIR" | cut -f1) in $(( $(date +%s) - t ))s -> holo-models:/ckpt/$NAME"
/workspace/modal-venv/bin/modal volume ls holo-models "/ckpt/$NAME"
