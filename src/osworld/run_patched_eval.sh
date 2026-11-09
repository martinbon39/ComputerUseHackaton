#!/usr/bin/env bash
# Online validation arms on orbit, same harness and task list, <workers> VMs each, one tmux window per arm:
#   orig     original 4B, production vLLM :8000, prompt v2
#   patched  patched 4B, vLLM pod :8011 seen as orbit :8001 (tmux osw_tunnel2), prompt v2
#   prompt   original 4B on :8000 with prompt v2_verify (run_holo_verify.py; prompt baseline, AxBench-style)
# Lists: confirm = val_confirm_tasks.json (never used to build an intervention); fs_insample = secondary, in-sample;
# test = split_test.json (passed to run_holo as --test_meta only, never opened here).
# PATCHED_URL / PATCHED_NAME override the patched server (default orbit :8001 = pod :8011).
# Results ~/osw/results_val_<arm>_<tag>/, tmux osw_val_<tag>:<arm>. Before EACH arm: running VMs + workers <= 6 and
# >= 14 G available (override with MAX_VMS / MIN_AVAIL_G when ares sets another cap), else refuse (or with WAIT=1
# retry every 5 min, up to 6 h).
# Then: PYTHONPATH=. ~/osw/venv/bin/python osworld/compare_val.py --origin stuck|other \
#         patched=~/osw/results_val_patched_<tag> prompt=~/osw/results_val_prompt_<tag> orig=~/osw/results_val_orig_<tag>
# RESUME=1: an arm whose results dir exists continues it (run_holo skips tasks that already have result.txt).
# DRY_RUN=1: full checks, prints the commands, launches nothing (use it to test this script: a passing preflight
# otherwise starts VMs for real).
# Usage: [ARMS="orig patched"] [WAIT=1] [RESUME=1] [DRY_RUN=1] bash osworld/run_patched_eval.sh <tag> <confirm|fs_insample> [workers=3]
#        [extra run_holo args, all arms]
set -euo pipefail
TAG="${1:?usage: run_patched_eval.sh <tag> <confirm|fs_insample> [workers=3] [run_holo args]}"
LIST="${2:?list: confirm | fs_insample}"; W="${3:-3}"; shift $(( $# < 3 ? $# : 3 ))
[[ "$W" =~ ^[1-9]$ ]] || { echo "workers must be 1-9, got $W" >&2; exit 1; }
ARMS="${ARMS:-orig patched}"; WAIT="${WAIT:-0}"; DRY_RUN="${DRY_RUN:-0}"; RESUME="${RESUME:-0}"
HERE="$(cd "$(dirname "$0")" && pwd)"
if [ "$LIST" = test ]; then TASKS="$HERE/split_test.json"; else TASKS="$HERE/val_${LIST}_tasks.json"; fi
[ -f "$TASKS" ] || { echo "no $TASKS" >&2; exit 1; }
MAX_VMS="${MAX_VMS:-6}"; MIN_AVAIL_G="${MIN_AVAIL_G:-14}"
PATCHED_URL="${PATCHED_URL:-http://127.0.0.1:8001/v1}"; PATCHED_NAME="${PATCHED_NAME:-Holo-3.1-4B-patched}"
META=~/osw/val_$TAG.json

for arm in $ARMS; do
  case $arm in orig|patched|prompt) ;; *) echo "unknown arm $arm" >&2; exit 1;; esac
  [ "$RESUME" = 1 ] || [ ! -e ~/osw/results_val_${arm}_$TAG ] || { echo "~/osw/results_val_${arm}_$TAG exists: pick a new tag or RESUME=1" >&2; exit 1; }
done
if [ -e "$META" ]; then cmp -s "$TASKS" "$META" || { echo "$META differs from $TASKS: arms must share the list" >&2; exit 1; }
elif [ "$DRY_RUN" != 1 ]; then cp "$TASKS" "$META"; fi
echo "task list: $META"
if [[ " $ARMS " == *" patched "* ]]; then
  curl -sf "$PATCHED_URL/models" | grep -q "\"$PATCHED_NAME\"" || { echo "no $PATCHED_NAME on $PATCHED_URL: start it before any arm" >&2; exit 1; }
fi

preflight() {  # $1 = arm
  if [ "$1" = patched ]; then
    curl -sf "$PATCHED_URL/models" | grep -q "\"$PATCHED_NAME\"" || { echo "no $PATCHED_NAME on $PATCHED_URL"; return 1; }
  fi
  curl -sf -m 10 http://127.0.0.1:8000/v1/models | grep -q '"Holo-3.1-4B"' || { echo "production vLLM :8000 unreachable"; return 1; }
  local vms avail
  vms=$(~/osw/osh "docker ps -q --filter ancestor=happysixd/osworld-docker" | wc -l)
  avail=$(free -g | awk '/^Mem:/ {print $7}')
  [ $((vms + W)) -le $MAX_VMS ] && [ "$avail" -ge $MIN_AVAIL_G ] || { echo "$vms VMs + $W > $MAX_VMS or ${avail}G < ${MIN_AVAIL_G}G"; return 1; }
}

launch() {  # $1 = arm
  local arm=$1 res=~/osw/results_val_$1_$TAG cmd; shift
  case $arm in
    orig)    cmd="bash ~/osw/run_osw.sh $res $META $W --no_recording $*" ;;
    patched) cmd="bash ~/osw/run_osw.sh $res $META $W --base_url $PATCHED_URL --model $PATCHED_NAME --no_recording $*" ;;
    prompt)  local runner=~/osw/run_osw_verify.sh
             sed "s|holo_repro/run_holo.py|$HERE/run_holo_verify.py|" ~/osw/run_osw.sh > "$runner.new"
             [ "$(grep -c run_holo_verify.py "$runner.new")" = 1 ] || { echo "run_osw.sh layout changed" >&2; exit 1; }
             mv "$runner.new" "$runner"
             cmd="bash $runner $res $META $W --prompt v2_verify --no_recording $*" ;;
  esac
  local done_tag; done_tag="$(echo "$arm" | tr a-z A-Z)_EXIT"
  if [ "$DRY_RUN" = 1 ]; then echo "DRY_RUN $arm: $cmd"; return; fi
  if tmux has-session -t "osw_val_$TAG" 2>/dev/null; then
    tmux new-window -t "osw_val_$TAG" -n "$arm" "$cmd; echo $done_tag; exec bash"
  else
    tmux new-session -d -s "osw_val_$TAG" -n "$arm" "$cmd; echo $done_tag; exec bash"
  fi
  echo "$(date -u +%H:%M) launched $arm -> $res (tmux osw_val_$TAG:$arm)"
  sleep 90  # let this arm's VMs start before the next preflight counts them
}

for arm in $ARMS; do
  tries=0
  until why=$(preflight "$arm"); do
    [ "$WAIT" = 1 ] && [ $tries -lt 72 ] || { echo "refused $arm: $why" >&2; exit 1; }
    tries=$((tries + 1)); echo "$(date -u +%H:%M) waiting for $arm: $why"; sleep 300
  done
  launch "$arm" "$@"
done
