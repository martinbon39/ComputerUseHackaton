#!/usr/bin/env bash
# Feci Guard online run: same login, env and arguments as ~/osw/run_osw.sh (the original runs), but the guarded copy
# of run_holo. Usage: run_guard.sh <result_dir> <test_meta> <workers> [extra run_holo args, e.g. --guard off]
RES="$1"; META="$2"; W="$3"; shift 3
G="$(cd "$(dirname "$0")" && pwd)"
exec ~/osw/osh "cd ~/osw/rtg/Env/OSWorld && export DOCKER_HOST=unix:///var/run/docker.sock OSWORLD_FORCE_KVM=1 OSW_MEM_LIMIT=5g OSW_NETWORK_SH=$HOME/osw/network_nft.sh no_proxy=localhost,127.0.0.1 NO_PROXY=localhost,127.0.0.1 && ~/osw/venv/bin/python $G/run_holo_guard.py --base_url http://127.0.0.1:8000/v1 --model Holo-3.1-4B --result_dir $RES --test_meta $META --workers $W --max_steps 50 --no_recording $* 2>&1 | tee -a $RES.log"
