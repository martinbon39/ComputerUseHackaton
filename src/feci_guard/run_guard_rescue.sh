#!/usr/bin/env bash
# Local run of run_holo_guard_rescue.py: run_osw.sh's environment, Claude judge through the local CLI, rescue model
# Holo4-27B on Modal. The Modal key is read inside the login from ~/.holo_modal_key into MODAL_KEY, never printed.
# Usage: run_guard_rescue.sh <result_dir> <test_meta> <workers> [extra run_holo args]
RES="$1"; META="$2"; W="$3"; shift 3
G="$(cd "$(dirname "$0")" && pwd)"
R_URL="${RESCUE_BASE_URL:-https://martinbon39--holo-judge-serve.us-east.modal.run/v1}"; R_MODEL="${RESCUE_MODEL:-Holo4-27B}"
exec ~/osw/osh "cd ~/osw/rtg/Env/OSWorld && export DOCKER_HOST=unix:///var/run/docker.sock OSWORLD_FORCE_KVM=1 OSW_MEM_LIMIT=5g OSW_NETWORK_SH=$HOME/osw/network_nft.sh no_proxy=localhost,127.0.0.1 NO_PROXY=localhost,127.0.0.1 GUARD_BACKEND=claude RESCUE_BASE_URL=$R_URL RESCUE_MODEL=$R_MODEL RESCUE_API_KEY_ENV=MODAL_KEY && export MODAL_KEY=\$(cat ~/.holo_modal_key) && ~/osw/venv/bin/python $G/run_holo_guard_rescue.py --base_url http://127.0.0.1:8000/v1 --model Holo-3.1-4B --result_dir $RES --test_meta $META --workers $W --max_steps 50 --no_recording $* 2>&1 | tee -a $RES.log"
