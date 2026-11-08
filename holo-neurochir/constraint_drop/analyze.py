"""Statistics from annotations.jsonl, as fixed in PROTOCOL.md. Python stdlib only."""
import json, math, random
from collections import defaultdict
from pathlib import Path

HERE = Path(__file__).parent
rows = [json.loads(l) for l in (HERE / "annotations.jsonl").read_text().splitlines() if l.strip()]
Z = 1.959963984540054


def wilson(k, n):
    if n == 0:
        return [None, None]
    p = k / n
    d = 1 + Z * Z / n
    c = (p + Z * Z / (2 * n)) / d
    h = Z * math.sqrt(p * (1 - p) / n + Z * Z / (4 * n * n)) / d
    return [c - h, c + h]


def newcombe(k1, n1, k2, n2):
    l1, u1 = wilson(k1, n1)
    l2, u2 = wilson(k2, n2)
    p1, p2 = k1 / n1, k2 / n2
    return [p1 - p2 - math.sqrt((p1 - l1) ** 2 + (u2 - p2) ** 2), p1 - p2 + math.sqrt((u1 - p1) ** 2 + (p2 - l2) ** 2)]


def fisher_greater(a, b, c, d):
    """P(X >= a) under the hypergeometric, table [[a,b],[c,d]], rows FS/TS, cols yes/no."""
    n1, k, n = a + b, a + c, a + b + c + d
    tot = math.comb(n, k)
    return sum(math.comb(n1, x) * math.comb(n - n1, k - x) for x in range(a, min(n1, k) + 1)) / tot


def block(rs):
    fs = [r for r in rs if r["cls"] == "FS"]
    ts = [r for r in rs if r["cls"] == "TS"]
    a = sum(r["label"] == "yes" for r in fs)
    c = sum(r["label"] == "yes" for r in ts)
    out = {"FS_yes": a, "FS_n": len(fs), "TS_yes": c, "TS_n": len(ts)}
    if fs and ts:
        out.update(FS_rate=a / len(fs), FS_ci=wilson(a, len(fs)), TS_rate=c / len(ts), TS_ci=wilson(c, len(ts)),
                   diff=a / len(fs) - c / len(ts), diff_ci=newcombe(a, len(fs), c, len(ts)),
                   fisher_p_greater=fisher_greater(a, len(fs) - a, c, len(ts) - c))
    return out


valid = [r for r in rows if r["label"] in ("yes", "no")]
res = {"n_rows": len(rows), "n_unparseable": len(rows) - len(valid), "primary": block(valid),
       "by_arm": {arm: block([r for r in valid if r["arm"] == arm]) for arm in ("modal", "pod")},
       "not_declared_infeasible": block([r for r in valid if not r["declared_infeasible"]])}
p = res["primary"]
res["H1_holds"] = bool(p.get("fisher_p_greater", 1) < 0.05 and p.get("diff_ci", [0])[0] > 0)
yes = [r for r in valid if r["label"] == "yes"]
res["quote_in_text"] = {"yes_total": len(yes), "quote_found": sum(r["quote_in_text"] for r in yes)}
res["self_check_guard"] = {"recall_FS": p["FS_yes"] / p["FS_n"], "recall_ci": wilson(p["FS_yes"], p["FS_n"]),
                           "false_reject_TS": p["TS_yes"] / p["TS_n"], "false_reject_ci": wilson(p["TS_yes"], p["TS_n"]),
                           "precision": (p["FS_yes"] / len(yes)) if yes else None,
                           "external_guard_ref": {"detection": "45/66 = 0.68", "false_reject": "21/202 = 0.10"}}
bytask = defaultdict(list)
for r in valid:
    bytask[(r["domain"], r["task_id"])].append(r)
keys = sorted(bytask)
rng = random.Random(20261108)
diffs = []
for _ in range(2000):
    s = [r for k in (rng.choice(keys) for _ in keys) for r in bytask[k]]
    fs = [r for r in s if r["cls"] == "FS"]
    ts = [r for r in s if r["cls"] == "TS"]
    if fs and ts:
        diffs.append(sum(r["label"] == "yes" for r in fs) / len(fs) - sum(r["label"] == "yes" for r in ts) / len(ts))
diffs.sort()
res["task_cluster_bootstrap_diff_ci"] = [diffs[int(0.025 * len(diffs))], diffs[int(0.975 * len(diffs)) - 1]]
(HERE / "RESULT.json").write_text(json.dumps(res, indent=2) + "\n")
print(json.dumps(res, indent=2))
