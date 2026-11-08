#!/usr/bin/env bash
# Judging window of the public jury endpoint holo-jury-probe (on orbit, only on ares' order).
#   up <minutes>  refuse if the projected spend (2 H100 for <minutes> + 15) would pass 24 $ on an account; deploy the
#                 original (account 1) and merge_cua_b050 (account 2), wait for both, open the gate, run one rehearsal
#                 probe, then keep both warm (GET /v1/models every 4 min) and run `down` by itself after <minutes>.
#   down          close the gate, stop holo-vllm on both accounts, mark the account locks CLOSED.
#   check <minutes>  only the budget projection of `up`, starts nothing.
# Usage: bash osworld/modal_jury_window.sh check 90 | up 90 --go | down     (up without --go starts nothing)
set -uo pipefail
cd "$(dirname "$0")/.."
JURY=https://martinbon39--holo-jury-probe-web.us-east.modal.run
LOG=~/modal_queue/jury_window.log
HDR=~/.holo_modal_hdr  # "Authorization: Bearer <key>" (mode 600), read by curl -H @file so the key stays out of ps
models_ok() { curl -s --max-time 30 "https://$1--holo-vllm-serve.us-east.modal.run/v1/models" -H @"$HDR" | grep -q "\"$2\""; }
report() { MODAL_PROFILE=$1 timeout 90 modal billing report "${@:2}" --json 2>/dev/null |
           python3 -c "import sys,json; print(sum(float(r['cost']) for r in json.load(sys.stdin)))" 2>/dev/null; }

PIDF=~/modal_queue/jury_keepwarm.pid
down() {
  bash osworld/modal_jury_gate.sh close
  if [ -f "$PIDF" ]; then pid=$(cat "$PIDF"); rm -f "$PIDF"
    grep -q "jury-keepwarm" "/proc/$pid/cmdline" 2>/dev/null && kill "$pid"; fi
  for p in emilejouannet martinbon39; do MODAL_PROFILE=$p modal app stop holo-vllm -y >/dev/null 2>&1; done
  for a in 1 2; do mkdir -p ~/modal_queue/busy_acct$a; echo "CLOSED $(date -u +%FT%TZ) jury window over" > ~/modal_queue/busy_acct$a/holder; done
  echo "$(date -u +%T) window closed: gate closed, holo-vllm stopped on both accounts"
}

up() {
  local minutes="$1"
  [[ "$minutes" =~ ^[0-9]+$ ]] && [ "$minutes" -ge 10 ] && [ "$minutes" -le 180 ] || { echo "minutes must be 10..180"; exit 2; }
  [ -f "$HDR" ] || { echo "missing $HDR"; exit 2; }
  pgrep -f "modal_budget_guard.sh" >/dev/null || { echo "budget guard not running: start it first"; exit 2; }
  for p in emilejouannet martinbon39; do
    a=$(report "$p" --start 2026-11-01); b=$(report "$p" --for today)
    [ -n "$a" ] && [ -n "$b" ] || { echo "refused: billing of $p unreadable"; exit 2; }
    python3 -c "import sys; n=$a+$b; s=n + 4.1 * ($minutes + 15) / 60; print('$p: %.2f \$ now, ~%.2f \$ at the end' % (n, s)); sys.exit(s > 24)" ||
      { echo "refused: $p would pass 24 \$"; exit 2; }
  done
  [ "${CHECK_ONLY:-}" = 1 ] && { echo "check only: nothing started"; exit 0; }
  for a in 1 2; do mkdir -p ~/modal_queue/busy_acct$a; echo "JURY $(date -u +%FT%TZ) holo-jury-probe window ${minutes} min" > ~/modal_queue/busy_acct$a/holder; done
  M1=$(bash osworld/modal_deploy.sh 1 Holo-3.1-4B-modal-orig | grep "modal_deploys/") || { echo "deploy 1 failed"; down; exit 1; }
  M2=$(bash osworld/modal_deploy.sh 2 Holo-3.1-4B-merge_cua_b050 merge_cua_b050 | grep "modal_deploys/") || { echo "deploy 2 failed"; down; exit 1; }
  git add "$M1" "$M2" && git commit -q -m "holo-neurochir: Modal deploys for the jury window (modal-orig on 1, merge_cua_b050 on 2)

Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>
Co-authored-by: Emile Jouannet <123695416+Symbioose@users.noreply.github.com>" -- "$M1" "$M2" && git push -q origin main
  local t=$(date +%s)
  until models_ok emilejouannet Holo-3.1-4B-modal-orig && models_ok martinbon39 Holo-3.1-4B-merge_cua_b050; do
    [ $(( $(date +%s) - t )) -gt 1800 ] && { echo "not ready after 30 min"; down; exit 1; }
    sleep 10
  done
  echo "$(date -u +%T) both servers ready in $(( $(date +%s) - t )) s"
  bash osworld/modal_jury_gate.sh open
  curl -s --max-time 150 "$JURY/probe/ctx1_false_success_feasible" | python3 -c "
import sys, json
d = json.load(sys.stdin)
for k in ('original', 'merge'):
    r = d.get(k, {})
    print(k, r.get('tool'), r.get('error', ''), 'p_first=%s' % (r.get('tool_first_token') or {}).get('p'), r.get('latency_s'), 's')"
  local end=$(( $(date +%s) + minutes * 60 ))
  setsid nohup bash -c "
    : jury-keepwarm
    while [ \$(date +%s) -lt $end ]; do
      for u in emilejouannet martinbon39; do curl -s -o /dev/null --max-time 60 https://\$u--holo-vllm-serve.us-east.modal.run/v1/models -H @$HDR; done
      sleep 240
    done
    rm -f $PIDF
    bash osworld/modal_jury_window.sh down
    argos send ares 'modal-serve: fenêtre du jury terminée, porte fermée, holo-vllm arrêté sur les deux comptes.'
  " >> "$LOG" 2>&1 < /dev/null &
  echo $! > "$PIDF"
  echo "$(date -u +%T) window open until $(date -u -d @$end +%T) UTC (keep-warm + automatic down: $LOG)"
}

case "${1:-}" in
  check) CHECK_ONLY=1 up "${2:-}" ;;
  up) [ "${3:-}" = "--go" ] || { echo "up starts 2 H100: add --go (only on ares' order); use check to test"; exit 2; }; up "${2:-}" ;;
  down) down ;;
  *) echo "usage: up <minutes> | down"; exit 2 ;;
esac
