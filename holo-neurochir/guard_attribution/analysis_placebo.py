"""Supplementary analysis for arm D (report/PREREG_GUARD_PLACEBO.md), as drafted there. Python >= 3.9 stdlib only.
The frozen analysis (analysis.py, arms A, B, C) is not changed by arm D.

Valid (task, seed): scored in all four arms. A (task, seed) dropped by the frozen rule (A, B or C dead after rerun)
is dropped here too; a (task, seed) where only D is dead is dropped from this analysis only.
Primary: C - D on false "done", per task averaged over valid seeds, bootstrap over tasks (10,000 draws,
random.Random(0), percentile 95 %): the guard's verdict, not refusal as such, lowers false "done" only if the upper
bound is < 0. Kill rule: if C's refusal rate in seed 0 (refused / answers that got a verdict: not infeasible, not at the cap, not
without verdict) is outside [r/2, 2r], D is not a
matched placebo; C - D (false done and score) is then reported as descriptive only and D is labelled "random
refusal at rate r".
Secondaries: (1) D - B false "done" (effect of random refusal); (2) C - D score (lower bound > 0) and C - B score;
(3) competing-risk decomposition per arm: true done, false done, step cap, other; (4) sign-flip randomisation
p-values (two-sided, 100,000 Monte Carlo flips, seed 0) for C - D false "done" and score, alongside the bootstrap.
Usage: python3 analysis_placebo.py --results DIR [--out FILE] [--md FILE]
"""
from __future__ import annotations

import argparse
import json
import os
import random

import analysis as A
from neutral_verifier import PLACEBO_RATE

ARMS4 = ("A", "B", "C", "D")
N_FLIPS = 100000


def signflip_p(d: list[float], n: int = N_FLIPS, seed: int = 0) -> float:
    rng = random.Random(seed)
    obs = abs(sum(d))
    hits = sum(1 for _ in range(n) if abs(sum(x if rng.random() < 0.5 else -x for x in d)) >= obs - 1e-12)
    return (hits + 1) / (n + 1)


def per_task_diff(eps, valid, x, y, field):
    ts = [t for t in sorted(valid) if valid[t]]
    return [sum(float(eps[(x, s, t)][field]) for s in valid[t]) / len(valid[t])
            - sum(float(eps[(y, s, t)][field]) for s in valid[t]) / len(valid[t]) for t in ts]


def outcome(ep) -> str:
    if ep["false_done"]:
        return "false_done"
    if ep["actions"] and ep["actions"][-1]["tool_name"] == "answer" and ep["score"] > 0:
        return "true_done"
    if ep["step_cap"]:
        return "step_cap"
    return "other"


def refusal_rate(eps, arm, seed) -> dict:
    ref = chk = 0
    for (a, s, t), ep in eps.items():
        if a == arm and s == seed:
            ref += ep["guard_decisions"].count("refused")
            chk += sum(1 for x in ep["guard_decisions"] if x not in ("passed_infeasible", "passed_cap", "passed_no_verdict"))
    return {"refused": ref, "checked": chk, "rate": ref / chk if chk else None}


def analyse(root: str, tasks: list[str], seeds=(0, 1, 2), r: float = PLACEBO_RATE) -> dict:
    eps = A.load(root, ARMS4)
    valid, dropped = {}, []
    for t in tasks:
        for s in seeds:
            if all((a, s, t) in eps for a in ARMS4):
                valid.setdefault(t, []).append(s)
            else:
                dropped.append(f"{t} seed{s} (missing: {','.join(a for a in ARMS4 if (a, s, t) not in eps)})")
    primary = A.paired(eps, valid, "C", "D", "false_done")
    rr_c0, rr_d0 = refusal_rate(eps, "C", 0), refusal_rate(eps, "D", 0)
    killed = rr_c0["rate"] is None or not (r / 2 <= rr_c0["rate"] <= 2 * r)
    primary["verdict_lowers_false_done"] = (not killed) and bool(primary.get("n_tasks")) and primary["ci95"][1] < 0
    primary["kill_rule"] = {"C_seed0_refusal": rr_c0, "D_seed0_refusal": rr_d0, "r": r,
                            "band": [r / 2, 2 * r], "killed": killed}
    s2 = {"C_minus_D": A.paired(eps, valid, "C", "D", "score"), "C_minus_B": A.paired(eps, valid, "C", "B", "score"),
          "note": "C - B here uses the four-arm valid set; the frozen secondary 2 (analysis.py) is the reference"}
    s2["C_minus_D"]["score_gain_over_placebo"] = (not killed) and bool(s2["C_minus_D"].get("n_tasks")) and \
        s2["C_minus_D"]["ci95"][0] > 0
    pairs = [(t, s) for t in sorted(valid) for s in valid[t]]
    s3 = {a: {k: sum(1 for t, s in pairs if outcome(eps[(a, s, t)]) == k)
              for k in ("true_done", "false_done", "step_cap", "other")} for a in ARMS4}
    s4 = {"C_minus_D_false_done_p": signflip_p(per_task_diff(eps, valid, "C", "D", "false_done")) if valid else None,
          "C_minus_D_score_p": signflip_p(per_task_diff(eps, valid, "C", "D", "score")) if valid else None}
    ended_refused = {a: sum(1 for t, s in pairs if eps[(a, s, t)]["ended_on_refused_answer"]) for a in ("C", "D")}
    return {"prereg": "holo-neurochir/report/PREREG_GUARD_PLACEBO.md", "n_tasks_valid": len(valid),
            "label_D": "random refusal at rate %.2f" % r + (" (not a matched placebo: kill rule)" if killed else ""),
            "episodes_ending_on_refused_answer": ended_refused,
            "n_pairs_valid": len(pairs), "dropped_task_seed": dropped,
            "primary_C_minus_D_false_done": primary,
            "s1_D_minus_B_false_done": A.paired(eps, valid, "D", "B", "false_done"),
            "s2_score": s2, "s3_competing_risks": s3, "s4_signflip": s4,
            "realised_refusal_rates": {f"{a}_seed{s}": refusal_rate(eps, a, s) for a in ("C", "D") for s in seeds}}


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--results", required=True)
    ap.add_argument("--tasks", default=os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                                                    "osworld", "split_test.json"))
    ap.add_argument("--seeds", default="0,1,2")
    ap.add_argument("--out", default=None)
    a = ap.parse_args()
    m = json.load(open(a.tasks))
    res = analyse(a.results, [f"{d}/{t}" for d in m for t in m[d]], [int(x) for x in a.seeds.split(",")])
    js = json.dumps(res, indent=1)
    if a.out:
        open(a.out, "w").write(js)
    print(js)
