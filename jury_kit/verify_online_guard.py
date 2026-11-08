#!/usr/bin/env python3
"""README row 10: recompute the pre-registered online test of Feci Guard (Holo-3.1-4B, OSWorld test split, 120 tasks)
from the per-task outcomes in results/online_guard_tasks.csv, with the analysis code committed before the Guard results
were read (holo-neurochir/report/online_guard_analysis.py, function `compare`), and check it against
holo-neurochir/report/ONLINE_GUARD_RESULT.json. Standard library only; exit 1 on any mismatch."""
import csv, json, pathlib, sys

sys.dont_write_bytecode = True
ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "holo-neurochir" / "report"))
import online_guard_analysis as oga  # noqa: E402

arms = {}
for r in csv.DictReader((ROOT / "jury_kit" / "results" / "online_guard_tasks.csv").open()):
    arms.setdefault(r["arm"], {})[r["task"]] = {"score": float(r["score"]), "steps": int(r["steps"]),
                                               "false_done": r["false_done"] == "1"}
G, B, B2 = arms["orig_guard_claude_modal"], arms["orig_modal"], arms["orig_pod"]
got = {"primary_vs_modal": oga.compare(G, B), "secondary_vs_pod": oga.compare(G, B2),
       "noise_orig_pod_vs_modal": oga.noise(B2, B)}
ref = json.loads((ROOT / "holo-neurochir" / "report" / "ONLINE_GUARD_RESULT.json").read_text())

p = got["primary_vs_modal"]
pct = lambda x: f"{100 * x:+.1f}"
print("Online Feci Guard test, OSWorld test split, paired by task (bootstrap 10,000, seed 0)")
print(f"  tasks: {p['n_tasks']}, excluded: {len(p['invalid_excluded'])}")
print(f"  false 'done' rate : original {100*p['false_done_base']:.1f} % -> Guard {100*p['false_done_guard']:.1f} %"
      f"   diff {pct(p['false_done_diff'])} pts CI95 [{pct(p['false_done_diff_ci95'][0])}, {pct(p['false_done_diff_ci95'][1])}]")
print(f"  OSWorld score     : original {100*p['score_base']:.1f} -> Guard {100*p['score_guard']:.1f}"
      f"   diff {pct(p['score_diff'])} pts CI95 [{pct(p['score_diff_ci95'][0])}, {pct(p['score_diff_ci95'][1])}]")
print(f"  repaired B={p['B_repaired']}  true successes lost C={p['C_true_lost']}  net={p['net_B_minus_C']:+d}"
      f"  false done avoided E={p['E_false_done_avoided']}")
print(f"  criterion 1 (false done down): {p['criterion1_false_done_down']}   criterion 2 (score gain): "
      f"{p['criterion2_score_gain']} -> {'GAIN' if p['criterion2_score_gain'] else 'NO SCORE GAIN CLAIMED'}   rule 5 useful: {p['rule5_useful']}")


def same(a, b):
    if isinstance(a, float) or isinstance(b, float):
        return abs(a - b) < 1e-9
    if isinstance(a, dict):
        return a.keys() == b.keys() and all(same(a[k], b[k]) for k in a)
    if isinstance(a, list):
        return len(a) == len(b) and all(same(x, y) for x, y in zip(a, b))
    return a == b


ok = same(got, ref)
print("Matches ONLINE_GUARD_RESULT.json exactly." if ok else "MISMATCH with ONLINE_GUARD_RESULT.json.")
sys.exit(0 if ok else 1)
