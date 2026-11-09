"""Record a side-by-side demo (original vs patched, same task, same seed) as a replayable JSON.
Each step stores: screenshot (base64 PNG), action, short reasoning/content, gauge <h_l, u> per selected layer.
Usage: python -m holo.demo_record --task click-collapsible --seed 7 --spec patch_spec.json --name demo1
"""
import holo.settings as S
import argparse, base64, io, json, copy
from pathlib import Path
import numpy as np
from holo.model import Holo
from holo.agent import run_episode
from holo.surgery import load_spec, apply_patch_inplace

DEMO_DIR = S.ROOT / "demo"


def make_gauge(spec):
    D = np.load(S.ROOT / spec["direction_file"])
    layers = [int(l) for l in spec.get("gauge_layers", spec["layers"])]
    U = {l: D["U"][l] for l in layers}

    def gauge(resid):  # resid: [L, D] float16
        return {str(l): float(resid[l].astype(np.float32) @ U[l]) for l in layers}
    thr = {str(l): float((D["pos_mean"][l] + D["neg_mean"][l]) / 2) for l in layers}
    return gauge, thr


def img_b64(img):
    buf = io.BytesIO(); img.save(buf, format="PNG"); return base64.b64encode(buf.getvalue()).decode()


def record_arm(holo, task, seed, gauge, arm, max_steps, emit=None):
    steps = []

    def on_step(rec, img):
        ev = {"arm": arm, "t": rec["t"], "img": img_b64(img), "action": rec["action"] or "(aucune action valide)",
              "text": (rec.get("content") or rec.get("reasoning") or "")[:200], "gauge": rec.get("gauge", {}),
              "reward": rec["reward"]}
        steps.append(ev)
        if emit: emit(ev)
    out = S.RUNS_DIR / "demo_runs" / f"{task}__s{seed}__{arm}"
    s = run_episode(holo, task, seed, out, max_steps=max_steps, gauge=gauge, on_step=on_step)
    outcome = {"arm": arm, "reward": s["reward"], "n_steps": s["n_steps"], "claimed_done": s["claimed_done"],
               "env_done": s["env_done"], "success": s["reward"] > 0}
    if emit: emit({"arm": arm, "done": True, **outcome})
    return {"steps": steps, "outcome": outcome}


def record(task, seed, spec_path, name, max_steps=None, holo_orig=None, holo_patched=None, emit=None):
    from holo.rollouts import BUDGET
    spec = load_spec(spec_path)
    gauge, thr = make_gauge(spec)
    max_steps = max_steps or BUDGET.get(task, 10)
    holo_orig = holo_orig or Holo()
    if holo_patched is None:
        holo_patched = Holo(); apply_patch_inplace(holo_patched.model, spec)
    demo = {"name": name, "task": task, "seed": seed, "threshold": thr, "spec": spec,
            "n_layers": holo_orig.n_layers}
    demo["original"] = record_arm(holo_orig, task, seed, gauge, "original", max_steps, emit)
    demo["patched"] = record_arm(holo_patched, task, seed, gauge, "patched", max_steps, emit)
    s = json.loads((S.RUNS_DIR / "demo_runs" / f"{task}__s{seed}__original" / "summary.json").read_text(encoding="utf-8"))
    demo["goal"] = s.get("goal", "")
    DEMO_DIR.mkdir(exist_ok=True)
    (DEMO_DIR / f"{name}.json").write_text(json.dumps(demo), encoding="utf-8")
    return demo


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--task", required=True); ap.add_argument("--seed", type=int, required=True)
    ap.add_argument("--spec", default="patch_spec.json"); ap.add_argument("--name", required=True)
    a = ap.parse_args()
    d = record(a.task, a.seed, a.spec, a.name)
    print(json.dumps({k: d[k]["outcome"] for k in ("original", "patched")}))
