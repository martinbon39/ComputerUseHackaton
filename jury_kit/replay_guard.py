#!/usr/bin/env python3
"""Quickstart (b): replay Feci Guard on 268 recorded OSWorld episodes, with the verdicts Claude gave when it ran.

No GPU, no key, no VM, standard library only. The frozen decision code `holo-neurochir/feci_guard/feci_guard.py`
runs unchanged on each episode's real final screenshot (`verif_study/images/`). Only the network call
`verifier.verify` is swapped, in memory, for a lookup of the verdict Claude Sonnet returned on 2026-11-08
(`judge_bench/claude_responses.jsonl`). The script then scores the accept/reject decisions against the official
OSWorld labels (`verif_study/manifest.json`: 66 false successes, 202 true successes) and checks the published numbers.

    python jury_kit/replay_guard.py            # summary + checks, exit 1 on mismatch
    python jury_kit/replay_guard.py --show 3   # also print 3 refusals the agent would receive
"""
import argparse, hashlib, json, math, pathlib, random, sys
sys.dont_write_bytecode = True  # keep a judge's clone clean

ROOT = pathlib.Path(__file__).resolve().parent.parent / "holo-neurochir"
sys.path.insert(0, str(ROOT / "feci_guard"))
import feci_guard  # noqa: E402  (the frozen module; imports verifier)
import verifier  # noqa: E402

EXPECTED = {"detected": 45, "false_success": 66, "wrongly_rejected": 21, "true_success": 202,
            "verifier_sha": "0af76fdb"}


def wilson(k, n, z=1.96):
    p, d = k / n, 1 + z * z / n
    c, h = (p + z * z / 2 / n) / d, z * math.sqrt(p * (1 - p) / n + z * z / 4 / n / n) / d
    return 100 * (c - h), 100 * (c + h)


def gap_ci(rows, n=10000, seed=0):
    """Task-cluster bootstrap of detection rate minus false-rejection rate (episodes of a task move together)."""
    by_task = {}
    for r in rows:
        by_task.setdefault(r["task"], []).append(r)
    tasks, rng, out = list(by_task), random.Random(seed), []
    for _ in range(n):
        s = [e for t in (rng.choice(tasks) for _ in tasks) for e in by_task[t]]
        fs = [e["reject"] for e in s if e["label"] == "false_success"]
        ts = [e["reject"] for e in s if e["label"] == "true_success"]
        if fs and ts:
            out.append(100 * (sum(fs) / len(fs) - sum(ts) / len(ts)))
    out.sort()
    return out[int(0.025 * len(out))], out[int(0.975 * len(out)) - 1]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--show", type=int, default=0, help="print N refusal messages sent back to the agent")
    a = ap.parse_args()

    manifest = json.loads((ROOT / "verif_study" / "manifest.json").read_text())
    recorded = {}
    for line in (ROOT / "judge_bench" / "claude_responses.jsonl").read_text().splitlines():
        if line.strip():
            r = json.loads(line)
            recorded[r["episode_id"]] = r["result"]
    assert set(recorded) == {e["episode_id"] for e in manifest}, "recorded verdicts do not cover the manifest"

    current = {}
    verifier.verify = lambda instruction, image_path, **kw: dict(recorded[current["id"]])

    rows, shown = [], 0
    for e in manifest:
        png = (ROOT / "verif_study" / "images" / pathlib.Path(e["image_path"]).name).read_bytes()
        assert hashlib.sha256(png).hexdigest() == e["screenshot_sha256"], f"screenshot changed: {e['episode_id']}"
        current["id"] = e["episode_id"]
        out = feci_guard.check(e["instruction"], png)
        rows.append({"label": e["label"], "task": (e["domain"], e["task_id"]), "reject": out["verdict"] == "reject",
                     "kind": out["kind"]})
        if out["verdict"] == "reject" and e["label"] == "false_success" and shown < a.show:
            shown += 1
            print(f"--- refusal {shown}: {e['domain']}/{e['task_id'][:8]}\nTASK: {e['instruction']}")
            for q in out["requirements"]:
                print(f"  [{ {'yes': 'v', 'no': 'x'}.get(q['status'], '?') }] {q['text']}: {q['evidence']}")
            print(f"FEEDBACK TO THE AGENT: {out['feedback']}\n")

    fs = [r for r in rows if r["label"] == "false_success"]
    ts = [r for r in rows if r["label"] == "true_success"]
    det, fr = sum(r["reject"] for r in fs), sum(r["reject"] for r in ts)
    kinds = {}
    for r in rows:
        kinds[r["kind"]] = kinds.get(r["kind"], 0) + 1
    lo, hi = wilson(det, len(fs))
    lo2, hi2 = wilson(fr, len(ts))
    glo, ghi = gap_ci(rows)
    print("Feci Guard replay: frozen feci_guard.check on 268 recorded final screens, recorded Claude Sonnet verdicts")
    print(f"  verifier sha {feci_guard.VERIFIER_SHA[:8]}   decision kinds: {kinds}")
    print(f"  false successes rejected (detection) : {det}/{len(fs)} = {100*det/len(fs):.0f} %  Wilson95 [{lo:.0f}-{hi:.0f}]")
    print(f"  true successes rejected (false alarm): {fr}/{len(ts)} = {100*fr/len(ts):.0f} %  Wilson95 [{lo2:.0f}-{hi2:.0f}]")
    print(f"  gap detection - false alarm         : {100*det/len(fs)-100*fr/len(ts):+.0f} pts  task-bootstrap95 [{glo:+.0f}, {ghi:+.0f}]")

    got = {"detected": det, "false_success": len(fs), "wrongly_rejected": fr, "true_success": len(ts),
           "verifier_sha": feci_guard.VERIFIER_SHA[:8]}
    bad = [k for k in EXPECTED if got[k] != EXPECTED[k]]
    for k in EXPECTED:
        print(f"  {'OK ' if k not in bad else 'BAD'} {k}: {got[k]} (expected {EXPECTED[k]})")
    print("Matches the published judge-bench numbers." if not bad else "MISMATCH with the published numbers.")
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
