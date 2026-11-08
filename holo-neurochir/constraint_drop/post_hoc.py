"""NOT pre-registered. Adds post-hoc breakdowns to RESULT.json (key 'post_hoc'). Run after analyze.py."""
import json, os
from pathlib import Path
from analyze import wilson, newcombe, fisher_greater

HERE = Path(__file__).parent
H = os.path.expanduser("~/osw")
ROOT = {"modal": f"{H}/results_test_gh_orig_modal_test/pyautogui/screenshot/Holo-3.1-4B-modal-orig",
        "pod": f"{H}/results_test_gh_orig/pyautogui/screenshot/Holo-3.1-4B"}
rows = [json.loads(l) for l in (HERE / "annotations.jsonl").read_text().splitlines()]
for r in rows:
    r["infeasible_task"] = json.load(open(f"{ROOT[r['arm']]}/{r['domain']}/{r['task_id']}/meta.json"))["infeasible_task"]


def cnt(rs, cls):
    s = [r for r in rs if r["cls"] == cls]
    return sum(r["label"] == "yes" for r in s), len(s)


feas = [r for r in rows if not r["infeasible_task"]]
a, n1 = cnt(feas, "FS")
c, n2 = cnt(feas, "TS")
res = json.loads((HERE / "RESULT.json").read_text())
res["post_hoc"] = {
    "FS_on_infeasible_tasks": {"n": sum(r["cls"] == "FS" and r["infeasible_task"] for r in rows),
                                "yes": sum(r["cls"] == "FS" and r["infeasible_task"] and r["label"] == "yes" for r in rows),
                                "note": "agent states the task cannot be done; harness regex missed the answer text, emitted DONE, scored 0"},
    "feasible_tasks_only": {"FS_yes": a, "FS_n": n1, "FS_ci": wilson(a, n1), "TS_yes": c, "TS_n": n2, "TS_ci": wilson(c, n2),
                            "diff": a / n1 - c / n2, "diff_ci": newcombe(a, n1, c, n2),
                            "fisher_p_greater": fisher_greater(a, n1 - a, c, n2 - c)},
    "audit": json.loads((HERE / "audit_results.json").read_text()),
}
(HERE / "RESULT.json").write_text(json.dumps(res, indent=2) + "\n")
print(json.dumps(res["post_hoc"]["FS_on_infeasible_tasks"]), json.dumps(res["post_hoc"]["feasible_tasks_only"]))
