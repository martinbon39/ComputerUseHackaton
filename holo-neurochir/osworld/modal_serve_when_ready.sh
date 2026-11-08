#!/usr/bin/env bash
# On orbit: serve a checkpoint on the first FREE Modal account of a preference list, as soon as its upload is complete.
# 1. Wait until holo-models:/ckpt/<ckpt> on the source account (first in the list) is complete (config, tokenizer,
#    safetensors; listing unchanged over 60 s).
# 2. Wait until one account of the list is free, i.e. its lock ~/modal_queue/busy_acct<n> can be taken (mkdir, atomic).
#    A lock means "a model is served there and may be under measurement": it is released ONLY by hand, on ares' signal
#    "<model> mesuré" (rmdir ~/modal_queue/busy_acct<n>). Nothing ever replaces a model under measurement.
# 3. If the free account is not the source, upload the checkpoint there from the pod's /dev/shm/<ckpt>.
# 4. Deploy as Holo-3.1-4B-<ckpt> (modal_deploy.sh), wait for /v1/models, run the 3-request smoke with full outputs
#    (modal_probe.py --out; none for astra-free's free_* checkpoints), commit manifest + smoke, report to ares.
#    While waiting, a lower <prio> number goes first: a ready job never takes an account that a ready job of better
#    priority is also waiting for (markers ~/modal_queue/ready_acct<n>_p<prio>_<ckpt>).
# Usage: bash osworld/modal_serve_when_ready.sh <ckpt> <accounts, e.g. 2,1> [prio per account, e.g. 0,4; default 5]
set -uo pipefail
cd "$(dirname "$0")/.."
CKPT="$1"; IFS=, read -ra ACCOUNTS <<< "$2"; IFS=, read -ra PRIOS <<< "${3:-5}"
prio_of() { local i; for i in "${!ACCOUNTS[@]}"; do [ "${ACCOUNTS[$i]}" = "$1" ] && echo "${PRIOS[$i]:-${PRIOS[0]}}"; done; }
LOCKS=~/modal_queue; mkdir -p "$LOCKS"
profile() { [ "$1" = 1 ] && echo emilejouannet || echo martinbon39; }
POD="${POD:?set POD to the ssh command of the GPU pod}"
NAME="Holo-3.1-4B-$CKPT"
TASK=/home/orbit/osw/results_diag/pyautogui/screenshot/Holo-3.1-4B/chrome/fc6d8143-9452-4171-9459-7f515143419a
SRC=$(profile "${ACCOUNTS[0]}")
prev=""
for i in $(seq 1 480); do
  cur=$(MODAL_PROFILE=$SRC modal volume ls holo-models "/ckpt/$CKPT" --json 2>/dev/null | python3 -c "
import sys, json
d = {x['filename'].split('/')[-1]: x['size'] for x in json.load(sys.stdin)}
ok = 'config.json' in d and 'tokenizer.json' in d and any(k.endswith('.safetensors') for k in d)
print(sorted(d.items()) if ok else '')" 2>/dev/null)
  [ -n "$cur" ] && [ "$cur" = "$prev" ] && break
  prev="$cur"; sleep 60
done
[ -n "$cur" ] && [ "$cur" = "$prev" ] || { echo "$CKPT never completed on account ${ACCOUNTS[0]}"; exit 1; }
echo "$(date -u +%T) $CKPT complete on account ${ACCOUNTS[0]}"
ACCOUNT=""
for a in "${ACCOUNTS[@]}"; do touch "$LOCKS/ready_acct${a}_p$(prio_of "$a")_$CKPT"; done
outranked() { ls "$LOCKS" | grep -E "^ready_acct$1_p[0-9]+_" | grep -v "_$CKPT\$" |
  sed -E 's/^ready_acct[0-9]+_p([0-9]+)_.*/\1/' | awk -v p="$(prio_of "$1")" '$1 < p' | grep -q .; }
until [ -n "$ACCOUNT" ]; do
  for a in "${ACCOUNTS[@]}"; do
    outranked "$a" && continue
    mkdir "$LOCKS/busy_acct$a" 2>/dev/null && { ACCOUNT=$a; break; }
  done
  [ -z "$ACCOUNT" ] && sleep 30
done
rm -f "$LOCKS"/ready_acct*_p*_"$CKPT"
echo "$NAME $(date -u +%FT%TZ)" > "$LOCKS/busy_acct$ACCOUNT/holder"
echo "$(date -u +%T) took account $ACCOUNT"
PROFILE=$(profile "$ACCOUNT"); URL="https://$PROFILE--holo-vllm-serve.us-east.modal.run/v1"
listing() { MODAL_PROFILE=$1 modal volume ls holo-models "/ckpt/$CKPT" --json 2>/dev/null | python3 -c "
import sys, json; print(sorted((x['filename'].split('/')[-1], x['size']) for x in json.load(sys.stdin)))" 2>/dev/null; }
if [ "$ACCOUNT" != "${ACCOUNTS[0]}" ] && [ "$(listing "$PROFILE")" != "$(listing "$SRC")" ]; then
  $POD "bash /workspace/modal_put_ckpt.sh /dev/shm/$CKPT $CKPT $ACCOUNT" 2>&1 | grep -aE "uploaded|missing|rror" ||
    { argos send ares "modal-serve: $CKPT absent de /dev/shm du pod, impossible de le servir sur le compte $ACCOUNT"; exit 1; }
fi
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
argos send ares "modal-serve: $NAME prêt sur le compte $ACCOUNT, $URL (Bearer ~/.holo_modal_key), prêt en ${READY}s. Smoke : $SUMMARY. Manifeste et sorties complètes : $MANIFEST (+ .smoke.json), poussés. Compte $ACCOUNT verrouillé jusqu'à ton signal « $CKPT mesuré »."
echo "$(date -u +%T) done: $SUMMARY"
