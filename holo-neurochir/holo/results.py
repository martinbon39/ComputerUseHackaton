"""Phase 5 report: metrics per arm with 95 % CI (bootstrap over tasks), results.md / results.json / PNG charts.
Usage: python -m holo.results --arms original=eval_original,corrective=eval_corrective,steer=eval_steer,patched=eval_patched
"""
import holo.settings as S
import argparse, json
from collections import defaultdict
import numpy as np
from holo.taxonomy import scan
from holo.splits import TEST_UNSEEN, EASY, DIAG_TASKS

RNG = np.random.default_rng(0)


def boot_ci(per_task_vals, B=2000):
    """per_task_vals: dict task -> list of per-rollout values. Resample tasks, then rollouts within task."""
    tasks = list(per_task_vals)
    if not tasks:
        return (float("nan"),) * 3
    point = np.mean([v for t in tasks for v in per_task_vals[t]])
    stats = []
    for _ in range(B):
        ts = RNG.choice(tasks, len(tasks))
        vals = np.concatenate([RNG.choice(per_task_vals[t], len(per_task_vals[t])) for t in ts])
        stats.append(vals.mean())
    lo, hi = np.percentile(stats, [2.5, 97.5])
    return float(point), float(lo), float(hi)


def metrics(rows, subset):
    by = defaultdict(lambda: defaultdict(list))
    for d, s, steps, c in rows:
        t = s["task"]
        if subset == "unseen" and t not in TEST_UNSEEN: continue
        if subset == "seen" and t not in DIAG_TASKS: continue
        if subset == "easy" and t not in EASY: continue
        if subset == "test" and t in EASY: continue
        if s["impossible"]: continue
        by["success"][t].append(float(c["success"]))
        by["false_success"][t].append(float(c["false_success"]))
        by["loop"][t].append(float(c["loop"]))
        by["steps"][t].append(float(s["n_steps"]))
        by["wall_s"][t].append(float(s["wall_s"]))
    n = sum(len(v) for v in by["success"].values())
    out = {"n": n, "n_tasks": len(by["success"])}
    for k in ["success", "false_success", "loop", "steps", "wall_s"]:
        p, lo, hi = boot_ci(by[k])
        out[k] = {"mean": p, "lo": lo, "hi": hi}
    return out


def paired_diff(rows_a, rows_b, key="success"):
    """Paired (same task+seed) difference b - a, bootstrap over tasks."""
    def idx(rows):
        return {(s["task"], s["seed"]): c for d, s, st, c in rows if not s["impossible"] and s["task"] not in EASY}
    A, Bm = idx(rows_a), idx(rows_b)
    per = defaultdict(list)
    for k in A.keys() & Bm.keys():
        per[k[0]].append(float(Bm[k][key]) - float(A[k][key]))
    return boot_ci(per)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--arms", required=True)
    ap.add_argument("--patch_spec", default="patch_spec.json")
    a = ap.parse_args()
    arms = dict(kv.split("=") for kv in a.arms.split(","))
    data = {arm: scan(tag) for arm, tag in arms.items()}
    res = {"arms": {}, "paired_vs_original": {}}
    for arm, rows in data.items():
        res["arms"][arm] = {sub: metrics(rows, sub) for sub in ["test", "unseen", "seen", "easy"]}
    if "original" in data:
        for arm in data:
            if arm != "original":
                res["paired_vs_original"][arm] = {k: dict(zip(["mean", "lo", "hi"], paired_diff(data["original"], data[arm], k)))
                                                  for k in ["success", "false_success", "loop"]}
    try:
        res["patch"] = json.loads((S.ROOT / a.patch_spec).read_text(encoding="utf-8"))
    except Exception:
        pass
    (S.ROOT / "results.json").write_text(json.dumps(res, indent=1), encoding="utf-8")

    import matplotlib; matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    names = list(data)
    fig, axes = plt.subplots(1, 3, figsize=(13, 4))
    for ax, (k, title) in zip(axes, [("success", "Taux de succès (test)"), ("false_success", "Taux de faux succès (test)"),
                                      ("loop", "Rollouts avec boucle (test)")]):
        m = [res["arms"][n]["test"][k] for n in names]
        ax.bar(names, [100 * x["mean"] for x in m], color=["#888", "#c9a227", "#4a7fb5", "#2e9e5b"][: len(names)],
               yerr=[[100 * (x["mean"] - x["lo"]) for x in m], [100 * (x["hi"] - x["mean"]) for x in m]], capsize=5)
        ax.set_title(title); ax.set_ylabel("%"); ax.set_ylim(0, 100)
    plt.tight_layout(); plt.savefig(S.ROOT / "results_arms.png", dpi=130)

    L = ["# Résultats — phase 5 (évaluation finale)", "",
         "Même harness, mêmes seeds, mêmes réglages pour les 4 bras. IC 95 % = bootstrap sur les tâches (puis rollouts).",
         "Test = tâches jamais vues (" + ", ".join(TEST_UNSEEN) + ") + nouvelles seeds (100-101) des tâches du diagnostic.", "",
         "![bras](results_arms.png)", "",
         "| Bras | n | Succès | Faux succès | Boucle | Pas moyens | Temps/tâche (s) | Succès tâches faciles |",
         "|---|---|---|---|---|---|---|---|"]
    f = lambda x: f"{100 * x['mean']:.1f} % [{100 * x['lo']:.1f} ; {100 * x['hi']:.1f}]"
    for n in names:
        t, e = res["arms"][n]["test"], res["arms"][n]["easy"]
        L.append(f"| {n} | {t['n']} | {f(t['success'])} | {f(t['false_success'])} | {f(t['loop'])} | {t['steps']['mean']:.1f} | "
                 f"{t['wall_s']['mean']:.0f} | {f(e['success'])} (n={e['n']}) |")
    L += ["", "## Sous-ensembles", "", "| Bras | Succès tâches jamais vues | Succès nouvelles seeds |", "|---|---|---|"]
    for n in names:
        L.append(f"| {n} | {f(res['arms'][n]['unseen']['success'])} (n={res['arms'][n]['unseen']['n']}) | "
                 f"{f(res['arms'][n]['seen']['success'])} (n={res['arms'][n]['seen']['n']}) |")
    if res["paired_vs_original"]:
        L += ["", "## Différences appariées vs original (même tâche, même seed)", "",
              "| Bras | Δ succès | Δ faux succès | Δ boucle |", "|---|---|---|---|"]
        g = lambda x: f"{100 * x['mean']:+.1f} pts [{100 * x['lo']:+.1f} ; {100 * x['hi']:+.1f}]"
        for n, v in res["paired_vs_original"].items():
            L.append(f"| {n} | {g(v['success'])} | {g(v['false_success'])} | {g(v['loop'])} |")
    if "patch" in res:
        p = res["patch"]
        L += ["", "## Patch", "", f"- Couches {p.get('layers')}, α={p.get('alpha')}, top-k={p.get('topk')}, "
              f"poids modifiés : {p.get('n_modified')} ({p.get('pct_modified', 0):.4f} % du modèle)"]
    (S.ROOT / "results.md").write_text("\n".join(L), encoding="utf-8")
    print("\n".join(L))


if __name__ == "__main__":
    main()
