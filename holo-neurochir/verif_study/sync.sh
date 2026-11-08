#!/usr/bin/env bash
set -euo pipefail
study_dir=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)
remote='root@213.181.111.151:/workspace/astra/verif-study/'
transport='ssh -i /home/orbit/.ssh/runpod_holo -p 15780 -o BatchMode=yes'
case "${1:-}" in
  to-pod) rsync -rt --exclude __pycache__ --exclude responses.jsonl --exclude attempts.jsonl --exclude '*.log' -e "$transport" "$study_dir/" "$remote" ;;
  from-pod) rsync -rt --include /responses.jsonl --include /attempts.jsonl --include '/*.log' --exclude '*' -e "$transport" "$remote" "$study_dir/" ;;
  *) echo 'usage: sync.sh to-pod|from-pod' >&2; exit 2 ;;
esac
