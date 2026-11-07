#!/usr/bin/env bash
# Download the artifacts of a holo-osworld-runner workflow run and merge them into one results dir that
# compare_val.py reads as name=<dest> (<dest>/pyautogui/screenshot/<model>/<domain>/<id>/).
# Per-job logs and timing.json go to <dest>/_jobs/<artifact>/.
# Usage: gh_collect.sh <run_id> <dest> [artifact-name-glob, default *]
set -euo pipefail
RUN="$1"; DEST="$2"; PAT="${3:-*}"
REPO="${GH_RUNNER_REPO:-martinbon39/holo-osworld-runner}"
TMP="$(mktemp -d)"; trap 'rm -rf "$TMP"' EXIT
gh run download "$RUN" -R "$REPO" -p "$PAT" -D "$TMP"
mkdir -p "$DEST/_jobs"
n=0
for a in "$TMP"/*/; do
  name="$(basename "$a")"
  if [ -d "$a/pyautogui" ]; then cp -r "$a/pyautogui" "$DEST/"; fi
  if [ -d "$a/_job" ]; then rm -rf "$DEST/_jobs/$name"; cp -r "$a/_job" "$DEST/_jobs/$name"; fi
  n=$((n + 1))
done
done_n=$(find "$DEST/pyautogui" -name result.txt 2>/dev/null | wc -l)
echo "run $RUN: $n artifacts -> $DEST ($done_n tasks with result.txt)"
