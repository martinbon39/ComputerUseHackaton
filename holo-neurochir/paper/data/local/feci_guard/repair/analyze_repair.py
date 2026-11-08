"""Repair measure analysis (protocol in PREREG.md, section "Repair measure").
Usage: python analyze_repair.py ~/osw/feci_repair [--out repair/results.json]
Episodes kept for the primary analysis: every branch of both arms present, no error, replay_valid.
Primary: repaired branches (score 1) per arm; episode-level paired difference of the mean score over K,
bootstrap 95 % CI over episodes (10 000 resamples, seed 0); exact counts.
"""
import argparse, json, random
from collections import defaultdict
from pathlib import Path


def load(p):
    rows = [json.loads(l) for l in open(p) if l.strip()] if Path(p).exists() else []
    by = defaultdict(list)
    for r in rows:
        by[r["task"].split("/pyautogui/screenshot/Holo-3.1-4B/")[-1]].append(r)
    return by


def boot(diffs, n=10000, seed=0):
    rnd, k = random.Random(seed), len(diffs)
    m = sorted(sum(rnd.choice(diffs) for _ in range(k)) / k for _ in range(n))
    return [round(m[int(0.025 * n)], 3), round(m[int(0.975 * n) - 1], 3)]


def arm_stats(rows):
    claimed = [r for r in rows if r.get("finished_by_agent") and not r.get("declined")]
    return {"branches": len(rows), "repaired": sum(r["score"] >= 1 for r in rows),
            "answered_done": len(claimed), "false_success": sum(r["score"] < 1 for r in claimed),
            "no_answer": sum(not r.get("finished_by_agent") for r in rows),
            "declined": sum(bool(r.get("declined")) for r in rows),
            "new_steps_mean": round(sum(r.get("new_steps", 0) for r in rows) / max(1, len(rows)), 2)}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("root")
    ap.add_argument("--k", type=int, default=2)
    ap.add_argument("--out")
    a = ap.parse_args()
    root = Path(a.root).expanduser()
    nog, grd = load(root / "nog" / "branches.jsonl"), load(root / "guard" / "branches.jsonl")
    eps = sorted(set(nog) | set(grd))
    kept, dropped, per = [], {}, {}
    for e in eps:
        rows = nog.get(e, []) + grd.get(e, [])
        why = ("incomplete" if len(nog.get(e, [])) < a.k or len(grd.get(e, [])) < a.k else
               "error" if any("error" in r for r in rows) else
               "replay_invalid" if not all(r.get("replay_valid") for r in rows) else None)
        per[e] = {"nog": [r.get("score") for r in nog.get(e, [])], "guard": [r.get("score") for r in grd.get(e, [])],
                  "guard_decisions": [(r.get("guard") or {}).get("decisions") for r in grd.get(e, [])],
                  "nog_tools": [r.get("tools") for r in nog.get(e, [])], "guard_tools": [r.get("tools") for r in grd.get(e, [])],
                  "replay_diff_max": max([r.get("replay_diff_max") or 0 for r in rows], default=None), "excluded": why}
        (dropped.__setitem__(e, why) if why else kept.append(e))
    N = [r for e in kept for r in nog[e]]
    G = [r for e in kept for r in grd[e]]
    diffs = [sum(r["score"] for r in grd[e]) / len(grd[e]) - sum(r["score"] for r in nog[e]) / len(nog[e]) for e in kept]
    grows = [r for e in kept for r in grd[e]]
    refused = [r for r in grows if (r.get("guard") or {}).get("refusals")]
    rep = {"episodes_total": len(eps), "episodes_kept": len(kept), "dropped": dropped,
           "no_guard": arm_stats(N), "guard": arm_stats(G),
           "paired_diff_mean": round(sum(diffs) / len(diffs), 3) if diffs else None,
           "paired_diff_ci95": boot(diffs) if diffs else None,
           "episodes_guard_better": sum(d > 0 for d in diffs), "episodes_guard_worse": sum(d < 0 for d in diffs),
           "guard_branches_refused": len(refused),
           "guard_refused_then_repaired": sum(r["score"] >= 1 for r in refused),
           "guard_refusals_total": sum((r.get("guard") or {}).get("refusals", 0) for r in grows),
           "guard_verifier_latency_s": [x for r in grows for x in (r.get("guard") or {}).get("verifier_latency_s", []) if x],
           "guard_passed_without_refusal_still_false": sum(1 for r in grows if r.get("finished_by_agent")
                                                           and not (r.get("guard") or {}).get("refusals") and r["score"] < 1),
           "per_episode": per}
    s = json.dumps(rep, indent=1, ensure_ascii=False)
    if a.out:
        Path(a.out).write_text(s)
    print(json.dumps({k: v for k, v in rep.items() if k not in ("per_episode", "guard_verifier_latency_s")}, indent=1))


if __name__ == "__main__":
    main()
