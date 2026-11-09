"""Applies holo-neurochir/report/PREREG_ONLINE_GUARD.md to the online Feci Guard arm (test split, Modal comparator).

Usage: python online_guard_analysis.py [--guard DIR] [--base DIR] [--base2 DIR] > out.json
"""
from __future__ import annotations

import argparse
import glob
import json
import os
import random

HOME = os.path.expanduser("~/osw")


def load(root: str) -> dict:
    out = {}
    for f in glob.glob(os.path.join(root, "**", "result.txt"), recursive=True):
        d = os.path.dirname(f)
        key = "/".join(d.split("/")[-2:])
        try:
            score = float(open(f).read().strip() or 0)
        except ValueError:
            score = 0.0
        last, n = "", 0
        tj = os.path.join(d, "traj.jsonl")
        if os.path.exists(tj):
            for line in open(tj):
                try:
                    last = json.loads(line).get("tool_name", "") or last
                    n += 1
                except json.JSONDecodeError:
                    pass
        out[key] = {"score": score, "steps": n, "false_done": last == "answer" and score == 0}
    return out


def boot(diffs: list[float], n: int = 10000, seed: int = 0) -> tuple[float, float]:
    rng = random.Random(seed)
    k = len(diffs)
    means = sorted(sum(diffs[rng.randrange(k)] for _ in range(k)) / k for _ in range(n))
    return means[int(0.025 * n)], means[int(0.975 * n) - 1]


def compare(g: dict, b: dict) -> dict:
    keys = sorted(k for k in set(g) & set(b) if g[k]["steps"] > 0 and b[k]["steps"] > 0)
    invalid = sorted((set(g) | set(b)) - set(keys))
    gs = [g[k]["score"] for k in keys]
    bs = [b[k]["score"] for k in keys]
    fd_g = [1.0 if g[k]["false_done"] else 0.0 for k in keys]
    fd_b = [1.0 if b[k]["false_done"] else 0.0 for k in keys]
    d_score = [x - y for x, y in zip(gs, bs)]
    d_fd = [x - y for x, y in zip(fd_g, fd_b)]
    B = sum(1 for x, y in zip(gs, bs) if y < 1 <= x)
    C = sum(1 for x, y in zip(gs, bs) if x < 1 <= y)
    E = sum(1 for x, y in zip(fd_g, fd_b) if y == 1 and x == 0)
    n = len(keys)
    lo_s, hi_s = boot(d_score)
    lo_f, hi_f = boot(d_fd)
    return {
        "n_tasks": n, "invalid_excluded": invalid,
        "score_guard": sum(gs) / n, "score_base": sum(bs) / n,
        "score_diff": sum(d_score) / n, "score_diff_ci95": [lo_s, hi_s],
        "false_done_guard": sum(fd_g) / n, "false_done_base": sum(fd_b) / n,
        "false_done_diff": sum(d_fd) / n, "false_done_diff_ci95": [lo_f, hi_f],
        "B_repaired": B, "C_true_lost": C, "E_false_done_avoided": E,
        "net_B_minus_C": B - C, "ratio_E_over_C": E / max(C, 1),
        "criterion1_false_done_down": hi_f < 0,
        "criterion2_score_gain": lo_s > 0,
        "rule5_useful": (B - C) >= 0 and hi_f < 0,
    }


def noise(a: dict, b: dict) -> dict:
    keys = [k for k in set(a) & set(b)]
    return {"n": len(keys), "flips_1_to_0": sum(1 for k in keys if a[k]["score"] >= 1 > b[k]["score"]),
            "flips_0_to_1": sum(1 for k in keys if a[k]["score"] < 1 <= b[k]["score"])}


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--guard", default=f"{HOME}/results_test_gh_orig_guard_claude")
    ap.add_argument("--base", default=f"{HOME}/results_test_gh_orig_modal_test")
    ap.add_argument("--base2", default=f"{HOME}/results_test_gh_orig")
    a = ap.parse_args()
    G, B, B2 = load(a.guard), load(a.base), load(a.base2)
    print(json.dumps({"primary_vs_modal": compare(G, B), "secondary_vs_pod": compare(G, B2),
                      "noise_orig_pod_vs_modal": noise(B2, B)}, indent=1))
