#!/usr/bin/env bash
# Quickstart: no GPU, no key, no VM, Python >= 3.9 standard library only. Exit 0 = every published number reproduced.
set -euo pipefail
cd "$(dirname "$0")/.."
PY="${PYTHON:-python3}"
export PYTHONDONTWRITEBYTECODE=1

echo "== (a) OSWorld paired comparisons, recomputed from per-task scores =="
"$PY" jury_kit/verify_results.py

echo; echo "== (b) Feci Guard replayed on 268 recorded episodes (frozen decision code, recorded verdicts) =="
"$PY" jury_kit/replay_guard.py --show 1

echo; echo "== (c) demo replay page =="
"$PY" - <<'PY'
import html.parser, pathlib
p = pathlib.Path("holo-neurochir/demo_faux_fini/demo_faux_fini.html")
s = p.read_text(encoding="utf-8")
class P(html.parser.HTMLParser):
    imgs = scripts = 0; ext = []
    def handle_starttag(self, tag, a):
        a = dict(a)
        if tag == "img": P.imgs += 1
        if tag == "script":
            P.scripts += 1
            if a.get("src"): P.ext.append(a["src"])
P().feed(s)
n_data = s.count("data:image/")
assert n_data > 0 and not P.ext, (n_data, P.ext)
print(f"{p}: {p.stat().st_size/1e6:.1f} MB, self-contained ({n_data} embedded images, {P.scripts} inline scripts, "
      f"0 external scripts). Open it in a browser.")
PY
echo; echo "QUICKSTART OK: (a) and (b) match the published numbers, (c) is ready to open."
