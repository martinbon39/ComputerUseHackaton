#!/usr/bin/env bash
# Regenerate every number, table and figure from paper/data/, then compile main.pdf.
set -euo pipefail
cd "$(dirname "$0")"
[ -x .venv/bin/python ] || { uv venv -q .venv && uv pip install -q --python .venv/bin/python matplotlib numpy pillow; }
cd figs
for f in osw_diag miniwob b4 teaser pipeline traps causal perceive expo attractor broad closures online infeasible power; do ../.venv/bin/python "$f.py"; done
cd ..
TECTONIC=${TECTONIC:-$(command -v tectonic || echo "$HOME/.local/bin/tectonic")}
"$TECTONIC" -X compile main.tex
"$TECTONIC" -X compile neurips.tex
