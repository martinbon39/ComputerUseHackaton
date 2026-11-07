"""Online-validation task lists from the diagnostic passes (split_diag only; split_test is never read).

val_fs_tasks.json  every split_diag task with >= 1 completed pass classified false_success (holo.osw_taxonomy rule)
val_ok_tasks.json  n split_diag tasks that succeeded in every completed pass and never ended in false success,
                   picked round-robin over domains in a seeded order (non-regression arm)
Both are run_holo --test_meta files ({domain: [example_id]}); val_tasks_provenance.json keeps per-task outcomes.
Usage: PYTHONPATH=. ~/osw/venv/bin/python osworld/make_val_tasks.py [--results "~/osw/results_diag*"] [--n_ok 15]
"""
import argparse, glob, hashlib, json, os
from collections import defaultdict
from pathlib import Path
from holo.osw_taxonomy import classify, find_tasks, load_task

HERE = Path(__file__).resolve().parent


def outcomes(results_glob):
    per_task = defaultdict(list)
    for r in sorted(glob.glob(os.path.expanduser(results_glob))):
        if not os.path.isdir(r):
            continue
        for d in find_tasks(r):
            meta, score, steps = load_task(d)
            if not steps or score is None:
                continue
            c = classify(meta, score, steps, [None] * len(steps), max_steps=50)
            per_task[(d.parent.name, d.name)].append({"pass": Path(r).name, "category": c["category"],
                                                      "fs_kind": c["fs_kind"], "score": score})
    return per_task


def as_meta(keys):
    m = defaultdict(list)
    for dom, eid in sorted(keys):
        m[dom].append(eid)
    return dict(m)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--results", default="~/osw/results_diag*")
    ap.add_argument("--n_ok", type=int, default=15)
    ap.add_argument("--seed", default="val-ok-v1")
    a = ap.parse_args()
    diag = json.loads((HERE / "split_diag.json").read_text())
    in_diag = {(dom, eid) for dom, ids in diag.items() for eid in ids}
    per_task = {k: v for k, v in outcomes(a.results).items() if k in in_diag}

    fs = sorted(k for k, v in per_task.items() if any(o["category"] == "false_success" for o in v))
    ok_pool = defaultdict(list)
    for k, v in per_task.items():
        if all(o["category"] == "success" for o in v):
            ok_pool[k[0]].append(k)
    order = lambda k: hashlib.sha1(f"{a.seed}/{k[0]}/{k[1]}".encode()).hexdigest()
    queues = {dom: sorted(ks, key=order) for dom, ks in sorted(ok_pool.items())}
    ok = []
    while len(ok) < a.n_ok and any(queues.values()):
        for dom in list(queues):
            if queues[dom] and len(ok) < a.n_ok:
                ok.append(queues[dom].pop(0))
    assert len(ok) == a.n_ok, f"only {len(ok)} always-successful split_diag tasks"

    (HERE / "val_fs_tasks.json").write_text(json.dumps(as_meta(fs), indent=1))
    (HERE / "val_ok_tasks.json").write_text(json.dumps(as_meta(ok), indent=1))
    prov = {"results": a.results, "passes": sorted({o["pass"] for v in per_task.values() for o in v}),
            "n_tasks_scored": len(per_task), "seed": a.seed,
            "fs": {f"{d}/{e}": per_task[(d, e)] for d, e in fs}, "ok": {f"{d}/{e}": per_task[(d, e)] for d, e in ok}}
    (HERE / "val_tasks_provenance.json").write_text(json.dumps(prov, indent=1))
    print(json.dumps({"passes": prov["passes"], "n_tasks_scored": len(per_task), "n_fs": len(fs), "n_ok": len(ok),
                      "fs_kinds": sorted({o["fs_kind"] for v in prov["fs"].values() for o in v if o["fs_kind"]})}))


if __name__ == "__main__":
    main()
