#!/usr/bin/env bash
# Load watch of the served models (orbit side, through the tunnels): every minute, vLLM /metrics of each server ->
# running / waiting requests, KV cache use, mean end-to-end latency over the last minute. Logs to ~/osw/server_load.log
# and alerts <agent> (argos send, at most once per 30 min per server) when a server queues requests for 3 minutes,
# runs at its max-num-seqs, uses > 85 % KV, or its minute latency exceeds 2.5x its first-15-minute baseline.
# Usage: bash osworld/watch_servers.sh [agent=ares] [deadline=09:00]   servers: 8000 (max 64 seqs), 8001 (pod 8011, 16)
set -uo pipefail
AGENT="${1:-ares}"; DEADLINE="${2:-09:00}"
end_s=$(date -u -d "$DEADLINE" +%s); [ "$end_s" -gt "$(date +%s)" ] || end_s=$(date -u -d "tomorrow $DEADLINE" +%s)
declare -A MAXSEQ=([8000]=64 [8001]=16) LS LC BASE NB QUEUED LAST_ALERT
start=$(date +%s)
metric() { echo "$1" | awk -v k="$2" '$1 ~ "^"k"({|$)" {s += $NF} END {print s + 0}'; }
while [ "$(date +%s)" -lt "$end_s" ]; do
  for p in 8000 8001; do
    m=$(curl -s -m 10 "127.0.0.1:$p/metrics") || { echo "$(date -u +%H:%M) $p metrics unreachable" >> ~/osw/server_load.log; continue; }
    run=$(metric "$m" vllm:num_requests_running); wait=$(metric "$m" vllm:num_requests_waiting)
    kv=$(metric "$m" vllm:kv_cache_usage_perc)
    s=$(metric "$m" vllm:e2e_request_latency_seconds_sum); c=$(metric "$m" vllm:e2e_request_latency_seconds_count)
    lat=$(awk -v s="$s" -v c="$c" -v ls="${LS[$p]:-$s}" -v lc="${LC[$p]:-$c}" 'BEGIN {d = c - lc; print (d > 0) ? (s - ls) / d : -1}')
    LS[$p]=$s; LC[$p]=$c
    if [ $(( $(date +%s) - start )) -lt 900 ] && awk -v l="$lat" 'BEGIN {exit !(l > 0)}'; then
      BASE[$p]=$(awk -v b="${BASE[$p]:-0}" -v n="${NB[$p]:-0}" -v l="$lat" 'BEGIN {print (b * n + l) / (n + 1)}'); NB[$p]=$(( ${NB[$p]:-0} + 1 ))
    fi
    QUEUED[$p]=$(awk -v w="$wait" -v q="${QUEUED[$p]:-0}" 'BEGIN {print (w > 0) ? q + 1 : 0}')
    line="$(date -u +%H:%M) $p running=$run waiting=$wait kv=$(awk -v k="$kv" 'BEGIN {printf "%.2f", k}') lat_1min=$(awk -v l="$lat" 'BEGIN {printf "%.1f", l}')s base=${BASE[$p]:-?}"
    echo "$line" >> ~/osw/server_load.log
    why=""
    [ "${QUEUED[$p]}" -ge 3 ] && why+="requests queued for 3 min; "
    awk -v r="$run" -v m="${MAXSEQ[$p]}" 'BEGIN {exit !(r >= m)}' && why+="running at max-num-seqs ${MAXSEQ[$p]}; "
    awk -v k="$kv" 'BEGIN {exit !(k > 0.85)}' && why+="KV > 85 %; "
    [ -n "${BASE[$p]:-}" ] && [ $(( $(date +%s) - start )) -ge 900 ] && \
      awk -v l="$lat" -v b="${BASE[$p]}" 'BEGIN {exit !(l > 2.5 * b)}' && why+="minute latency > 2.5x baseline; "
    if [ -n "$why" ] && [ $(( $(date +%s) - ${LAST_ALERT[$p]:-0} )) -ge 1800 ]; then
      argos send "$AGENT" "online-eval servers: :$p SATURATION? ${why%; } — $line (log ~/osw/server_load.log)"
      LAST_ALERT[$p]=$(date +%s)
    fi
  done
  sleep 60
done
