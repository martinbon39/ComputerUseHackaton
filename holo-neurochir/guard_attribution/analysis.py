"""Analysis of the guard attribution study, exactly as preregistered in report/PREREG_GUARD_ATTRIBUTION.md.
Committed before any episode of arms A, B, C exists. Python >= 3.9 stdlib only.

Input: the runner's results root, <root>/arm{A,B,C}/seed{s}/pyautogui/screenshot/<model>/<domain>/<task>/
{result.txt, traj.jsonl, meta.json}, and <root>/ledger.jsonl (attempts, reruns). Moved-aside dead attempts
(<task>.dead1) are ignored.

Episode outcomes (as in online_guard_analysis.py load()):
  false_done     last tool of traj.jsonl is `answer` and score == 0
  never_answered no `answer` tool call in traj.jsonl
  step_cap       the loop's step counter reached 50 (meta.json "steps"; traj.jsonl line count if meta.json is
                 missing). traj.jsonl also holds the accepted answer, so its line count overstates by one.
A (task, seed) is valid only if all three arms have a scored episode (result.txt); otherwise it is dropped from all
three arms for that seed (prereg "Exclusions and reruns") and listed.

Primary: per task, the false-"done" rate averaged over its valid seeds in C and in B; paired difference C - B over the
tasks; bootstrap over tasks, 10,000 draws, seed 0 (random.Random, the boot() of online_guard_analysis.py), 95 %
percentile interval. The guard reduces false "done" only if the upper bound is < 0.
Secondaries 1-6 as numbered in the prereg.

Usage: python3 analysis.py --results DIR [--out result.json] [--md result.md]
"""
from __future__ import annotations

import argparse
import glob
import json
import os
import random

ARMS = ("A", "B", "C")
STEP_CAP = 50
N_BOOT = 10000
BOOT_SEED = 0


def boot(diffs: list[float], n: int = N_BOOT, seed: int = BOOT_SEED) -> tuple[float, float]:
    """Percentile bootstrap of the mean; identical to online_guard_analysis.py boot()."""
    rng = random.Random(seed)
    k = len(diffs)
    means = sorted(sum(diffs[rng.randrange(k)] for _ in range(k)) / k for _ in range(n))
    return means[int(0.025 * n)], means[int(0.975 * n) - 1]


def read_episode(d: str) -> dict | None:
    rp = os.path.join(d, "result.txt")
    if not os.path.exists(rp):
        return None
    try:
        score = float(open(rp).read().strip() or 0)
    except ValueError:
        score = 0.0
    actions = []
    tj = os.path.join(d, "traj.jsonl")
    if os.path.exists(tj):
        for line in open(tj, encoding="utf-8"):
            try:
                rec = json.loads(line)
            except json.JSONDecodeError:
                continue
            actions.append({"tool_name": rec.get("tool_name", "") or "", "tool_call": rec.get("tool_call")})
    last = next((a["tool_name"] for a in reversed(actions) if a["tool_name"]), "")
    meta = {}
    mp = os.path.join(d, "meta.json")
    if os.path.exists(mp):
        try:
            meta = json.load(open(mp))
        except json.JSONDecodeError:
            pass
    loop_steps = meta.get("steps") if isinstance(meta.get("steps"), int) else len(actions)
    guard = []
    gp = os.path.join(d, "guard.jsonl")
    if os.path.exists(gp):
        guard = [json.loads(x) for x in open(gp, encoding="utf-8") if x.strip()]
    failed = 0
    sp = os.path.join(d, "seeds.jsonl")
    if os.path.exists(sp):
        failed = sum(1 for x in open(sp) if '"failed"' in x)
    return {"score": score, "steps": len(actions), "loop_steps": loop_steps,
            "verifier_latency_s": (meta.get("feci_guard") or {}).get("verifier_latency_s") or [],
            "guard_decisions": [g.get("decision") for g in guard],
            "verifier_errors": sum(1 for g in guard if (g.get("verifier") or {}).get("error")),
            "ended_on_refused_answer": bool(guard) and guard[-1].get("decision") == "refused" and last == "answer",
            "model_request_failures": failed, "false_done": last == "answer" and score == 0,
            "never_answered": not any(a["tool_name"] == "answer" for a in actions),
            "step_cap": loop_steps >= STEP_CAP, "actions": actions}


def load(root: str) -> dict:
    """{(arm, seed, task): episode}. task = '<domain>/<id>'."""
    out = {}
    for arm in ARMS:
        for sd in glob.glob(os.path.join(root, f"arm{arm}", "seed*")):
            seed = int(os.path.basename(sd)[4:])
            for d in glob.glob(os.path.join(sd, "pyautogui", "screenshot", "*", "*", "*")):
                if not os.path.isdir(d) or ".dead" in os.path.basename(d):
                    continue
                ep = read_episode(d)
                if ep is not None:
                    out[(arm, seed, "/".join(d.split(os.sep)[-2:]))] = ep
    return out


def ledger_events(root: str) -> dict:
    p = os.path.join(root, "ledger.jsonl")
    if not os.path.exists(p):
        return {"reruns": [], "dead_attempts": []}
    rows = [json.loads(x) for x in open(p)]
    att = [r for r in rows if r.get("kind") == "attempt"]
    return {"reruns": [f"arm{r['arm']} seed{r['seed']} {r['domain']}/{r['task']} -> "
                       f"{'dead' if r['dead'] else 'scored'}" for r in att if r["attempt"] > 1],
            "dead_attempts": [f"arm{r['arm']} seed{r['seed']} {r['domain']}/{r['task']} attempt {r['attempt']}"
                              f" ({r.get('error') or '0 steps'})" for r in att if r["dead"]],
            "stops": [r for r in rows if r.get("kind") == "stop"]}


def valid_pairs(eps: dict, tasks: list[str] | None, seeds: list[int]) -> tuple[dict, list[str]]:
    """{task: [seeds valid in all three arms]} and the list of dropped (task, seed)."""
    tasks = tasks or sorted({k[2] for k in eps})
    valid, dropped = {}, []
    for t in tasks:
        for s in seeds:
            if all((a, s, t) in eps for a in ARMS):
                valid.setdefault(t, []).append(s)
            else:
                dropped.append(f"{t} seed{s} (missing: {','.join(a for a in ARMS if (a, s, t) not in eps)})")
    return valid, dropped


def paired(eps, valid, x: str, y: str, field: str, tasks=None) -> dict:
    """Per task, mean over valid seeds of field in arm x minus arm y; mean and bootstrap CI over tasks."""
    ts = [t for t in (tasks if tasks is not None else sorted(valid)) if valid.get(t)]
    if not ts:
        return {"n_tasks": 0}
    mx = [sum(float(eps[(x, s, t)][field]) for s in valid[t]) / len(valid[t]) for t in ts]
    my = [sum(float(eps[(y, s, t)][field]) for s in valid[t]) / len(valid[t]) for t in ts]
    d = [a - b for a, b in zip(mx, my)]
    lo, hi = boot(d)
    return {"n_tasks": len(ts), f"{field}_{x}": sum(mx) / len(ts), f"{field}_{y}": sum(my) / len(ts),
            "diff": sum(d) / len(ts), "ci95": [lo, hi], "diff_label": f"{x} - {y}"}


def first_answer_prefix(actions: list[dict]) -> list:
    out = []
    for a in actions:
        out.append(a["tool_call"])
        if a["tool_name"] == "answer":
            break
    return out


def analyse(root: str, tasks: list[str] | None = None, seeds: list[int] | None = None) -> dict:
    eps = load(root)
    seeds = seeds or sorted({k[1] for k in eps})
    valid, dropped = valid_pairs(eps, tasks, seeds)
    pairs = [(t, s) for t in sorted(valid) for s in valid[t]]

    primary = paired(eps, valid, "C", "B", "false_done")
    primary["guard_reduces_false_done"] = bool(primary.get("n_tasks")) and primary["ci95"][1] < 0

    s1 = paired(eps, valid, "B", "A", "false_done")
    s2 = paired(eps, valid, "C", "B", "score")
    s2["score_gain_claimed"] = bool(s2.get("n_tasks")) and s2["ci95"][0] > 0

    same = [first_answer_prefix(eps[("A", s, t)]["actions"]) == first_answer_prefix(eps[("B", s, t)]["actions"])
            for t, s in pairs]
    s3 = {"pairs": len(same), "identical_until_first_answer": sum(same),
          "share": sum(same) / len(same) if same else None}

    rates = {}
    for a in ARMS:
        e = [eps[(a, s, t)] for t, s in pairs]
        rates[a] = {"episodes": len(e), "never_answered": sum(x["never_answered"] for x in e),
                    "step_cap": sum(x["step_cap"] for x in e), "false_done": sum(x["false_done"] for x in e),
                    "never_answered_rate": sum(x["never_answered"] for x in e) / max(len(e), 1),
                    "step_cap_rate": sum(x["step_cap"] for x in e) / max(len(e), 1)}
    answered_c = [t for t in sorted(valid) if all(not eps[("C", s, t)]["never_answered"] for s in valid[t])]
    s4 = {"rates": rates, "primary_on_tasks_where_C_answered_every_seed": {
        **paired(eps, valid, "C", "B", "false_done", tasks=answered_c),
        "note": "descriptive only; the subset is post-treatment"}}

    b_rep = sum(1 for t, s in pairs if eps[("B", s, t)]["score"] < 1 <= eps[("C", s, t)]["score"])
    c_lost = sum(1 for t, s in pairs if eps[("C", s, t)]["score"] < 1 <= eps[("B", s, t)]["score"])
    avoided = sum(1 for t, s in pairs if eps[("B", s, t)]["false_done"] and not eps[("C", s, t)]["false_done"])
    added = sum(1 for t, s in pairs if eps[("C", s, t)]["false_done"] and not eps[("B", s, t)]["false_done"])
    s5 = {"pairs": len(pairs), "B_rep_score_0_to_1": b_rep, "C_lost_score_1_to_0": c_lost, "net_B_rep_minus_C_lost":
          b_rep - c_lost, "false_done_avoided": avoided, "false_done_added": added,
          "rule5_useful": (b_rep - c_lost) >= 0 and primary["guard_reduces_false_done"]}

    s6 = {}
    for s in seeds:
        vs = {t: [s] for t in valid if s in valid[t]}
        s6[f"seed{s}"] = paired(eps, vs, "C", "B", "false_done")

    lat = {}
    for a in ("B", "C"):
        v = sorted(x for t, s in pairs for x in eps[(a, s, t)]["verifier_latency_s"] if x is not None)
        lat[a] = {"n": len(v), "median": v[len(v) // 2] if v else None, "p90": v[int(0.9 * len(v))] if v else None}
    health = {}
    for a in ARMS:
        e = [eps[(a, s, t)] for t, s in pairs]
        dec = [x for ep in e for x in ep["guard_decisions"]]
        health[a] = {"verifier_decisions": {k: dec.count(k) for k in sorted(set(dec))},
                     "verifier_errors": sum(ep["verifier_errors"] for ep in e),
                     "episodes_ending_on_refused_answer": sum(ep["ended_on_refused_answer"] for ep in e),
                     "episodes_with_failed_model_requests": sum(1 for ep in e if ep["model_request_failures"]),
                     "failed_model_requests": sum(ep["model_request_failures"] for ep in e)}
    checks = {"note": "not preregistered; checks that B differs from C only by the verdict, that C's verifier "
                      "answered (a failing verifier passes every answer, which turns C into B), and model outages",
              "verifier_latency_s": lat, "health": health}

    return {"prereg": "holo-neurochir/report/PREREG_GUARD_ATTRIBUTION.md", "seeds": seeds,
            "n_tasks_valid": len(valid), "n_pairs_valid": len(pairs), "dropped_task_seed": dropped,
            "ledger": ledger_events(root), "primary_C_minus_B_false_done": primary,
            "s1_B_minus_A_false_done": s1, "s2_C_minus_B_score": s2, "s3_seed_fidelity_A_vs_B": s3,
            "s4_never_answered_step_cap": s4, "s5_benefit_cost_C_vs_B": s5, "s6_per_seed_primary": s6,
            "checks_not_preregistered": checks}


def pct(x):
    return "n/a" if x is None else f"{100 * x:+.1f}"


def markdown(r: dict) -> str:
    p = r["primary_C_minus_B_false_done"]
    lines = ["# Guard attribution study: result (generated by guard_attribution/analysis.py)", "",
             f"Valid tasks: {r['n_tasks_valid']}; valid (task, seed) pairs: {r['n_pairs_valid']}; "
             f"dropped: {len(r['dropped_task_seed'])}; reruns: {len(r['ledger']['reruns'])}.", ""]
    if p.get("n_tasks"):
        lines += [f"**Primary (C - B, false done):** {pct(p['diff'])} pts, 95 % CI [{pct(p['ci95'][0])}, "
                  f"{pct(p['ci95'][1])}] over {p['n_tasks']} tasks. Criterion (upper bound < 0): "
                  f"{'MET' if p['guard_reduces_false_done'] else 'NOT MET'}.", ""]
    for key, label in (("s1_B_minus_A_false_done", "S1 B - A, false done"), ("s2_C_minus_B_score", "S2 C - B, score")):
        x = r[key]
        if x.get("n_tasks"):
            lines.append(f"- {label}: {pct(x['diff'])} pts [{pct(x['ci95'][0])}, {pct(x['ci95'][1])}]")
    s3 = r["s3_seed_fidelity_A_vs_B"]
    lines.append(f"- S3 seed fidelity: {s3['identical_until_first_answer']}/{s3['pairs']} (task, seed) pairs with "
                 f"identical A and B actions up to the first answer")
    for a, x in r["s4_never_answered_step_cap"]["rates"].items():
        lines.append(f"- S4 arm {a}: never answered {x['never_answered']}/{x['episodes']}, step cap "
                     f"{x['step_cap']}/{x['episodes']}, false done {x['false_done']}/{x['episodes']}")
    s5 = r["s5_benefit_cost_C_vs_B"]
    lines.append(f"- S5 C vs B per (task, seed): B_rep {s5['B_rep_score_0_to_1']}, C_lost {s5['C_lost_score_1_to_0']}, "
                 f"false done avoided {s5['false_done_avoided']}, added {s5['false_done_added']}")
    for s, x in r["s6_per_seed_primary"].items():
        if x.get("n_tasks"):
            lines.append(f"- S6 {s}: {pct(x['diff'])} pts [{pct(x['ci95'][0])}, {pct(x['ci95'][1])}]")
    h = r["checks_not_preregistered"]["health"]["C"]
    lines.append(f"- Check (not preregistered), arm C verifier: decisions {h['verifier_decisions']}, errors "
                 f"{h['verifier_errors']}; episodes ending on a refused answer {h['episodes_ending_on_refused_answer']}")
    if r["dropped_task_seed"]:
        lines += ["", "Dropped (task, seed): " + "; ".join(r["dropped_task_seed"])]
    return "\n".join(lines) + "\n"


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--results", required=True)
    ap.add_argument("--tasks", default=os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                                                    "osworld", "split_test.json"),
                    help="split json (default: the 120 TEST tasks); a task with no valid seed is listed as dropped")
    ap.add_argument("--seeds", default="0,1,2")
    ap.add_argument("--out", default=None)
    ap.add_argument("--md", default=None)
    a = ap.parse_args()
    m = json.load(open(a.tasks))
    tasks = [f"{d}/{t}" for d in m for t in m[d]]
    r = analyse(a.results, tasks, [int(s) for s in a.seeds.split(",")])
    js = json.dumps(r, indent=1)
    if a.out:
        open(a.out, "w").write(js)
    if a.md:
        open(a.md, "w").write(markdown(r))
    print(markdown(r))
