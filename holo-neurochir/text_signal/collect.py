"""Collect feasible answer-terminated episodes (fs = score 0, true success = score 1)."""
import glob
import json
import os
import sys

HOME = os.path.expanduser("~")
BASES = ["osw/results_diag", "osw/results_diag2",
         "osw/results_diag_extra_gh/pass1", "osw/results_diag_extra_gh/pass2"]
EX = f"{HOME}/osw/rtg/Env/OSWorld/evaluation_examples/examples"


def infeasible(domain, tid):
    p = f"{EX}/{domain}/{tid}.json"
    if not os.path.exists(p):
        return None
    ev = json.load(open(p)).get("evaluator", {})
    return "infeasible" in json.dumps(ev.get("func", ""))


def collect():
    eps, seen, audit = [], set(), {"n_result": 0, "partial": 0, "no_traj": 0,
                                   "infeasible": 0, "no_eval": 0, "not_answer": 0,
                                   "dup": 0, "bad_score": 0}
    for b in BASES:
        for r in sorted(glob.glob(f"{HOME}/{b}/**/result.txt", recursive=True)):
            audit["n_result"] += 1
            d = os.path.dirname(r)
            tid, domain = os.path.basename(d), os.path.basename(os.path.dirname(d))
            task = f"{domain}/{tid}"
            try:
                s = float(open(r).read().strip())
            except ValueError:
                audit["bad_score"] += 1
                continue
            if 0 < s < 1:
                audit["partial"] += 1
                continue
            if (task, b) in seen:
                audit["dup"] += 1
                continue
            tp = f"{d}/traj.jsonl"
            if not os.path.exists(tp):
                audit["no_traj"] += 1
                continue
            steps = [json.loads(l) for l in open(tp) if l.strip()]
            if not steps:
                audit["no_traj"] += 1
                continue
            inf = infeasible(domain, tid)
            if inf is None:
                audit["no_eval"] += 1
                continue
            if inf:
                audit["infeasible"] += 1
                continue
            last = steps[-1]
            if last.get("tool_name") != "answer":
                audit["not_answer"] += 1
                continue
            seen.add((task, b))
            eps.append({
                "task": task, "domain": domain, "pass": b, "dir": d, "score": s,
                "y_fs": int(s == 0),
                "final_step": last.get("step_num", len(steps)),
                "n_steps": len(steps),
                "final_note": last.get("note") or "",
                "final_thought": last.get("thought") or "",
                "final_reasoning": last.get("reasoning") or "",
                "final_answer_arg": json.dumps(last.get("tool_call", {}), ensure_ascii=False),
                "last3_notes": " ||| ".join((x.get("note") or "") for x in steps[-3:]),
                "total_reasoning_chars": sum(len(x.get("reasoning") or "") for x in steps),
            })
    return eps, audit


if __name__ == "__main__":
    eps, audit = collect()
    out = os.path.join(os.path.dirname(os.path.abspath(__file__)), "episodes.json")
    json.dump({"audit": audit, "episodes": eps}, open(out, "w"), indent=1, ensure_ascii=False)
    print(audit, len(eps), sum(e["y_fs"] for e in eps), file=sys.stderr)
