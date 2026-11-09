#!/usr/bin/env bash
# Copy the Guard into the GitHub runner repo (its workflow runs feci_guard/run_holo_guard.py from $GITHUB_WORKSPACE).
# This directory is the source of truth; the runner copy is overwritten, never edited there.
set -euo pipefail
SRC="$(cd "$(dirname "$0")" && pwd)"; DST="${1:-$HOME/projects/holo-osworld-runner}/feci_guard"
mkdir -p "$DST"
cp "$SRC"/{run_holo_guard.py,run_holo_guard_rescue.py,verifier.py,feci_guard.py,run_holo_guard_v2.py,feci_guard_v2.py,verifier_v2.py} "$DST"/
printf 'Synced from cogito-ergo-feci/src/feci_guard (do not edit here). See its README.md.\n' > "$DST/README.md"
(cd "$DST" && sha256sum run_holo_guard.py run_holo_guard_rescue.py verifier.py feci_guard.py run_holo_guard_v2.py feci_guard_v2.py verifier_v2.py)
