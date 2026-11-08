#!/usr/bin/env python3
"""Maintainers: export the per-task outcomes of the online Feci Guard test (README row 10) from the raw episode folders
on our server to jury_kit/results/online_guard_tasks.csv, with the loader of holo-neurochir/report/online_guard_analysis.py."""
import csv, os, pathlib, sys

ROOT = pathlib.Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "holo-neurochir" / "report"))
import online_guard_analysis as oga  # noqa: E402

ARMS = {"orig_guard_claude_modal": "results_test_gh_orig_guard_claude",
        "orig_modal": "results_test_gh_orig_modal_test",
        "orig_pod": "results_test_gh_orig"}
out = ROOT / "jury_kit" / "results" / "online_guard_tasks.csv"
with out.open("w", newline="") as f:
    w = csv.writer(f)
    w.writerow(["arm", "task", "score", "steps", "false_done"])
    for arm, d in ARMS.items():
        for task, r in sorted(oga.load(os.path.join(oga.HOME, d)).items()):
            w.writerow([arm, task, r["score"], r["steps"], int(r["false_done"])])
print(out)
