#!/usr/bin/env bash
# On the GPU pod: run one research job on a Modal H100 (app holo-slot, osworld/modal_slot.py) and bring its output back.
# Uploads <job_dir> (scripts, data, contexts; use paths relative to it) and the pod's /workspace/projet/holo, runs
# <command> there with cwd=<job_dir copy>, PYTHONPATH=<code>:<job dir>, HF_HOME=Holo-3.1-4B cache, OUT_DIR=<output dir>,
# then downloads OUT_DIR to <job_dir>/modal_out/ (with modal_log.txt and modal_exit_code). Returns the job's exit code.
# Refuses while the same account serves holo-vllm on its GPU (one H100 per account), unless MODAL_SLOT_FORCE=1.
# Usage: bash /workspace/modal_run_job.sh <job_dir> "<command>" [1|2]     (account 2 by default)
set -euo pipefail
DIR="$(realpath "$1")"; CMD="$2"; ACCOUNT="${3:-2}"
if [ "$ACCOUNT" = 1 ]; then source /root/.modal_env; else source /root/.modal_env2; fi
M=/workspace/modal-venv/bin/modal; PY=/workspace/modal-venv/bin/python
JOB="$(basename "$DIR")-$(date +%Y%m%d-%H%M%S)"
if [ "${MODAL_SLOT_FORCE:-0}" != 1 ] && $M container list --json 2>/dev/null | grep -q '"app_name": "holo-vllm"'; then
  echo "account $ACCOUNT is serving holo-vllm on its H100; wait for it to scale down or MODAL_SLOT_FORCE=1"; exit 3
fi
t0=$(date +%s)
$M volume put --force holo-slot /workspace/projet/holo /code/holo >/dev/null
$M volume put --force holo-slot "$DIR" "/jobs/$JOB/in" >/dev/null
echo "uploaded $(du -sh "$DIR" | cut -f1) in $(( $(date +%s) - t0 ))s as $JOB (account $ACCOUNT)"
t1=$(date +%s)
set +e
$PY -c "import modal, sys; sys.exit(modal.Function.from_name('holo-slot', 'run_job').remote(sys.argv[1], sys.argv[2]))" \
  "$JOB" "$CMD"
RC=$?
set -e
echo "ran in $(( $(date +%s) - t1 ))s (H100 billed ~ this plus the container start), exit $RC"
rm -rf "$DIR/modal_out"; TMP=$(mktemp -d)
$M volume get holo-slot "/jobs/$JOB/out" "$TMP/" >/dev/null
mv "$TMP/out" "$DIR/modal_out"; rmdir "$TMP"
echo "output: $DIR/modal_out ; log tail:"; tail -5 "$DIR/modal_out/modal_log.txt" || true
exit $RC
