"""Paired comparison of the patched and original arms of an online validation run (run_patched_eval.sh).

Per task present and scored in both arms, in priority order: success (score > 0), false success (holo.osw_taxonomy
category), number of steps, and reaching the 50-step limit without answering (step_limit).
Subsets (from val_tasks_provenance.json): confirm (out of sample, main) and its diag tags confirm:fs / confirm:ok /
confirm:other; insample (fs tasks outside confirm, secondary); all pairs. --origin is required (FLEET_ORDERS.md):
stuck = the candidate was built by astra-stuck or combines a stuck edit -> confirm keeps only the odd sha1 half (the
even half was used for construction); other = all 45 confirm tasks. For each: rate per arm, paired delta
(patched - original), bootstrap IC95 over tasks, and the discordant pairs.
Usage: PYTHONPATH=. ~/osw/venv/bin/python osworld/compare_val.py <patched_results> <orig_results> --origin stuck|other
       [--out f.json]
"""
import argparse, json
from pathlib import Path
import numpy as np
from holo.osw_taxonomy import classify, find_tasks, load_task

HERE = Path(__file__).resolve().parent
N_BOOT = 10000
MAX_STEPS = 50
METRICS = ("success", "false_success", "n_steps", "step_limit")


def arm(results_dir):
    out = {}
    for d in find_tasks(results_dir):
        meta, score, steps = load_task(d)
        if not steps or score is None:
            continue
        c = classify(meta, score, steps, [None] * len(steps), max_steps=MAX_STEPS)
        out[f"{d.parent.name}/{d.name}"] = {"success": score > 0, "false_success": c["category"] == "false_success",
                                            "n_steps": c["n_steps"], "step_limit": c["step_limit"]}
    return out


def paired(p, o, keys, rng):
    res = {"n_pairs": len(keys)}
    if not keys:
        return res
    for m in METRICS:
        a = np.array([p[k][m] for k in keys], float); b = np.array([o[k][m] for k in keys], float)
        d = a - b
        idx = rng.integers(0, len(d), size=(N_BOOT, len(d)))
        boot = d[idx].mean(axis=1)
        res[m] = {"patched": a.mean(), "orig": b.mean(), "delta": d.mean(),
                  "ic95": [float(np.percentile(boot, 2.5)), float(np.percentile(boot, 97.5))],
                  "patched_only": int((d > 0).sum()), "orig_only": int((d < 0).sum())}
    return res


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("patched"); ap.add_argument("orig"); ap.add_argument("--out")
    ap.add_argument("--origin", required=True, choices=["stuck", "other"])
    a = ap.parse_args()
    p, o = arm(a.patched), arm(a.orig)
    prov = json.loads((HERE / "val_tasks_provenance.json").read_text())
    conf = {k: v for k, v in prov["confirm"].items() if a.origin == "other" or v["half"] == "odd"}
    sets = {"confirm": set(conf)}
    for t in ("fs", "ok", "other"):
        sets[f"confirm:{t}"] = {k for k, v in conf.items() if v["tag"] == t}
    sets["insample"] = set(prov["fs_insample"]) - set(prov["confirm"])
    sets["all"] = p.keys() | o.keys()
    rng = np.random.default_rng(0)
    report = {"patched": a.patched, "orig": a.orig, "origin": a.origin,
              "confirm_scope": "all 45" if a.origin == "other" else f"odd half ({prov['half_rule']})", "n_scored": {"patched": len(p), "orig": len(o)}, "subsets": {}}
    for name, ks in sets.items():
        keys = sorted(ks & p.keys() & o.keys())
        report["subsets"][name] = {"n_tasks": len(ks), **paired(p, o, keys, rng)}
    if a.out:
        Path(a.out).write_text(json.dumps(report, indent=1))
    print(f"scored: patched {len(p)}, orig {len(o)}; origin {a.origin}: confirm = {report['confirm_scope']}")
    for name, r in report["subsets"].items():
        print(f"[{name}] pairs {r['n_pairs']}/{r['n_tasks']}")
        for m in METRICS:
            if m in r:
                x = r[m]
                print(f"  {m:13s} patched {x['patched']:6.3f}  orig {x['orig']:6.3f}  delta {x['delta']:+7.3f}  "
                      f"IC95 [{x['ic95'][0]:+.3f}, {x['ic95'][1]:+.3f}]  pairs higher +{x['patched_only']}/-{x['orig_only']}")


if __name__ == "__main__":
    main()
