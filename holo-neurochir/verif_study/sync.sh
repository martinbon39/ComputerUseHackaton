#!/usr/bin/env bash
set -euo pipefail
study_dir=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)
remote="${POD_HOST:?set POD_HOST=user@host of the GPU pod}:/workspace/astra/verif-study/"
transport="${POD_SSH:?set POD_SSH to the ssh command with key and port} -o BatchMode=yes"
case "${1:-}" in
  to-pod) rsync -rt --exclude __pycache__ --exclude responses.jsonl --exclude attempts.jsonl --exclude '*.log' -e "$transport" "$study_dir/" "$remote" ;;
  from-pod) rsync -rt --include /responses.jsonl --include /attempts.jsonl --include '/*.log' --exclude '*' -e "$transport" "$remote" "$study_dir/" ;;
  *) echo 'usage: sync.sh to-pod|from-pod' >&2; exit 2 ;;
esac
