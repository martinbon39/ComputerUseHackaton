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

echo; echo "== (b2) the three judges recounted from their raw responses (README rows 2 and 7) =="
"$PY" jury_kit/recount_judges.py | tail -6

echo; echo "== (c) demo replay pages =="
"$PY" - <<'PY'
import html.parser, pathlib
for name, what in [("holo-neurochir/demo_live/repair_calc.html", "Feci Guard refuses a false done, the agent repairs"),
                   ("holo-neurochir/demo_faux_fini/demo_faux_fini.html", "one task, the original's false done next to the merged agent")]:
    p = pathlib.Path(name)
    s = p.read_text(encoding="utf-8")
    class P(html.parser.HTMLParser):
        scripts = 0; ext = []
        def handle_starttag(self, tag, a):
            a = dict(a)
            if tag == "script":
                P.scripts += 1
                if a.get("src"): P.ext.append(a["src"])
    P().feed(s)
    n_data = s.count("data:image/")
    assert n_data > 0 and not P.ext, (name, n_data, P.ext)
    print(f"{p}: {p.stat().st_size/1e6:.1f} MB, {n_data} embedded screenshots, 0 external scripts: {what}")
PY
echo; echo "QUICKSTART OK: (a) and (b) match the published numbers, (c) the two demo pages are ready to open in a browser."
