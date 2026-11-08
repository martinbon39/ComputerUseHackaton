"""Builds demo_live/repair_calc.html: Feci Guard refuses a false 'done', the agent repairs (calc/1de60575, branch k0)."""
import base64, io, json, html, sys
from pathlib import Path
from PIL import Image

SRC = Path.home() / "osw/feci_demo/calc_1de60575/guard_branch_k0"
OUT = Path(__file__).resolve().parent / "repair_calc.html"


def img(p):
    im = Image.open(p).convert("RGB")
    im.thumbnail((1100, 1100))
    b = io.BytesIO(); im.save(b, "JPEG", quality=72)
    return "data:image/jpeg;base64," + base64.b64encode(b.getvalue()).decode()


def act(tc):
    return str(tc.get("element") or tc.get("content") or "")[:90]


guard = [json.loads(l) for l in open(SRC / "guard.jsonl")]
steps = [json.loads(l) for l in open(SRC / "frames/steps.jsonl")]
refusal, accept = guard[0], guard[-1]
assert refusal["verifier"]["verdict"] == "INCOMPLETE" and accept["verifier"]["verdict"] == "COMPLETE"


def reqs(v):
    return [{"m": {"yes": "✓", "no": "✗"}.get(r["status"], "?"), "t": r["requirement"], "e": r["evidence"]} for r in v["requirements"]]


scenes = [
    {"img": img(SRC / "guard_step_12.png"), "tag": "Holo-3.1-4B", "kind": "claim",
     "title": "The agent says: “done”", "fr": "L'agent annonce : « fini »", "text": refusal["answer"],
     "side": "Without the Guard, the episode ends here. Official OSWorld score: 0.",
     "side_fr": "Sans Guard, l'épisode s'arrête ici. Score officiel OSWorld : 0."},
    {"img": img(SRC / "guard_step_12.png"), "tag": "Feci Guard", "kind": "refuse",
     "title": "Feci Guard refuses", "fr": "Feci Guard refuse", "reqs": reqs(refusal["verifier"])},
]
NAMES = {"right_click": ("right click", "clic droit"), "click": ("click", "clic"), "write": ("type", "saisie"), "answer": ("answer", "réponse")}
for s in steps[1:]:
    tool = s["tool_call"]["tool_name"]
    scenes.append({"img": img(SRC / "frames" / s["frame"]), "tag": f"Repair · step {s['new_step']}/5 · réparation, pas {s['new_step']}/5", "kind": "step",
                   "title": f"{NAMES.get(tool, (tool, tool))[0]}: {act(s['tool_call'])}", "fr": f"{NAMES.get(tool, (tool, tool))[1]} : {act(s['tool_call'])}",
                   "text": s["thought"]})
last = sorted(SRC.glob("guard_step_1[3-9].png"))[-1]
scenes.append({"img": img(last), "tag": "Feci Guard", "kind": "accept", "title": "Feci Guard accepts", "fr": "Feci Guard accepte", "reqs": reqs(accept["verifier"]),
               "side": "Official OSWorld score: 1", "side_fr": "Score officiel OSWorld : 1"})

tpl = (Path(__file__).resolve().parent / "repair_template.html").read_text()
OUT.write_text(tpl.replace("/*SCENES*/[]", json.dumps(scenes, ensure_ascii=False)))
print(OUT, f"{OUT.stat().st_size/1e6:.1f} MB", len(scenes), "scenes")
