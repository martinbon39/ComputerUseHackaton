#!/usr/bin/env bash
# On orbit: wait until holo-models:/ckpt/<ckpt> on account <1|2> is complete (config, tokenizer, safetensors; listing
# unchanged over 60 s) and the optional --after file exists, then deploy it as Holo-3.1-4B-<ckpt> (modal_deploy.sh),
# wait for /v1/models, run the 3-request smoke with full outputs (modal_probe.py --out; skipped for astra-free's
# free_* checkpoints, which get read-only checks only), commit manifest + smoke, and report to ares.
# --skip-if <ckpt2>: give up if <ckpt2> got deployed on this account first (queue order).
# Usage: bash osworld/modal_serve_when_ready.sh <1|2> <ckpt> [--after <file>] [--skip-if <ckpt2>]
set -uo pipefail
cd "$(dirname "$0")/.."
ACCOUNT="$1"; CKPT="$2"; shift 2; AFTER=""; SKIP=""
while [ $# -gt 0 ]; do case "$1" in --after) AFTER="$2"; shift 2 ;; --skip-if) SKIP="$2"; shift 2 ;; *) exit 2 ;; esac; done
case "$ACCOUNT" in 1) PROFILE=emilejouannet ;; 2) PROFILE=martinbon39 ;; *) exit 2 ;; esac
NAME="Holo-3.1-4B-$CKPT"; URL="https://$PROFILE--holo-vllm-serve.us-east.modal.run/v1"
TASK=/home/orbit/osw/results_diag/pyautogui/screenshot/Holo-3.1-4B/chrome/fc6d8143-9452-4171-9459-7f515143419a
START=$(date -u +%Y%m%dT%H%M%S)
skipped() { [ -n "$SKIP" ] && ls osworld/modal_deploys/*_acct${ACCOUNT}_Holo-3.1-4B-${SKIP}.json 2>/dev/null |
  awk -F/ '{print $NF}' | awk -v s="$START" '$0 > s' | grep -q .; }
prev=""
for i in $(seq 1 480); do
  skipped && { echo "$(date -u +%T) $SKIP was deployed first on account $ACCOUNT: $CKPT waits for ares"; exit 0; }
  cur=$(MODAL_PROFILE=$PROFILE modal volume ls holo-models "/ckpt/$CKPT" --json 2>/dev/null | python3 -c "
import sys, json
d = {x['filename'].split('/')[-1]: x['size'] for x in json.load(sys.stdin)}
ok = 'config.json' in d and 'tokenizer.json' in d and any(k.endswith('.safetensors') for k in d)
print(sorted(d.items()) if ok else '')" 2>/dev/null)
  [ -n "$cur" ] && [ "$cur" = "$prev" ] && break
  prev="$cur"; sleep 60
done
[ -n "$cur" ] && [ "$cur" = "$prev" ] || { echo "$CKPT never completed on account $ACCOUNT"; exit 1; }
echo "$(date -u +%T) $CKPT complete on account $ACCOUNT"
if [ -n "$AFTER" ]; then until [ -e "$AFTER" ]; do sleep 15; done; echo "$(date -u +%T) $AFTER exists"; fi
skipped && { echo "$(date -u +%T) $SKIP was deployed first on account $ACCOUNT: $CKPT waits for ares"; exit 0; }
MANIFEST=$(bash osworld/modal_deploy.sh "$ACCOUNT" "$NAME" "$CKPT" | grep "modal_deploys/") || { echo "deploy failed"; exit 1; }
echo "$(date -u +%T) deployed $MANIFEST"
t=$(date +%s)
until curl -s --max-time 30 "$URL/models" -H "Authorization: Bearer $(cat ~/.holo_modal_key)" | grep -q "\"$NAME\""; do
  [ $(( $(date +%s) - t )) -gt 1800 ] && { argos send ares "modal-serve: $NAME pas prêt après 30 min sur le compte $ACCOUNT"; exit 1; }
  sleep 10
done
READY=$(( $(date +%s) - t ))
SMOKE="${MANIFEST%.json}.smoke.json"
if [[ "$CKPT" == free_* ]]; then
  SUMMARY="pas de smoke génératif (règle astra-free), /v1/models OK"
else
  PYTHONPATH=.:osworld ~/osw/venv/bin/python osworld/modal_probe.py "$URL" "$TASK" --model "$NAME" --out "$SMOKE" >/dev/null 2>&1
  SUMMARY=$(python3 - "$SMOKE" <<'EOF'
import json, sys
try:
    d = json.load(open(sys.argv[1]))
except Exception as e:
    print(f"smoke ÉCHOUÉ ({e})"); sys.exit()
parts = [f"{r['req']} {r['latency_s']}s {r['completion_tokens']}tok {r['finish']}" for r in d["requests"]]
t0 = d["requests"][0]["content"].replace("\n", " ")[:160]
print("; ".join(parts) + f"; outil OSWorld={d['sampled_tool']} (enregistré {d['recorded_tool']}); T=0: « {t0} »")
EOF
)
fi
git add "$MANIFEST" $( [ -f "$SMOKE" ] && echo "$SMOKE" ) && git commit -q -m "holo-neurochir: Modal deploy of $NAME on account $ACCOUNT (manifest + smoke)

Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>" -- osworld/modal_deploys/ && git push -q origin main
argos send ares "modal-serve: $NAME prêt sur le compte $ACCOUNT, $URL (Bearer ~/.holo_modal_key), prêt en ${READY}s. Smoke : $SUMMARY. Manifeste et sorties complètes : $MANIFEST (+ .smoke.json), poussés."
echo "$(date -u +%T) done: $SUMMARY"
