#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
printf -v RESCUE_ARGS '%q ' "$@"
printf -v RESCUE_RUNNER '%q' "$ROOT/feci_guard/rescue_runner.py"
exec "$HOME/osw/osh" "cd ~/osw/rtg/Env/OSWorld && export DOCKER_HOST=unix:///var/run/docker.sock OSWORLD_FORCE_KVM=1 OSW_MEM_LIMIT=5g OSW_NETWORK_SH=\$HOME/osw/network_nft.sh no_proxy=localhost,127.0.0.1 NO_PROXY=localhost,127.0.0.1 && ~/osw/venv/bin/python $RESCUE_RUNNER $RESCUE_ARGS"
