"""Automatic failure taxonomy (brief §5) + step-level labels for the direction analysis.

Per step:  repeat = same action as previous step (click < 15 px apart, same text typed, same key)
           AND previous action left the screen ~unchanged (pixel-diff < DIFF_EPS).
Loop rollout = a run of >= 3 identical actions (>= 2 consecutive repeats).
Loop-positive step = the step that emits the repeated action, from the 2nd repetition on
(i.e. the 3rd identical action and beyond). Loop-negative step = a non-repeated action that changed the screen.
"""
import holo.settings as S
import json, math, re
from pathlib import Path

DIFF_EPS = 0.01  # "screen ~unchanged": < 1 % of pixels changed (checkbox toggles ~0.5 %)
CLICK_PX = 15
INTERACTIVE = {"BUTTON", "INPUT", "A", "LABEL", "SELECT", "TEXTAREA", "OPTION", "LI", "SPAN", "SVG", "CIRCLE", "RECT",
               "POLYGON", "TD", "H3", "UL"}


def action_key(s):
    c = s.get("call")
    if not c or "error" in c:
        return None
    return c["name"], c["arguments"]


def same_action(a, b):
    if a is None or b is None or a["call"] is None or b["call"] is None:
        return False
    ca, cb = a["call"], b["call"]
    if ca["name"] != cb["name"] or "error" in ca or "error" in cb:
        return False
    if ca["name"] in ("click", "scroll"):
        if a.get("point") is None or b.get("point") is None:
            return False
        return math.dist(a["point"], b["point"]) < CLICK_PX
    return ca["arguments"] == cb["arguments"]


def load_run(d: Path):
    s = json.loads((d / "summary.json").read_text(encoding="utf-8"))
    steps = [json.loads(l) for l in open(d / "steps.jsonl", encoding="utf-8")] if (d / "steps.jsonl").exists() else []
    return s, steps


SUBMIT_TEXT = {"submit", "login", "log in", "search", "send", "done"}


def is_submit(st):
    """Final 'I'm done' action: click on a submit-like button, or Enter."""
    c = st.get("call") or {}
    if c.get("name") == "press_key" and "enter" in str(c.get("arguments", {}).get("key", "")).lower():
        return True
    h = st.get("hit") or {}
    return c.get("name") == "click" and (h.get("id") in ("subbtn",) or h.get("text", "").strip().lower() in SUBMIT_TEXT)


def label_steps(steps):
    """Returns list of per-step labels: 'loop+' / 'loop-' / None, and the max identical-action run length."""
    labels, run, max_run = [], 1, 1
    for i, st in enumerate(steps):
        lab = None
        if i > 0 and same_action(st, steps[i - 1]) and (steps[i - 1].get("screen_diff") is not None
                                                          and steps[i - 1]["screen_diff"] < DIFF_EPS):
            run += 1
        else:
            run = 1
        max_run = max(max_run, run)
        if run >= 3:
            lab = "loop+"
        elif run == 1 and st.get("screen_diff") is not None and st["screen_diff"] >= DIFF_EPS and st["call"] \
                and st["call"]["name"] != "answer":
            lab = "loop-"
        labels.append(lab)
    return labels, max_run


def classify(s, steps):
    labels, max_run = label_steps(steps)
    loop = max_run >= 3
    success = s["reward"] > 0 and not s["impossible"]
    # False success, two forms (MiniWoB: clicking Submit / the final widget IS the "I'm done" declaration):
    #  - fs_answer: answer("done...") while reward == 0 (or on an impossible task)
    #  - fs_submit: the agent's own action ended the episode with reward 0 (premature / wrong submission)
    fs_answer = s["claimed_done"] and (s["reward"] <= 0 or s["impossible"])
    fs_submit = s["env_done"] and s["reward"] <= 0 and bool(steps) and is_submit(steps[-1])
    false_success = fs_answer or fs_submit
    clicks = [st for st in steps if st.get("call") and st["call"]["name"] == "click" and st.get("hit") is not None]
    miss = [st for st in clicks if (st["hit"] or {}).get("tag", "").upper() not in INTERACTIVE]
    grounding = len(clicks) > 0 and len(miss) / len(clicks) >= 0.5
    if s.get("error"):
        cat = "error"
    elif success:
        cat = "success"
    elif s["impossible"] and s["abandoned"]:
        cat = "correct_abandon"
    elif false_success:
        cat = "false_success"
    elif loop:
        cat = "loop"
    elif grounding:
        cat = "grounding"
    elif s["n_steps"] >= s["max_steps"] or s["abandoned"]:
        cat = "abandon_or_budget"
    elif s["env_done"]:
        cat = "wrong_final_action"   # single-action tasks: episode-ending click on the wrong element
    else:
        cat = "other"
    # step labels for the false-success target: terminal "done" step, wrong (fs+) vs correct (fs-)
    fs_labels = [None] * len(steps)
    if steps and (s["env_done"] or s["claimed_done"]) and not s.get("error"):
        last_is_done = s["claimed_done"] or is_submit(steps[-1])
        if last_is_done:
            fs_labels[-1] = "fs+" if false_success else ("fs-" if s["reward"] > 0 else None)
    return {"category": cat, "loop": loop, "max_run": max_run, "false_success": false_success,
            "fs_answer": fs_answer, "fs_submit": fs_submit, "fs_labels": fs_labels,
            "grounding": grounding, "labels": labels, "success": success}


def scan(tag):
    out = []
    for d in sorted((S.RUNS_DIR / tag).iterdir()):
        if (d / "summary.json").exists():
            s, steps = load_run(d)
            out.append((d, s, steps, classify(s, steps)))
    return out
