#!/usr/bin/env bash
# Download the artifacts of a holo-osworld-runner workflow run and merge them into one results dir that
# compare_val.py reads as name=<dest> (<dest>/pyautogui/screenshot/<model>/<domain>/<id>/).
# Per-job logs and timing.json go to <dest>/_jobs/<artifact>/.
# NO_PNG=1: keep everything but the screenshots and report.html, which embeds them (they stay in the GitHub artifacts).
# Stops before an artifact when the disk holding <dest> has less than MIN_FREE_MB (default 300) free.
# Usage: [NO_PNG=1] gh_collect.sh <run_id> <dest> [artifact-name-glob, default *]
set -euo pipefail
RUN="$1"; DEST="$2"; PAT="${3:-*}"
REPO="${GH_RUNNER_REPO:-martinbon39/holo-osworld-runner}"
MIN_FREE_MB="${MIN_FREE_MB:-300}"
mkdir -p "$DEST/_jobs"
TMP="$(mktemp -d)"; trap 'rm -rf "$TMP"' EXIT
gh run download "$RUN" -R "$REPO" -p "$PAT" -D "$TMP"
excl=(); [ "${NO_PNG:-0}" = 1 ] && excl=(--exclude='*.png' --exclude='report.html')
n=0
for a in "$TMP"/*/; do
  free_mb=$(df -Pm "$DEST" | awk 'NR==2{print $4}')
  if [ "$free_mb" -lt "$MIN_FREE_MB" ]; then echo "STOP: only ${free_mb} MB free on $DEST, $n artifacts copied" >&2; exit 3; fi
  name="$(basename "$a")"
  if [ -d "$a/pyautogui" ]; then tar -C "$a" -cf - "${excl[@]}" pyautogui | tar -C "$DEST" -xf -; fi
  if [ -d "$a/_job" ]; then rm -rf "$DEST/_jobs/$name"; mkdir -p "$DEST/_jobs/$name"; tar -C "$a/_job" -cf - . | tar -C "$DEST/_jobs/$name" -xf -; fi
  n=$((n + 1))
done
done_n=$(find "$DEST/pyautogui" -name result.txt 2>/dev/null | wc -l)
echo "run $RUN: $n artifacts -> $DEST ($done_n tasks with result.txt)"
