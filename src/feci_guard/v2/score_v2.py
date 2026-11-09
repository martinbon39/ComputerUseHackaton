"""Score verifier variants on a half. Usage: python score_v2.py dev|holdout [variant ...] (v1 = judge_bench responses)."""
import json, math, random, sys
from collections import defaultdict
from pathlib import Path
HERE = Path(__file__).resolve().parent
REPO = Path(__file__).resolve().parents[3]  # repository root
M = {e["episode_id"]: e for e in json.loads((REPO / "experiments/verif_study/manifest.json").read_text())}


def wilson(k, n, z=1.96):
    if not n: return [None, None]
    p = k / n; d = 1 + z * z / n; c = p + z * z / (2 * n); h = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n))
    return [round((c - h) / d, 3), round((c + h) / d, 3)]


def load(variant, half):
    ids = set(json.loads((HERE / "SPLIT.json").read_text())[half])
    p = (REPO / "experiments/judge_bench/claude_responses.jsonl") if variant == "v1" else HERE / "runs" / f"{variant}_{half}.jsonl"
    rows = {}
    for l in open(p):
        j = json.loads(l)
        if j["episode_id"] in ids:
            rows[j["episode_id"]] = j["result"]
    return rows, ids


def score(variant, half, boot=10000):
    rows, ids = load(variant, half)
    inc = {e: r.get("verdict") == "INCOMPLETE" for e, r in rows.items()}
    fs = [e for e in rows if M[e]["label"] == "false_success"]; ts = [e for e in rows if M[e]["label"] == "true_success"]
    d, f = sum(inc[e] for e in fs), sum(inc[e] for e in ts)
    by = defaultdict(list)
    for e in rows: by[(M[e]["domain"], M[e]["task_id"])].append(e)
    tasks = list(by); rnd = random.Random(0); gaps = []
    for _ in range(boot):
        s = [e for t in (rnd.choice(tasks) for _ in tasks) for e in by[t]]
        a = [inc[e] for e in s if M[e]["label"] == "false_success"]; b = [inc[e] for e in s if M[e]["label"] == "true_success"]
        if a and b: gaps.append(sum(a) / len(a) - sum(b) / len(b))
    gaps.sort()
    lat = [r.get("latency_s") for r in rows.values() if r.get("latency_s")]
    return {"variant": variant, "half": half, "n": len(rows), "missing": len(ids) - len(rows),
            "detection": f"{d}/{len(fs)}", "detection_rate": round(d / len(fs), 3) if fs else None, "detection_ci95": wilson(d, len(fs)),
            "false_rejection": f"{f}/{len(ts)}", "false_rejection_rate": round(f / len(ts), 3) if ts else None, "false_rejection_ci95": wilson(f, len(ts)),
            "gap_ci95_task_bootstrap": [round(gaps[int(.025 * len(gaps))], 3), round(gaps[int(.975 * len(gaps)) - 1], 3)] if gaps else None,
            "no_verdict": sum(1 for r in rows.values() if not r.get("verdict")),
            "latency_median_s": sorted(lat)[len(lat) // 2] if lat else None}


if __name__ == "__main__":
    for v in sys.argv[2:] or ["v1"]:
        print(json.dumps(score(v, sys.argv[1])))
