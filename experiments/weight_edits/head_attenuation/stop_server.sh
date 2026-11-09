#!/usr/bin/env bash
set -euo pipefail
arm="${1:?arm required}"
[[ "$arm" =~ ^[a-zA-Z0-9_]+$ ]]
pid="$(cat "/workspace/astra/moon-leak/server_${arm}.pid")"
[[ "$pid" =~ ^[0-9]+$ ]]
if [[ ! -e "/proc/$pid/cmdline" ]]; then exit 0; fi
cmd="$(tr '\0' ' ' < "/proc/$pid/cmdline")"
[[ "$cmd" == *vllm.entrypoints.openai.api_server* ]]
[[ "$cmd" == *"moon_leak_${arm}"* ]]
kill -TERM "$pid"
for attempt in $(seq 1 30); do
  if [[ ! -e "/proc/$pid/cmdline" ]]; then exit 0; fi
  sleep 1
done
echo "Owned server PID $pid still exists after30seconds" >&2
exit 1
