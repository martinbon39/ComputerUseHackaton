"""OSWorld failure taxonomy (brief §5 rules, adapted to the RealtimeGUI Holo harness) + step-level labels.

Input: an OSWorld results dir written by RealtimeGUI's run_holo.py; each task dir holds traj.jsonl, step_*.png,
system_prompt.txt, meta.json, result.txt.

Per task, primary category (first match wins), plus independent flags:
  success            score > 0 on a feasible task
  infeasible_correct score > 0 on an officially infeasible task (the agent declined)
  false_success      the agent called `answer` and scored 0: either claimed done (feasible task, or infeasible task
                     answered without declaring it), or wrongly declared a feasible task infeasible (fs_kind)
  loop               >= 3 identical actions in a row with an ~unchanged screen (< 1 % pixels)
  step_limit         max_steps reached without `answer`
  other              anything else (e.g. early stop after repeated harness errors)
Step labels: loop+ (3rd identical action and beyond) / loop- (non-repeated action that changed the screen);
fs+ / fs- on the final `answer` step (answer given wrongly / rightly).
Usage: python -m holo.osw_taxonomy <results_dir> [--max_steps 50] [--out diagnostic_osw]
"""
import holo.settings as S
import argparse, json, math, re
from pathlib import Path
import numpy as np
from PIL import Image

DIFF_EPS = 0.01
CLICK_PX = 15
SCREEN = (1920, 1080)
POINT_TOOLS = ("click", "double_click", "right_click", "scroll", "drag")
# Readable refusal, wider than the harness' scoring regex (fixed 2026-11-07 before any OSWorld AUROC). Scores stay the
# harness' own; this only removes such answers on infeasible tasks from the fs+/fs- labels.
READABLE_DECLINE = re.compile(r"cannot|can't|can not|unable|not (possible|supported|available)|impossible|"
                              r"doesn't support|does not support|no (option|way)", re.IGNORECASE)


def find_tasks(results_dir):
    return sorted(p.parent for p in Path(results_dir).rglob("traj.jsonl"))


def load_task(d: Path):
    steps = [json.loads(l) for l in open(d / "traj.jsonl", encoding="utf-8") if l.strip()]
    meta = json.loads((d / "meta.json").read_text(encoding="utf-8")) if (d / "meta.json").exists() else {}
    score = float((d / "result.txt").read_text().strip()) if (d / "result.txt").exists() else None
    return meta, score, steps


def to_px(x, y):
    return x / 1000 * SCREEN[0], y / 1000 * SCREEN[1]


def same_action(a, b):
    ta, tb = a["tool_call"], b["tool_call"]
    if ta["tool_name"] != tb["tool_name"]:
        return False
    name = ta["tool_name"]
    if name in POINT_TOOLS:
        if math.dist(to_px(ta["x"], ta["y"]), to_px(tb["x"], tb["y"])) >= CLICK_PX:
            return False
        if name == "drag":
            return math.dist(to_px(ta["to_x"], ta["to_y"]), to_px(tb["to_x"], tb["to_y"])) < CLICK_PX
        if name == "scroll":
            return ta["direction"] == tb["direction"]
        return True
    strip = lambda t: {k: v for k, v in t.items() if k not in ("element",)}
    return strip(ta) == strip(tb)


def screen_diffs(d: Path, steps):
    """diff[t] = fraction of pixels changed between the observation of step t and that of step t+1.
    Streams two screenshots at a time (orbit is memory-bound while the OSWorld VMs run)."""
    load = lambda s: np.asarray(Image.open(d / s["screenshot_file"]).convert("RGB")) if s.get("screenshot_file") else None
    out, a = [], load(steps[0]) if steps else None
    for t in range(len(steps)):
        b = load(steps[t + 1]) if t + 1 < len(steps) else None
        out.append(None if a is None or b is None or a.shape != b.shape else
                   float(np.mean((np.abs(a.astype(np.int16) - b.astype(np.int16)) > 8).any(-1))))
        a = b
    return out


def label_steps(steps, diffs):
    labels, run, max_run = [], 1, 1
    for i, st in enumerate(steps):
        lab = None
        if i > 0 and same_action(st, steps[i - 1]) and diffs[i - 1] is not None and diffs[i - 1] < DIFF_EPS:
            run += 1
        else:
            run = 1
        max_run = max(max_run, run)
        if run >= 3:
            lab = "loop+"
        elif run == 1 and diffs[i] is not None and diffs[i] >= DIFF_EPS and st["tool_name"] != "answer":
            lab = "loop-"
        labels.append(lab)
    return labels, max_run


def classify(meta, score, steps, diffs, max_steps):
    labels, max_run = label_steps(steps, diffs)
    infeasible = bool(meta.get("infeasible_task"))
    answered = bool(steps) and steps[-1]["tool_name"] == "answer"
    declined = bool(meta.get("model_declared_infeasible"))
    ok = score is not None and score > 0
    n_act = sum(s["tool_name"] != "answer" for s in steps)
    fs_kind = None
    if answered and not ok:
        fs_kind = "wrong_infeasible" if (declined and not infeasible) else "claimed_done"
    loop = max_run >= 3
    step_limit = not answered and n_act >= max_steps
    if score is None:
        cat = "unscored"
    elif ok:
        cat = "infeasible_correct" if infeasible else "success"
    elif fs_kind:
        cat = "false_success"
    elif loop:
        cat = "loop"
    elif step_limit:
        cat = "step_limit"
    else:
        cat = "other"
    # fs+ = "done" claimed wrongly; fs- = "done" claimed rightly on a feasible task. Declines (right or wrong) are
    # left out so the probe cannot learn "about to decline" instead of "about to falsely claim done".
    fs_labels = [None] * len(steps)
    answer_text = steps[-1]["tool_call"].get("content", "") if answered else ""
    readable_decline = infeasible and bool(READABLE_DECLINE.search(answer_text or ""))
    if answered and score is not None and not declined and not readable_decline:
        if fs_kind == "claimed_done":
            fs_labels[-1] = "fs+"
        elif ok and not infeasible:
            fs_labels[-1] = "fs-"
    return {"category": cat, "loop": loop, "max_run": max_run, "step_limit": step_limit, "fs_kind": fs_kind,
            "infeasible": infeasible, "declined": declined, "readable_decline": readable_decline, "answered": answered, "score": score,
            "n_steps": len(steps), "labels": labels, "fs_labels": fs_labels}


def scan(results_dir, max_steps):
    """[(task_dir, s, steps, c)] with s['task'] = 'domain/example_id' (the CV group). results_dir may be a
    comma-separated list of passes over the same tasks."""
    out = []
    for d in [d for r in str(results_dir).split(",") for d in find_tasks(r)]:
        meta, score, steps = load_task(d)
        if not steps:  # run_holo infra-fail: empty trajectory, never scored
            continue
        diffs = screen_diffs(d, steps)
        c = classify(meta, score, steps, diffs, max_steps)
        c["diffs"] = diffs
        s = {"task": f"{meta.get('domain', d.parent.name)}/{meta.get('example_id', d.name)}", "meta": meta,
             "pass": d.parents[4].name}
        out.append((d, s, steps, c))
    return out


CATS = ["success", "infeasible_correct", "false_success", "loop", "step_limit", "other", "unscored"]
REMOVABLE = ["false_success", "loop", "step_limit"]


def summarize(rows):
    cats = {k: 0 for k in CATS}
    for _, _, _, c in rows:
        cats[c["category"]] += 1
    fails = [c for _, _, _, c in rows if c["category"] not in ("success", "infeasible_correct", "unscored")]
    nf = max(len(fails), 1)
    pos = lambda key, lab: sum(l == lab for _, _, _, c in rows for l in c[key])
    flags = {"loop_any": sum(c["loop"] for c in fails), "step_limit_any": sum(c["step_limit"] for c in fails),
             "fs_claimed_done": sum(c["fs_kind"] == "claimed_done" for c in fails),
             "fs_wrong_infeasible": sum(c["fs_kind"] == "wrong_infeasible" for c in fails)}
    steps_pos = {"loop+": pos("labels", "loop+"), "loop-": pos("labels", "loop-"),
                 "fs+": pos("fs_labels", "fs+"), "fs-": pos("fs_labels", "fs-")}
    share = {"false_success": cats["false_success"] / nf, "loop": flags["loop_any"] / nf,
             "step_limit": flags["step_limit_any"] / nf}
    npos = {"false_success": steps_pos["fs+"], "loop": steps_pos["loop+"],
            # step_limit has no step-level label of its own: its positive steps are the looping ones
            "step_limit": steps_pos["loop+"]}
    go = [k for k in REMOVABLE if share[k] >= 0.25 and npos[k] >= 40]
    return {"n_tasks": len(rows), "n_fail": len(fails), "categories": cats, "fail_flags": flags,
            "share_of_failures": {k: round(v, 3) for k, v in share.items()}, "step_labels": steps_pos,
            "positives_for_rule": npos, "go": go}


def write_report(rows, summ, out_md):
    L = ["# Diagnostic OSWorld — Holo-3.1-4B", "",
         f"{summ['n_tasks']} tâches, {summ['n_fail']} échecs. Règle STOP/GO (brief §5) : GO si une catégorie retirable "
         "≥ 25 % des échecs ET ≥ 40 pas positifs.", "",
         "| catégorie | tâches |", "|---|---|"]
    L += [f"| {k} | {v} |" for k, v in summ["categories"].items()]
    L += ["", "| défaut (dans les échecs) | part | pas positifs |", "|---|---|---|"]
    for k in REMOVABLE:
        L.append(f"| {k} | {100 * summ['share_of_failures'][k]:.0f} % | {summ['positives_for_rule'][k]} |")
    f = summ["fail_flags"]
    L += ["", f"Faux succès : {f['fs_claimed_done']} « terminé » à tort, {f['fs_wrong_infeasible']} « infaisable » à tort. "
          f"Labels de pas : {summ['step_labels']}.", "",
          "## Verdict STOP / GO", "",
          "- " + (("GO " + ", ".join(summ["go"])) if summ["go"] else "NO-GO pour l'instant"), "",
          "## Par tâche", "", "| tâche | passe | score | catégorie | pas | boucle max | answer |", "|---|---|---|---|---|---|---|"]
    for d, s, steps, c in rows:
        ans = (s["meta"].get("answer") or "")[:60].replace("|", "/").replace("\n", " ")
        L.append(f"| {s['task']} | {s['pass']} | {c['score']} | {c['category']} | {c['n_steps']} | {c['max_run']} | {ans} |")
    Path(out_md).write_text("\n".join(L) + "\n", encoding="utf-8")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("results_dir")
    ap.add_argument("--max_steps", type=int, required=True, help="the --max_steps the OSWorld run used")
    ap.add_argument("--out", default=str(S.ROOT / "diagnostic_osw"))
    a = ap.parse_args()
    rows = scan(a.results_dir, a.max_steps)
    summ = summarize(rows)
    import hashlib
    summ["rules_sha1"] = hashlib.sha1(Path(__file__).read_bytes()).hexdigest()[:12]
    summ["results_dir"] = a.results_dir
    summ["tasks"] = [{"task": s["task"], "pass": s["pass"], **{k: v for k, v in c.items() if k != "diffs"}} for _, s, _, c in rows]
    Path(a.out + ".json").write_text(json.dumps(summ, indent=1, ensure_ascii=False), encoding="utf-8")
    write_report(rows, summ, a.out + ".md")
    print(json.dumps({k: v for k, v in summ.items() if k != "tasks"}, indent=1, ensure_ascii=False))


if __name__ == "__main__":
    main()
