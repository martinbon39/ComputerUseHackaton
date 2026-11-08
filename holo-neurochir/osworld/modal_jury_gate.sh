#!/usr/bin/env bash
# Gate of the public jury endpoint holo-jury-probe (Modal account 2): while closed, /probe answers 503 and never
# calls the H100 servers. Open it only for the judging window, once both holo-vllm apps are deployed and warm.
# Usage: bash osworld/modal_jury_gate.sh open|close|status
set -euo pipefail
PY=$(head -1 "$(command -v modal)" | sed 's/^#!//')
MODAL_PROFILE=martinbon39 "$PY" - "$1" <<'PYEOF'
import sys, modal
g = modal.Dict.from_name("holo-jury-gate", create_if_missing=True)
if sys.argv[1] in ("open", "close"):
    g.put("open", sys.argv[1] == "open")
elif sys.argv[1] != "status":
    sys.exit("usage: open|close|status")
print("holo-jury-gate open =", g.get("open", False))
PYEOF
