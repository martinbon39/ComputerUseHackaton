#!/usr/bin/env bash
# On orbit: deploy osworld/modal_vllm.py on one Modal account and record osworld/modal_deploys/<utc>_acct<n>_<name>.json
# (checkpoint, served name, commit of modal_vllm.py, effective vllm options, GPU, account, time), for online-eval.
# Usage: bash osworld/modal_deploy.sh <1|2> <served_name> [ckpt_subdir]     (no ckpt = original Hcompany/Holo-3.1-4B)
set -euo pipefail
cd "$(dirname "$0")/.."
ACCOUNT="$1"; NAME="$2"; CKPT="${3:-}"
case "$ACCOUNT" in 1) PROFILE=emilejouannet ;; 2) PROFILE=martinbon39 ;; *) echo "account must be 1 or 2"; exit 2 ;; esac
git diff --quiet -- osworld/modal_vllm.py || { echo "osworld/modal_vllm.py has uncommitted changes: commit it first"; exit 2; }
COMMIT=$(git log -1 --format=%h -- osworld/modal_vllm.py)
MODAL_PROFILE=$PROFILE HOLO_CKPT="$CKPT" HOLO_NAME="$NAME" modal deploy osworld/modal_vllm.py | grep -aE "deployed|rror"
TS=$(date -u +%Y-%m-%dT%H:%M:%SZ)
mkdir -p osworld/modal_deploys
OUT="osworld/modal_deploys/$(date -u +%Y%m%dT%H%M%S)_acct${ACCOUNT}_${NAME}.json"
MPY=$(head -1 "$(command -v modal)" | sed 's/^#!//')
PYTHONPATH=osworld "$MPY" - "$OUT" "$ACCOUNT" "$PROFILE" "$NAME" "$CKPT" "$COMMIT" "$TS" <<'EOF'
import json, sys
from importlib.metadata import version
import modal_vllm as mv
out, account, profile, name, ckpt, commit, ts = sys.argv[1:]
json.dump({
    "deployed_at_utc": ts, "account": int(account), "modal_profile": profile, "app": "holo-vllm",
    "url": f"https://{profile}--holo-vllm-serve.us-east.modal.run/v1", "served_model_name": name,
    "checkpoint": f"holo-models:/ckpt/{ckpt}" if ckpt else f"{mv.HF_ID}@{mv.HF_REV}",
    "modal_vllm_py_commit": commit, "gpu": "1x NVIDIA H100 80GB (Modal gpu=H100, max_containers=1)",
    "image": "see osworld/MODAL_MANIFEST.md (nvidia/cuda:12.8.1-devel-ubuntu24.04, py3.12, vllm 0.23.0)",
    "vllm_args": mv.VLLM_ARGS + ["--api-key", "***"], "modal_client": version("modal"),
}, open(out, "w"), indent=1)
print(out)
EOF
