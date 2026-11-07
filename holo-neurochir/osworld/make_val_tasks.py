"""Online-validation task lists (split_diag only; split_test is never read).

val_confirm_tasks.json      main arm: ALL tasks of confirm_tasks.json (frozen by ares, never used to build an
                            intervention; sha256 checked), each tagged from the diagnostic passes:
                            fs (>= 1 completed pass false_success) / ok (success in every completed pass) / other.
val_fs_insample_tasks.json  secondary diagnostic, IN-SAMPLE: every split_diag task with >= 1 false_success pass.
Both are run_holo --test_meta files ({domain: [example_id]}); val_tasks_provenance.json keeps tags and outcomes.
Usage: PYTHONPATH=. ~/osw/venv/bin/python osworld/make_val_tasks.py [--results "~/osw/results_diag*"]
"""
import argparse, glob, hashlib, json, os
from collections import defaultdict
from pathlib import Path
from holo.osw_taxonomy import classify, find_tasks, load_task

HERE = Path(__file__).resolve().parent
CONFIRM_SHA256 = "03726f07b411869a7a4004b0f3c89ba37d89e948f34ac19cb70e4bb0c3cb5bb7"


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
            per_task[f"{d.parent.name}/{d.name}"].append({"pass": Path(r).name, "category": c["category"],
                                                          "fs_kind": c["fs_kind"], "score": score})
    return per_task


def keys(meta):
    return {f"{dom}/{e}" for dom, ids in meta.items() for e in ids}


def as_meta(ks):
    m = defaultdict(list)
    for k in sorted(ks):
        dom, eid = k.split("/")
        m[dom].append(eid)
    return dict(m)


def tag(runs):
    if any(o["category"] == "false_success" for o in runs):
        return "fs"
    if runs and all(o["category"] == "success" for o in runs):
        return "ok"
    return "other"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--results", default="~/osw/results_diag*")
    a = ap.parse_args()
    in_diag = keys(json.loads((HERE / "split_diag.json").read_text()))
    confirm = json.loads((HERE / "confirm_tasks.json").read_text())
    sha = hashlib.sha256(json.dumps(confirm["tasks"], sort_keys=True).encode()).hexdigest()
    assert sha == confirm["sha256_tasks"] == CONFIRM_SHA256, f"confirm_tasks.json changed: {sha}"
    conf = keys(confirm["tasks"])
    assert len(conf) == confirm["n"] and conf <= in_diag

    per_task = {k: v for k, v in outcomes(a.results).items() if k in in_diag}
    tags = {k: tag(per_task.get(k, [])) for k in sorted(conf)}
    fs_insample = sorted(k for k, v in per_task.items() if tag(v) == "fs")

    (HERE / "val_confirm_tasks.json").write_text(json.dumps(as_meta(conf), indent=1))
    (HERE / "val_fs_insample_tasks.json").write_text(json.dumps(as_meta(fs_insample), indent=1))
    prov = {"results": a.results, "passes": sorted({o["pass"] for v in per_task.values() for o in v}),
            "n_tasks_scored": len(per_task), "confirm_sha256": sha,
            "confirm": {k: {"tag": tags[k], "runs": per_task.get(k, [])} for k in tags},
            "fs_insample": {k: per_task[k] for k in fs_insample}}
    (HERE / "val_tasks_provenance.json").write_text(json.dumps(prov, indent=1))
    count = lambda t: sum(v == t for v in tags.values())
    print(json.dumps({"passes": prov["passes"], "n_tasks_scored": len(per_task), "confirm": len(conf),
                      "confirm_tags": {t: count(t) for t in ("fs", "ok", "other")},
                      "fs_insample": len(fs_insample), "fs_insample_in_confirm": len(set(fs_insample) & conf)}))


if __name__ == "__main__":
    main()
