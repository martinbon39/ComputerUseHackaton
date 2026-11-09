#!/bin/bash
# V2c: Holo4-27B behind the frozen Feci Guard verifier (its prompt, schema and rule), openai backend, 12 in parallel.
set -euo pipefail
cd "$(dirname "$0")"
export GUARD_BACKEND=openai GUARD_BASE_URL=https://martinbon39--holo-judge-serve.us-east.modal.run/v1 \
  GUARD_MODEL=Holo4-27B GUARD_API_KEY_ENV=HOLO_MODAL_KEY
HOLO_MODAL_KEY="$(cat ~/.holo_modal_key)"
export HOLO_MODAL_KEY
exec ~/osw/venv/bin/python run_claude.py --workers 12 --out "${OUT:-holo4_feci_responses.jsonl}" "$@"
