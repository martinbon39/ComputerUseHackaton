#!/usr/bin/env python3
"""Recompute frozen-arm integrity and emit a bounded group diff."""
import argparse
import hashlib
import json
import gzip
from collections import Counter
from pathlib import Path

import jsonschema


ROOT = Path(__file__).resolve().parent


def load_frozen():
    frozen = json.loads((ROOT / "FROZEN.json").read_text())
    schema = json.loads((ROOT / "schema.json").read_text())
    expected = {(c["row"]["task_id"], seed): c for c in frozen["contexts"] for seed in frozen["seeds"]}
    return frozen, schema, expected


def read_arm(arm, frozen, schema, expected):
    path = ROOT / "runs" / arm / "generations.jsonl"
    rows = [json.loads(line) for line in path.read_text().splitlines()]
    assert len(rows) == 220, (arm, len(rows))
    pairs = {(r["row"]["task_id"], r["seed"]): r for r in rows}
    assert len(pairs) == 220
    assert set(pairs) == set(expected)
    counts = {}
    for row in rows:
        key = (row["row"]["task_id"], row["seed"])
        c = expected[key]
        assert row["row"] == c["row"]
        payload = ROOT / "payloads" / f"{c['payload_sha256']}.json.gz"
        blob = gzip.decompress(payload.read_bytes())
        assert hashlib.sha256(blob).hexdigest() == c["payload_sha256"] == row["payload_sha256"]
        parsed = row.get("parsed")
        valid = False
        if parsed is not None:
            try:
                jsonschema.validate(parsed, schema)
                valid = True
            except jsonschema.ValidationError:
                pass
        assert row["schema_valid"] == valid
        assert row["answer"] == (valid and row.get("tool") == "answer")
        assert row["valid_nonanswer"] == (valid and row.get("tool") != "answer")
        label = c["row"]["label"]
        s = counts.setdefault(label, {"n": 0, "answer": 0, "valid_nonanswer": 0, "invalid": 0, "error": 0, "truncated": 0, "tools": Counter()})
        s["n"] += 1
        s["answer"] += int(row["answer"])
        s["valid_nonanswer"] += int(row["valid_nonanswer"])
        s["invalid"] += int(not row["schema_valid"])
        s["error"] += int(bool(row.get("error")))
        s["truncated"] += int(bool(row.get("truncated")))
        s["tools"][row.get("tool")] += 1
    all_rows = [r for r in rows]
    counts["all"] = {"n": len(all_rows), "answer": sum(r["answer"] for r in all_rows),
                      "valid_nonanswer": sum(r["valid_nonanswer"] for r in all_rows),
                      "invalid": sum(not r["schema_valid"] for r in all_rows),
                      "error": sum(bool(r.get("error")) for r in all_rows),
                      "truncated": sum(bool(r.get("truncated")) for r in all_rows),
                      "tools": Counter(r.get("tool") for r in all_rows)}
    for s in counts.values():
        s["tools"] = dict(s["tools"])
    return pairs, counts, hashlib.sha256(path.read_bytes()).hexdigest()


def slim(row):
    parsed = row.get("parsed") or {}
    return {"seed": row["seed"], "answer": row.get("answer"), "tool": row.get("tool"),
            "schema_valid": row.get("schema_valid"), "invalid": row.get("invalid"),
            "error": row.get("error"), "truncated": row.get("truncated"),
            "finish_reason": row.get("finish_reason"), "note": parsed.get("note"),
            "thought": parsed.get("thought"), "tool_call": parsed.get("tool_call"),
            "reasoning": row.get("reasoning")}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("arm")
    ap.add_argument("label", choices=["fs+", "fs-", "healthy"])
    ap.add_argument("output", type=Path)
    args = ap.parse_args()
    frozen, schema, expected = load_frozen()
    base, base_counts, base_sha = read_arm("A", frozen, schema, expected)
    cand, cand_counts, cand_sha = read_arm(args.arm, frozen, schema, expected)
    summary_path = ROOT / "SUMMARY.json"
    summary_check = None
    if summary_path.exists():
        summary = json.loads(summary_path.read_text()).get("arms", {}).get(args.arm, {}).get("summary")
        summary_check = {"present": summary is not None, "matches": summary == cand_counts, "summary": summary, "recomputed": cand_counts}
    contexts = []
    for idx, c in enumerate(frozen["contexts"]):
        if c["row"]["label"] != args.label:
            continue
        task = c["row"]["task_id"]
        seeds = []
        for seed in frozen["seeds"]:
            a, v = base[(task, seed)], cand[(task, seed)]
            seeds.append({"seed": seed, "baseline": slim(a), "candidate": slim(v)})
        contexts.append({"context_index": idx, "task_id": task, "task_suffix": task.rsplit("/", 1)[-1],
                         "label": args.label, "t": c["row"]["t"], "payload_sha256": c["payload_sha256"],
                         "n_images": c.get("n_images"), "last_image": f"image_{c.get('n_images', 0)-1:02d}" if c.get("n_images") else None,
                         "audit_packet": str(ROOT / "audit_packets" / f"{idx:03d}"), "seeds": seeds})
    out = {"scope": f"frozen {args.label} only", "baseline_arm": "A", "candidate_arm": args.arm,
           "seeds": frozen["seeds"], "baseline_sha256": base_sha, "candidate_sha256": cand_sha,
           "baseline_counts": base_counts, "candidate_counts": cand_counts, "summary_check": summary_check,
           "baseline_rows": 220, "candidate_rows": 220, "pairs_exact": True, "contexts": contexts}
    args.output.write_text(json.dumps(out, ensure_ascii=False, indent=2) + "\n")
    print(json.dumps({"output": str(args.output), "contexts": len(contexts), "pairs": len(contexts) * 4,
                      "summary_matches": None if summary_check is None else summary_check["matches"]}))


if __name__ == "__main__":
    main()
