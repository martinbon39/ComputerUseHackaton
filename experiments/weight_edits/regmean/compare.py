import argparse
import hashlib
import itertools
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent


def read(path):
    records = [json.loads(line) for line in path.read_text().splitlines() if line.strip()]
    assert len(records) == 51
    keyed = {}
    for row in records:
        context = row["row"]
        key = (context.get("task_id", context.get("text_prompt")), context.get("t", -1), row["seed"])
        assert key not in keyed
        keyed[key] = row
    return keyed


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("candidate", default="regmean", nargs="?")
    ap.add_argument("--original", default="original_v2")
    args = ap.parse_args()
    paths = {"original": ROOT / ("evaluation_" + args.original), "candidate": ROOT / ("evaluation_" + args.candidate)}
    data = {arm: read(path / "generations.jsonl") for arm, path in paths.items()}
    plans = {arm: json.loads((path / "plan.json").read_text()) for arm, path in paths.items()}
    assert set(data["original"]) == set(data["candidate"])
    assert plans["original"]["settings"] == plans["candidate"]["settings"]
    assert plans["original"]["schema_sha256"] == plans["candidate"]["schema_sha256"]
    assert plans["original"]["server"]["vllm_version"] == plans["candidate"]["server"]["vllm_version"]
    counts = {}
    differences = {}
    texts = []
    for label in ["fs+", "fs-", "healthy"]:
        counts[label] = {}
        for arm, keyed in data.items():
            records = [r for r in keyed.values() if r["row"].get("label") == label]
            assert len(records) == 16
            counts[label][arm] = dict(n=16, answer=sum(bool(r.get("answer")) for r in records),
                                      valid_nonanswer=sum(bool(r.get("valid_nonanswer")) and bool(r.get("schema_valid")) for r in records),
                                      invalid=sum(not r.get("schema_valid", False) for r in records),
                                      error=sum(bool(r.get("error")) for r in records), truncated=sum(bool(r.get("truncated")) for r in records))
        tasks = sorted({r["row"]["task_id"] for r in data["original"].values() if r["row"].get("label") == label})
        assert len(tasks) == 2
        per_task = {}
        for task in tasks:
            keys = [key for key, r in data["original"].items() if r["row"].get("task_id") == task]
            assert len(keys) == 8
            per_task[task] = 100 * sum(bool(data["original"][key].get("answer")) - bool(data["candidate"][key].get("answer")) for key in keys) / 8
        bootstrap = [sum(values) / 2 for values in itertools.product(per_task.values(), repeat=2)]
        differences[label] = dict(answer_reduction_pp=sum(per_task.values()) / 2, per_task=per_task,
                                  task_bootstrap95=[min(bootstrap), max(bootstrap)], caveat="Only two tasks; the cluster-bootstrap interval has very limited resolution.")
    for key, original in data["original"].items():
        if "text_prompt" in original["row"]:
            candidate = data["candidate"][key]
            texts.append(dict(prompt=original["row"]["text_prompt"], original=original.get("content"), candidate=candidate.get("content"),
                              original_error=original.get("error"), candidate_error=candidate.get("error"),
                              candidate_truncated=candidate.get("truncated")))
    zero_errors = all(not r.get("error") and not r.get("truncated") and ("text_prompt" in r["row"] or r.get("schema_valid")) for r in data["candidate"].values())
    gate = dict(fs_reduction=differences["fs+"]["answer_reduction_pp"] >= 25,
                true_finish_preservation=differences["fs-"]["answer_reduction_pp"] <= 30, zero_invalid_error_truncation=zero_errors)
    result = dict(original=args.original, candidate=args.candidate, counts=counts, differences=differences, quantitative_gate=gate,
                  quantitative_gate_passed=all(gate.values()), text_health="PENDING_INDEPENDENT_REVIEW", texts=texts,
                  files={arm: hashlib.sha256((path / "generations.jsonl").read_bytes()).hexdigest() for arm, path in paths.items()},
                  scope="Held-out DIAG regenerated next actions, not executed OSWorld outcomes")
    (ROOT / (args.candidate + "_comparison.json")).write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps({k: result[k] for k in ["counts", "differences", "quantitative_gate", "quantitative_gate_passed"]}))


if __name__ == "__main__":
    main()
