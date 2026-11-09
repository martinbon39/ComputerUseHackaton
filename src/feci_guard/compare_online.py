"""Feci Guard online: task-by-task paired comparison with the original runs on the same task list.
Usage: python compare_online.py --guard ~/osw/results_feci_guard --orig ~/osw/results_confirm_gh_orig_confirm \
         --orig ~/osw/results_val_orig_eager_m40 --tasks <tasks.json> [--out compare.json]
Per task: score (result.txt), claimed done (finished_by_agent and not declared infeasible), false success (claimed done,
feasible task, score < 1; a "done" on an infeasible task is not counted), guard decisions. Paired bootstrap 95 % CI over tasks scored in both arms (10 000 resamples).
"""
import argparse, json, os, random
from pathlib import Path


def load(root, tasks):
    out = {}
    for dom, tid in tasks:
        d = Path(os.path.expanduser(root)) / "pyautogui/screenshot/Holo-3.1-4B" / dom / tid
        if not (d / "result.txt").exists():
            continue
        m = json.loads((d / "meta.json").read_text()) if (d / "meta.json").exists() else {}
        score = float((d / "result.txt").read_text())
        claimed = bool(m.get("finished_by_agent")) and not m.get("model_declared_infeasible")
        out[f"{dom}/{tid}"] = {"score": score, "claimed_done": claimed, "infeasible_task": m.get("infeasible_task"),
                              "false_success": claimed and not m.get("infeasible_task") and score < 1,
                              "guard": m.get("feci_guard")}
    return out


def boot(diffs, n=10000, seed=0):
    rnd = random.Random(seed)
    k = len(diffs)
    means = sorted(sum(rnd.choice(diffs) for _ in range(k)) / k for _ in range(n))
    return [round(means[int(0.025 * n)], 4), round(means[int(0.975 * n) - 1], 4)]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--guard", required=True)
    ap.add_argument("--orig", action="append", required=True)
    ap.add_argument("--tasks", required=True)
    ap.add_argument("--out")
    a = ap.parse_args()
    tj = json.load(open(os.path.expanduser(a.tasks)))
    tasks = [(d, t) for d in tj for t in tj[d]]
    g = load(a.guard, tasks)
    origs = {o: load(o, tasks) for o in a.orig}
    rep = {"tasks": len(tasks), "guard_scored": len(g)}
    rep["guard"] = {"success": sum(x["score"] for x in g.values()), "false_success": sum(x["false_success"] for x in g.values()),
                    "refusals": sum((x["guard"] or {}).get("refusals", 0) for x in g.values()),
                    "episodes_refused": sum(bool((x["guard"] or {}).get("refusals")) for x in g.values()),
                    "refused_then_no_answer": sum(bool((x["guard"] or {}).get("refusals")) and not x["claimed_done"]
                                                  for x in g.values()),
                    "refused_then_solved": sum(bool((x["guard"] or {}).get("refusals")) and x["score"] >= 1
                                               for x in g.values())}
    for name, o in origs.items():
        common = sorted(set(g) & set(o))
        diffs = [g[k]["score"] - o[k]["score"] for k in common]
        solved = [k for k in common if o[k]["score"] >= 1]
        rep[Path(name).name] = {
            "paired_tasks": len(common),
            "orig_success": sum(o[k]["score"] for k in common), "guard_success": sum(g[k]["score"] for k in common),
            "delta_pts": round(100 * sum(diffs) / len(diffs), 2) if diffs else None,
            "ci95_pts": [round(100 * x, 2) for x in boot(diffs)] if diffs else None,
            "orig_false_success": sum(o[k]["false_success"] for k in common),
            "guard_false_success": sum(g[k]["false_success"] for k in common),
            "wins": [k for k in common if g[k]["score"] > o[k]["score"]],
            "losses": [k for k in common if g[k]["score"] < o[k]["score"]],
            "cost_refused_on_orig_solved (upper bound: other stochastic run)": [k for k in solved if (g[k]["guard"] or {}).get("refusals")],
            "cost_refused_on_orig_solved_then_lost": [k for k in solved if (g[k]["guard"] or {}).get("refusals")
                                                     and g[k]["score"] < 1],
        }
    common = sorted(set(g).intersection(*[set(o) for o in origs.values()]))
    if common and len(origs) > 1:
        diffs = [g[k]["score"] - sum(o[k]["score"] for o in origs.values()) / len(origs) for k in common]
        rep["vs_mean_of_orig_runs"] = {"paired_tasks": len(common), "delta_pts": round(100 * sum(diffs) / len(diffs), 2),
                                      "ci95_pts": [round(100 * x, 2) for x in boot(diffs)]}
    rep["per_task"] = {k: {"guard": g[k], **{Path(n).name: o.get(k, {}).get("score") for n, o in origs.items()}}
                       for k in sorted(g)}
    s = json.dumps(rep, indent=1, ensure_ascii=False)
    if a.out:
        Path(a.out).write_text(s)
    print(json.dumps({k: v for k, v in rep.items() if k != "per_task"}, indent=1, ensure_ascii=False))


if __name__ == "__main__":
    main()
