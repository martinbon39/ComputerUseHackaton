#!/usr/bin/env bash
# Online validation of a patched Holo-3.1-4B on orbit: patched arm (vLLM pod :8011 seen as orbit :8001 via tmux
# osw_tunnel2) and, mirrored, the original arm (production vLLM :8000) on the same task list, <workers> each.
# Lists: confirm = val_confirm_tasks.json (main, never used to build an intervention); fs_insample = secondary, in-sample.
# Results: ~/osw/results_val_patched_<tag>/ and ~/osw/results_val_orig_<tag>/; tmux osw_val_<tag>.
# Then: PYTHONPATH=. ~/osw/venv/bin/python osworld/compare_val.py ~/osw/results_val_patched_<tag> ~/osw/results_val_orig_<tag>
# Usage: bash osworld/run_patched_eval.sh <tag> <confirm|fs_insample> [workers=3] [extra run_holo args, both arms]
set -euo pipefail
TAG="${1:?usage: run_patched_eval.sh <tag> <confirm|fs_insample> [workers=3] [run_holo args]}"
LIST="${2:?list: confirm | fs_insample}"; W="${3:-3}"; shift $(( $# < 3 ? $# : 3 ))
[[ "$W" =~ ^[1-9]$ ]] || { echo "workers must be 1-9, got $W" >&2; exit 1; }
HERE="$(cd "$(dirname "$0")" && pwd)"
TASKS="$HERE/val_${LIST}_tasks.json"; [ -f "$TASKS" ] || { echo "no $TASKS" >&2; exit 1; }
MAX_VMS=6; MIN_AVAIL_G=14
PATCHED_URL=http://127.0.0.1:8001/v1; PATCHED_NAME=Holo-3.1-4B-patched
RES_P=~/osw/results_val_patched_$TAG; RES_O=~/osw/results_val_orig_$TAG; META=~/osw/val_$TAG.json

for d in "$RES_P" "$RES_O"; do [ ! -e "$d" ] || { echo "$d exists: pick a new tag" >&2; exit 1; }; done
curl -sf "$PATCHED_URL/models" | grep -q "\"$PATCHED_NAME\"" || { echo "no $PATCHED_NAME on :8001 (serve_patched.sh + tmux osw_tunnel2?)" >&2; exit 1; }
curl -sf http://127.0.0.1:8000/v1/models | grep -q '"Holo-3.1-4B"' || { echo "production vLLM :8000 unreachable" >&2; exit 1; }
VMS=$(~/osw/osh "docker ps -q --filter ancestor=happysixd/osworld-docker" | wc -l)
AVAIL=$(free -g | awk '/^Mem:/ {print $7}')
if [ $((VMS + 2 * W)) -gt $MAX_VMS ] || [ "$AVAIL" -lt $MIN_AVAIL_G ]; then
  echo "refused: $VMS VMs running + $((2 * W)) > $MAX_VMS, or ${AVAIL}G available < ${MIN_AVAIL_G}G" >&2; exit 1
fi

cp "$TASKS" "$META"; echo "frozen task list: $META <- $TASKS"

tmux new-session -d -s "osw_val_$TAG" -n patched \
  "bash ~/osw/run_osw.sh $RES_P $META $W --base_url $PATCHED_URL --model $PATCHED_NAME --no_recording $*; echo PATCHED_EXIT; exec bash"
tmux new-window -t "osw_val_$TAG" -n orig \
  "bash ~/osw/run_osw.sh $RES_O $META $W --no_recording $*; echo ORIG_EXIT; exec bash"
echo "tmux osw_val_$TAG (windows patched, orig) -> $RES_P , $RES_O"
