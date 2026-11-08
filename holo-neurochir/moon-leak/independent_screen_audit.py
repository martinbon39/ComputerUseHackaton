#!/usr/bin/env python3
import os

os.environ.update(OMP_NUM_THREADS="2", MKL_NUM_THREADS="2", OPENBLAS_NUM_THREADS="2")

import argparse
import collections
import gzip
import hashlib
import json
import re
from pathlib import Path

import jsonschema
import numpy as np

DEFAULT_ROOT = Path("/workspace/astra/moon-leak")
DEFAULT_POWER = Path("/workspace/astra/astra-power")
EXPECTED_CONTEXT_COUNTS = {"fs+": 19, "fs-": 20, "healthy": 16}
ORIGINAL_ROOT = "/workspace/hf/hub/models--Hcompany--Holo-3.1-4B/snapshots/8c88265a5a159bfd1492db9243733dd2e6e04a6e"
TEXT_IDS = {"translation_fr_en", "arithmetic_17x19", "linux_rename_three_steps"}
OUTPUT_FIELDS = [
    "prompt_id",
    "prompt",
    "seed",
    "reasoning",
    "content",
    "text",
    "token_ids",
    "n_out",
    "finish_reason",
    "stop_reason",
    "truncated",
    "error",
]


class AuditError(RuntimeError):
    pass


def require(condition, message):
    if not condition:
        raise AuditError(message)


def digest_bytes(value):
    return hashlib.sha256(value).hexdigest()


def digest(path):
    return digest_bytes(path.read_bytes())


def load_json(path):
    return json.loads(path.read_text())


def load_jsonl(path):
    require(path.is_file(), f"missing JSONL: {path}")
    try:
        return [json.loads(line) for line in path.read_text().splitlines() if line.strip()]
    except json.JSONDecodeError as exc:
        raise AuditError(f"invalid JSONL in {path}: {exc}") from exc


def atomic_json(path, value):
    temporary = path.with_name(f".{path.name}.{os.getpid()}.tmp")
    temporary.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n")
    os.replace(temporary, path)


def load_frozen(power):
    frozen_path = power / "FROZEN.json"
    schema_path = power / "schema.json"
    manifest_path = power / "cohort/manifest.json"
    frozen_bytes = frozen_path.read_bytes()
    frozen = json.loads(frozen_bytes)
    schema = load_json(schema_path)
    manifest = load_json(manifest_path)
    schema_sha = digest_bytes(json.dumps(schema, sort_keys=True).encode())
    require(schema_sha == frozen["schema_sha256"], "canonical schema hash differs from FROZEN")
    require(digest(manifest_path) == frozen["cohort_sha256"], "manifest hash differs from FROZEN")
    contexts = frozen["contexts"]
    require(manifest["train"] == [context["row"] for context in contexts], "manifest rows differ from FROZEN")
    require(manifest["seeds"] == frozen["seeds"], "manifest seeds differ from FROZEN")
    counts = collections.Counter(context["row"]["label"] for context in contexts)
    require(dict(counts) == EXPECTED_CONTEXT_COUNTS, f"unexpected cohort counts: {dict(counts)}")
    require(len({context["row"]["task_id"] for context in contexts}) == len(contexts) == 55, "task IDs are not 55 unique values")
    for context in contexts:
        payload_sha = context["payload_sha256"]
        payload = gzip.decompress((power / "payloads" / f"{payload_sha}.json.gz").read_bytes())
        require(digest_bytes(payload) == payload_sha, f"payload bytes differ: {payload_sha}")
        json.loads(payload)
    return frozen_bytes, frozen, schema, manifest


def derive_generation(value, schema):
    parsed = None
    tool = None
    valid = False
    if not value.get("error"):
        try:
            parsed = json.loads(value.get("content", ""))
            tool = parsed["tool_call"]["tool_name"]
        except (json.JSONDecodeError, KeyError, TypeError):
            parsed = None
            tool = None
        if parsed is not None:
            try:
                jsonschema.validate(parsed, schema)
                valid = True
            except jsonschema.ValidationError:
                pass
    derived = {
        "parsed": parsed,
        "tool": tool,
        "schema_valid": valid,
        "invalid": not valid,
        "answer": valid and tool == "answer",
        "valid_nonanswer": valid and tool != "answer",
    }
    for field, expected in derived.items():
        require(value.get(field) == expected, f"stored {field} disagrees with reconstructed value")
    return derived


def generation_table(rows, contexts, seeds, schema, provenance):
    expected = {(task_id, seed) for task_id in contexts for seed in seeds}
    table = {}
    counters = collections.Counter()
    for value in rows:
        task_id = value.get("row", {}).get("task_id")
        key = (task_id, value.get("seed"))
        require(key in expected and key not in table, f"unexpected or duplicate generation key: {key}")
        context = contexts[task_id]
        require(value["row"] == context["row"], f"frozen row mismatch: {key}")
        require(value["payload_sha256"] == context["payload_sha256"], f"payload hash mismatch: {key}")
        for field, expected_value in provenance.items():
            require(value.get(field) == expected_value, f"{field} provenance mismatch: {key}")
        derived = derive_generation(value, schema)
        counters["schema_valid"] += derived["schema_valid"]
        counters["answer"] += derived["answer"]
        counters["valid_nonanswer"] += derived["valid_nonanswer"]
        counters["invalid"] += derived["invalid"]
        counters["errors"] += bool(value.get("error"))
        counters["truncated"] += bool(value.get("truncated"))
        table[key] = {**value, **derived}
    require(set(table) == expected, f"generation keys incomplete: {len(table)}/{len(expected)}")
    return table, dict(counters)


def receipt_audit(root, arm, run_spec, generation_path, text_path):
    receipts = root / "runs" / arm / "receipts"
    starts = {path.name.removeprefix("start_").removesuffix(".json"): load_json(path) for path in receipts.glob("start_*.json")}
    ends = {path.name.removeprefix("end_").removesuffix(".json"): load_json(path) for path in receipts.glob("end_*.json")}
    require(starts and ends, "missing start/end receipts")
    expected_server = {
        "url": run_spec["url"],
        "vllm_version": "0.23.0",
        "models": [{"id": run_spec["model"], "root": run_spec["checkpoint"]}],
    }
    for invocation, start in starts.items():
        require(start["spec"] == run_spec, f"start receipt spec mismatch: {invocation}")
        require(start["server"] == expected_server, f"server provenance mismatch: {invocation}")
    complete = []
    for invocation, end in ends.items():
        require(invocation in starts, f"end receipt has no matching start: {invocation}")
        if end.get("status") == "COMPLETE":
            require(end["gui_completed"] == end["gui_expected"] == 220, "complete receipt GUI count mismatch")
            require(end["text_controls_completed"] == end["text_controls_expected"] == 3, "complete receipt text count mismatch")
            if end.get("generations_sha256") == digest(generation_path) and end.get("text_controls_sha256") == digest(text_path):
                complete.append(invocation)
    require(complete, "no COMPLETE receipt matches current generation and text files")
    return {"invocations": sorted(starts), "matching_complete_invocations": sorted(complete), "server": expected_server}


def baseline_receipt_audit(receipt_dir, frozen_sha):
    starts = list(receipt_dir.glob("start_*.json"))
    completes = list(receipt_dir.glob("complete_*.json"))
    require(starts and completes, f"missing A start/complete receipt in {receipt_dir}")
    expected_server = {
        "model": "power_A",
        "vllm_version": "0.23.0",
        "models": [{"id": "power_A", "root": ORIGINAL_ROOT}],
    }
    valid_complete = []
    for path in starts:
        value = load_json(path)
        require(value["arm"] == "A" and value["frozen_sha256"] == frozen_sha, f"A start provenance mismatch: {path.name}")
        require(value["scheduled"] + value["previously_completed"] == 220, f"A start count mismatch: {path.name}")
        require(value["max_retries"] == 0 and value["workers"] == 8, f"A request policy mismatch: {path.name}")
        for field, expected in expected_server.items():
            require(value["server"][field] == expected, f"A server {field} mismatch: {path.name}")
    for path in completes:
        value = load_json(path)
        require(value["arm"] == "A" and value["frozen_sha256"] == frozen_sha, f"A completion provenance mismatch: {path.name}")
        require(value["completed"] + value["previously_completed"] == 220, f"A completion count mismatch: {path.name}")
        for field, expected in expected_server.items():
            require(value["server"][field] == expected, f"A completion server {field} mismatch: {path.name}")
        valid_complete.append(path.name)
    return {"directory": str(receipt_dir), "complete_receipts": sorted(valid_complete), "server": expected_server}


def text_table(path):
    values = load_jsonl(path)
    require(len(values) == 3, f"expected three text controls in {path}")
    table = {value.get("prompt_id"): value for value in values}
    require(set(table) == TEXT_IDS and len(table) == len(values), f"text IDs differ in {path}")
    return table


def text_audit(candidate_path, baseline_path, run_spec):
    candidate = text_table(candidate_path)
    baseline = text_table(baseline_path)
    prompts = {item["id"]: item["prompt"] for item in run_spec["text_prompts"]}
    require(set(prompts) == TEXT_IDS, "run_spec text prompts differ")
    comparisons = {}
    for prompt_id in sorted(TEXT_IDS):
        cand = candidate[prompt_id]
        base = baseline[prompt_id]
        require(cand["kind"] == "text_control", f"candidate text kind mismatch: {prompt_id}")
        require(cand["arm"] == run_spec["arm"] and cand["model"] == run_spec["model"], f"candidate text model mismatch: {prompt_id}")
        require(cand["checkpoint"] == run_spec["checkpoint"], f"candidate text checkpoint mismatch: {prompt_id}")
        require(cand["frozen_sha256"] == run_spec["frozen_sha256"], f"candidate text freeze mismatch: {prompt_id}")
        require(base["model"] == "moon_leak_Atext", f"A text model mismatch: {prompt_id}")
        require(
            base["server"]
            == {
                "url": "http://127.0.0.1:8030/v1",
                "vllm_version": "0.23.0",
                "models": [{"id": "moon_leak_Atext", "root": ORIGINAL_ROOT}],
            },
            f"A text server provenance mismatch: {prompt_id}",
        )
        for value in (cand, base):
            require(value["prompt"] == prompts[prompt_id] and value["seed"] == 0, f"text prompt/seed mismatch: {prompt_id}")
            require(not value.get("error") and not value.get("truncated"), f"text request failed: {prompt_id}")
        differences = [field for field in OUTPUT_FIELDS if cand.get(field) != base.get(field)]
        comparisons[prompt_id] = {
            "identical_output": not differences,
            "different_fields": differences,
            "A": base["content"],
            "candidate": cand["content"],
        }
    return comparisons


def interval(draws):
    return np.quantile(draws, [0.025, 0.975]).tolist()


def bootstrap_metrics(baseline, candidate, contexts, seeds, replicates, seed):
    rng = np.random.default_rng(seed)
    metrics = {}
    draws = {}
    counts = {}
    for label in ["fs+", "fs-", "healthy"]:
        tasks = [task_id for task_id, context in contexts.items() if context["row"]["label"] == label]
        indices = rng.integers(0, len(tasks), size=(replicates, len(tasks)))
        counts[label] = {}
        fields = ["answer"] + (["valid_nonanswer"] if label == "healthy" else [])
        for field in fields:
            base_rates = np.array([np.mean([int(baseline[task_id, value][field]) for value in seeds]) for task_id in tasks])
            candidate_rates = np.array([np.mean([int(candidate[task_id, value][field]) for value in seeds]) for task_id in tasks])
            deltas = candidate_rates - base_rates
            sampled = deltas[indices].mean(axis=1)
            draws[label, field] = sampled
            base_count = sum(baseline[task_id, value][field] for task_id in tasks for value in seeds)
            candidate_count = sum(candidate[task_id, value][field] for task_id in tasks for value in seeds)
            metrics[f"{label}:{field}"] = {
                "tasks": len(tasks),
                "samples": len(tasks) * len(seeds),
                "A_count": base_count,
                "candidate_count": candidate_count,
                "A_rate": float(base_rates.mean()),
                "candidate_rate": float(candidate_rates.mean()),
                "candidate_minus_A": float(deltas.mean()),
                "task_bootstrap95": interval(sampled),
            }
        for name, table in [("A", baseline), ("candidate", candidate)]:
            rows = [table[task_id, value] for task_id in tasks for value in seeds]
            counts[label][name] = {
                "n": len(rows),
                "schema_valid": sum(row["schema_valid"] for row in rows),
                "answer": sum(row["answer"] for row in rows),
                "valid_nonanswer": sum(row["valid_nonanswer"] for row in rows),
                "invalid": sum(row["invalid"] for row in rows),
                "errors": sum(bool(row.get("error")) for row in rows),
                "truncated": sum(bool(row.get("truncated")) for row in rows),
            }
    selectivity = draws["fs+", "answer"] - draws["fs-", "answer"]
    selection_point = metrics["fs+:answer"]["candidate_minus_A"] - metrics["fs-:answer"]["candidate_minus_A"]
    return metrics, counts, {
        "definition": "candidate-minus-A fs+ answer delta minus true-finish answer delta",
        "value": selection_point,
        "task_bootstrap95": interval(selectivity),
    }


def perform_audit(args):
    root = args.root.resolve(strict=True)
    power = args.power.resolve(strict=True)
    run_root = root / "runs" / args.arm
    generation_path = run_root / "generations.jsonl"
    text_path = run_root / "text_controls.jsonl"
    baseline_generation_path = (args.baseline_generations or root / "baseline_A/generations.jsonl").resolve(strict=True)
    baseline_text_path = (args.baseline_text or root / "baseline_A/text_controls.jsonl").resolve(strict=True)
    frozen_bytes, frozen, schema, manifest = load_frozen(power)
    contexts = {context["row"]["task_id"]: context for context in frozen["contexts"]}
    run_spec = load_json(run_root / "run_spec.json")
    require(run_spec["arm"] == args.arm, "run_spec arm mismatch")
    require(run_spec["model"] == f"moon_leak_{args.arm}", "run_spec model mismatch")
    require(run_spec["checkpoint"] == f"/dev/shm/moon-leak/{args.arm}", "run_spec checkpoint mismatch")
    require(run_spec["vllm_version"] == "0.23.0", "run_spec vLLM mismatch")
    require(run_spec["cohort_sha256"] == frozen["cohort_sha256"], "run_spec cohort hash mismatch")
    require(run_spec["frozen_sha256"] == digest_bytes(frozen_bytes), "run_spec frozen hash mismatch")
    require(run_spec["schema_sha256"] == frozen["schema_sha256"], "run_spec schema hash mismatch")
    require(run_spec["seeds"] == frozen["seeds"] and run_spec["settings"] == frozen["settings"], "run_spec seeds/settings mismatch")
    receipts = receipt_audit(root, args.arm, run_spec, generation_path, text_path)
    if args.baseline_receipt_dir:
        baseline_receipt_dir = args.baseline_receipt_dir.resolve(strict=True)
    elif list(baseline_generation_path.parent.glob("complete_*.json")):
        baseline_receipt_dir = baseline_generation_path.parent
    else:
        baseline_receipt_dir = (power / "runs/A").resolve(strict=True)
    baseline_receipts = baseline_receipt_audit(baseline_receipt_dir, run_spec["frozen_sha256"])
    candidate, candidate_totals = generation_table(
        load_jsonl(generation_path),
        contexts,
        frozen["seeds"],
        schema,
        {
            "kind": "gui",
            "arm": args.arm,
            "model": run_spec["model"],
            "checkpoint": run_spec["checkpoint"],
            "frozen_sha256": run_spec["frozen_sha256"],
        },
    )
    baseline, baseline_totals = generation_table(
        load_jsonl(baseline_generation_path),
        contexts,
        frozen["seeds"],
        schema,
        {"arm": "A", "model": "power_A"},
    )
    texts = text_audit(text_path, baseline_text_path, run_spec)
    metrics, counts, selectivity = bootstrap_metrics(
        baseline, candidate, contexts, frozen["seeds"], args.bootstrap_replicates, args.bootstrap_seed
    )
    correct = metrics["fs+:answer"]["candidate_minus_A"] < 0
    return {
        "status": "PASS",
        "arm": args.arm,
        "verdict": {
            "RAN": [
                "frozen manifest/schema/payload audit",
                "run specification and server/completion receipt audit",
                "220-key candidate and A reconstruction from JSON content",
                "three-control comparison with original A",
                "paired task bootstrap",
            ],
            "PASSED": True,
            "CORRECT": {
                "screen_numbers": True,
                "false_success_answer_suppressed_vs_A": correct,
            },
            "NOT_RUN": ["online OSWorld evaluation", "model or server execution"],
        },
        "inputs": {
            "root": str(root),
            "power": str(power),
            "manifest_sha256": frozen["cohort_sha256"],
            "frozen_sha256": digest_bytes(frozen_bytes),
            "schema_sha256": frozen["schema_sha256"],
            "candidate_generations_sha256": digest(generation_path),
            "candidate_text_sha256": digest(text_path),
            "A_generations_sha256": digest(baseline_generation_path),
            "A_text_sha256": digest(baseline_text_path),
            "context_counts": dict(collections.Counter(row["label"] for row in manifest["train"])),
        },
        "run_spec": run_spec,
        "receipts": receipts,
        "A_receipts": baseline_receipts,
        "candidate_totals": candidate_totals,
        "A_totals": baseline_totals,
        "counts": counts,
        "bootstrap": {
            "unit": "task, paired between candidate and A within stratum",
            "replicates": args.bootstrap_replicates,
            "seed": args.bootstrap_seed,
            "interval": "percentile95",
        },
        "metrics": metrics,
        "selectivity": selectivity,
        "text_controls": texts,
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("arm")
    parser.add_argument("--root", type=Path, default=DEFAULT_ROOT)
    parser.add_argument("--power", type=Path, default=DEFAULT_POWER)
    parser.add_argument("--baseline-generations", type=Path)
    parser.add_argument("--baseline-text", type=Path)
    parser.add_argument("--baseline-receipt-dir", type=Path)
    parser.add_argument("--bootstrap-replicates", type=int, default=10_000)
    parser.add_argument("--bootstrap-seed", type=int, default=261029609)
    args = parser.parse_args()
    if not re.fullmatch(r"[A-Za-z0-9_.-]+", args.arm):
        parser.error("unsafe arm name")
    if args.bootstrap_replicates < 1:
        parser.error("bootstrap replicates must be positive")
    output = args.root / f"audit_{args.arm}.json"
    try:
        result = perform_audit(args)
    except Exception as exc:
        result = {
            "status": "FAIL",
            "arm": args.arm,
            "verdict": {"RAN": ["audit attempted"], "PASSED": False, "CORRECT": False, "NOT_RUN": ["online OSWorld evaluation", "model or server execution"]},
            "error": f"{type(exc).__name__}: {exc}",
        }
    atomic_json(output, result)
    print(json.dumps(result, ensure_ascii=False, indent=2))
    raise SystemExit(0 if result["status"] == "PASS" else 1)


if __name__ == "__main__":
    main()
