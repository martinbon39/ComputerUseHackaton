"""Maintainers only: export per-task scores from the raw OSWorld result folders to results/scores.csv."""
import csv, pathlib, sys
OSW = pathlib.Path.home() / "osw"
ARMS = [
    ("merge_cua_b050", "test", "results_test_gh_merge_cua_b050"),
    ("merge_cua_b050", "confirm", "results_confirm_gh_merge_cua_b050"),
    ("orig_modal", "test", "results_test_gh_orig_modal_test"),
    ("orig_modal", "confirm", "results_confirm_gh_orig_modal_confirm"),
    ("orig_pod", "test", "results_test_gh_orig"),
    ("orig_pod", "confirm", "results_confirm_gh_orig_confirm"),
    ("alphaedit_broad_residual_p100", "confirm", "results_confirm_gh_broad_residual_p100"),
    ("expo125", "test", "results_test_gh_expo125"),
]
rows = []
for arm, split, run in ARMS:
    for f in sorted((OSW / run / "pyautogui").rglob("result.txt")):
        parts = f.relative_to(OSW / run / "pyautogui" / "screenshot").parts
        rows.append((arm, split, parts[1], parts[2], float(f.read_text().strip())))
out = pathlib.Path(__file__).resolve().parent.parent / "results" / "scores.csv"
with out.open("w", newline="") as h:
    w = csv.writer(h); w.writerow(["arm", "split", "domain", "task_id", "score"]); w.writerows(rows)
print(len(rows), "rows ->", out)
