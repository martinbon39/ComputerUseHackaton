"""Check the Holo-3.1-4B files on the serving node against pins.json (sha256), before any episode.
Usage: python3 check_weights.py <snapshot dir, e.g. ~/.cache/huggingface/hub/models--Hcompany--Holo-3.1-4B/snapshots/8c88...>
Exit 0 when every pinned file matches."""
import hashlib
import json
import os
import sys

pins = json.load(open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "pins.json")))["model"]
d = sys.argv[1]
bad = 0
for name, want in pins["sha256"].items():
    h = hashlib.sha256()
    with open(os.path.join(d, name), "rb") as f:
        for chunk in iter(lambda: f.read(1 << 24), b""):
            h.update(chunk)
    ok = h.hexdigest() == want
    bad += not ok
    print(f"{'OK  ' if ok else 'BAD '} {name} {h.hexdigest()}")
sys.exit(1 if bad else 0)
