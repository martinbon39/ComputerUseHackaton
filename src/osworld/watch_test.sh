#!/usr/bin/env bash
# Wait for the GitHub test arms (~/osw/results_test_gh_{expo125,prompt,orig}) to fill, then run compare_test.sh and
# send the table to <agent>. Full = <n> scored tasks per arm; otherwise, after <quiet> min without a new result past
# <after> UTC, the report is sent as PARTIAL. Hard stop at <stop> UTC.
# Usage: bash osworld/watch_test.sh [agent=ares] [n=120] [after=01:45] [quiet=45] [stop=04:30]
set -uo pipefail
AGENT="${1:-ares}"; N="${2:-120}"; AFTER="${3:-01:45}"; QUIET="${4:-45}"; STOP="${5:-04:30}"
cd "$(dirname "$0")/.."
at() { local s; s=$(date -u -d "$1" +%s); [ "$s" -gt "$(date +%s)" ] || s=$(date -u -d "tomorrow $1" +%s); echo "$s"; }
after_s=$(at "$AFTER"); stop_s=$(at "$STOP")
counts() { for a in expo125 prompt orig; do echo -n "$a=$(find ~/osw/results_test_gh_$a -name result.txt 2>/dev/null | wc -l) "; done; }
last="" ; changed=$(date +%s)
while :; do
  c=$(counts); now=$(date +%s)
  [ "$c" != "$last" ] && { echo "$(date -u +%H:%M) $c"; last="$c"; changed=$now; }
  full=1; for x in $c; do [ "${x#*=}" -ge "$N" ] || full=0; done
  status=""
  [ $full = 1 ] && status="COMPLETE"
  [ -z "$status" ] && [ "$now" -ge "$after_s" ] && [ $(( now - changed )) -ge $(( QUIET * 60 )) ] && status="PARTIAL (no new result for $QUIET min)"
  [ -z "$status" ] && [ "$now" -ge "$stop_s" ] && status="PARTIAL (hard stop $STOP)"
  if [ -n "$status" ]; then
    out=$(bash osworld/compare_test.sh --out ~/osw/test_compare.json 2>&1 | grep -v Warn)
    echo "$out" > ~/osw/test_report_$(date -u +%H%M).txt
    argos send "$AGENT" "online-eval TEST $status — scored: $c
$out"
    echo "$(date -u +%H:%M) sent ($status)"; exit 0
  fi
  sleep 120
done
