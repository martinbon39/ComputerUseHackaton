"""Pairwise paired comparison of the arms of an online validation run (run_patched_eval.sh).

Arms are given as name=results_dir, in order; every pair (A, B) with A listed before B is compared, delta = A - B
(e.g. patched=… prompt=… orig=… gives patched-prompt, patched-orig, prompt-orig).
Several splits: name=dir_split1,dir_split2 with --strata split1,split2 (same order for every arm). Adds one subset per
split (split:<name>) and 'pooled', whose bootstrap resamples tasks within each split (stratified).
Per task present and scored in both arms, in priority order: success (score > 0), false success (holo.osw_taxonomy
category), reaching the 50-step limit without answering (step_limit), number of steps.
Subsets (from val_tasks_provenance.json): confirm (out of sample, main) and its diag tags confirm:fs / confirm:ok /
confirm:other; insample (fs tasks outside confirm, secondary); all pairs. --origin is required (FLEET_ORDERS.md):
stuck = the candidate was built by astra-stuck or combines a stuck edit -> confirm keeps only the odd sha1 half (the
even half was used for construction); other = all 45 confirm tasks. For each: rate per arm, paired delta, bootstrap
IC95 over tasks, and the number of pairs where A is higher / lower.
Usage: PYTHONPATH=. ~/osw/venv/bin/python osworld/compare_val.py --origin stuck|other [--out f.json]
         [--subsets confirm,...] [--strata confirm,test] name=dir[,dir] name=dir[,dir] [...]
"""
import argparse, itertools, json
from pathlib import Path
import numpy as np
from holo.osw_taxonomy import classify, find_tasks, load_task

HERE = Path(__file__).resolve().parent
N_BOOT = 10000
MAX_STEPS = 50
METRICS = ("success", "false_success", "step_limit", "n_steps")


def arm(results_dirs, strata):
    out = {}
    for results_dir, stratum in zip(results_dirs, strata):
        part = one_dir(results_dir, stratum)
        assert not part.keys() & out.keys(), f"a task appears in two splits: {sorted(part.keys() & out.keys())[:3]}"
        out.update(part)
    return out


def one_dir(results_dir, stratum):
    out = {}
    for d in find_tasks(results_dir):
        meta, score, steps = load_task(d)
        if not steps or score is None:
            continue
        c = classify(meta, score, steps, [None] * len(steps), max_steps=MAX_STEPS)
        out[f"{d.parent.name}/{d.name}"] = {"success": score > 0, "false_success": c["category"] == "false_success",
                                            "n_steps": c["n_steps"], "step_limit": c["step_limit"], "stratum": stratum}
    return out


def paired(p, o, keys, rng):
    res = {"n_pairs": len(keys)}
    if not keys:
        return res
    for m in METRICS:
        a = np.array([p[k][m] for k in keys], float); b = np.array([o[k][m] for k in keys], float)
        d = a - b
        st = np.array([p[k]["stratum"] for k in keys])
        idx = np.concatenate([g[rng.integers(0, len(g), size=(N_BOOT, len(g)))]
                              for g in (np.flatnonzero(st == s) for s in sorted(set(st)))], axis=1)
        boot = d[idx].mean(axis=1)
        res[m] = {"a": a.mean(), "b": b.mean(), "delta": d.mean(),
                  "ic95": [float(np.percentile(boot, 2.5)), float(np.percentile(boot, 97.5))],
                  "a_higher": int((d > 0).sum()), "b_higher": int((d < 0).sum())}
    return res


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("arms", nargs="+", help="name=results_dir, at least two")
    ap.add_argument("--origin", required=True, choices=["stuck", "other"])
    ap.add_argument("--subsets", help="comma-separated subsets to print (default: all)")
    ap.add_argument("--strata", default="all")
    ap.add_argument("--out")
    a = ap.parse_args()
    strata = a.strata.split(",")
    arms = {n: d.split(",") for n, d in (x.split("=", 1) for x in a.arms)}
    assert len(arms) == len(a.arms) >= 2, "need at least two distinct name=results_dir arms"
    assert all(len(d) == len(strata) for d in arms.values()), "each arm needs one results dir per --strata entry"
    data = {name: arm(d, strata) for name, d in arms.items()}
    prov = json.loads((HERE / "val_tasks_provenance.json").read_text())
    conf = {k: v for k, v in prov["confirm"].items() if a.origin == "other" or v["half"] == "odd"}
    sets = {"confirm": set(conf)}
    for t in ("fs", "ok", "other"):
        sets[f"confirm:{t}"] = {k for k, v in conf.items() if v["tag"] == t}
    sets["insample"] = set(prov["fs_insample"]) - set(prov["confirm"])
    sets["all"] = set().union(*(x.keys() for x in data.values()))
    if len(strata) > 1:
        for st in strata:
            sets[f"split:{st}"] = {k for x in data.values() for k, v in x.items() if v["stratum"] == st}
        sets["pooled"] = sets.pop("all")
    shown = a.subsets.split(",") if a.subsets else list(sets)
    rng = np.random.default_rng(0)
    report = {"arms": arms, "strata": strata, "origin": a.origin, "n_scored": {n: len(x) for n, x in data.items()},
              "confirm_scope": "all 45" if a.origin == "other" else f"odd half ({prov['half_rule']})", "pairs": {}}
    for na, nb in itertools.combinations(arms, 2):
        pa, pb = data[na], data[nb]
        report["pairs"][f"{na}-{nb}"] = {s: {"n_tasks": len(ks), **paired(pa, pb, sorted(ks & pa.keys() & pb.keys()), rng)}
                                        for s, ks in sets.items()}
    if a.out:
        Path(a.out).write_text(json.dumps(report, indent=1))
    print("scored: " + ", ".join(f"{n} {k}" for n, k in report["n_scored"].items())
          + f"; origin {a.origin}: confirm = {report['confirm_scope']}")
    for pair, subs in report["pairs"].items():
        na, nb = pair.split("-", 1)
        for s in shown:
            r = subs[s]
            print(f"[{pair}] [{s}] pairs {r['n_pairs']}/{r['n_tasks']}")
            for m in METRICS:
                if m in r:
                    x = r[m]
                    print(f"  {m:13s} {na} {x['a']:6.3f}  {nb} {x['b']:6.3f}  delta {x['delta']:+7.3f}  "
                          f"IC95 [{x['ic95'][0]:+.3f}, {x['ic95'][1]:+.3f}]  {na} higher {x['a_higher']} / lower {x['b_higher']}")


if __name__ == "__main__":
    main()
