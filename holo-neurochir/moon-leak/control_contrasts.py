#!/usr/bin/env python3
import os

os.environ.update(OMP_NUM_THREADS="2", MKL_NUM_THREADS="2", OPENBLAS_NUM_THREADS="2")

import argparse
import collections
import hashlib
import json
import sys
from pathlib import Path

import numpy as np

import independent_screen_audit as screen_audit

PAIRS = [
    {"family": "ranked", "edited": "head4_s0", "control": "random4_s0"},
    {"family": "raw", "edited": "raw4_s0", "control": "random_raw4_s0"},
]
FIELDS = {"fs+": ["answer"], "fs-": ["answer"], "healthy": ["answer", "valid_nonanswer"]}


def require(condition, message):
    if not condition:
        raise screen_audit.AuditError(message)


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load_arm(root, frozen, schema, contexts, arm):
    run_root = root / "runs" / arm
    generation_path = run_root / "generations.jsonl"
    audit_path = root / f"audit_{arm}.json"
    spec_path = root / f"spec_{arm}.json"
    run_spec_path = run_root / "run_spec.json"
    missing = [str(path) for path in [generation_path, audit_path, spec_path, run_spec_path] if not path.is_file()]
    require(not missing, f"arm {arm} is unavailable or incomplete; missing: {', '.join(missing)}")
    audit = screen_audit.load_json(audit_path)
    require(audit.get("status") == "PASS" and audit.get("verdict", {}).get("PASSED") is True, f"arm {arm} has no PASS audit")
    require(audit["inputs"]["candidate_generations_sha256"] == digest(generation_path), f"arm {arm} generations changed after audit")
    run_spec = screen_audit.load_json(run_spec_path)
    require(run_spec == audit["run_spec"], f"arm {arm} run_spec changed after audit")
    require(run_spec["arm"] == arm and run_spec["model"] == f"moon_leak_{arm}", f"arm {arm} run identity mismatch")
    require(run_spec["checkpoint"] == f"/dev/shm/moon-leak/{arm}", f"arm {arm} checkpoint root mismatch")
    require(run_spec["frozen_sha256"] == audit["inputs"]["frozen_sha256"], f"arm {arm} frozen hash mismatch")
    require(run_spec["cohort_sha256"] == frozen["cohort_sha256"], f"arm {arm} cohort mismatch")
    require(run_spec["schema_sha256"] == frozen["schema_sha256"], f"arm {arm} schema mismatch")
    require(run_spec["seeds"] == frozen["seeds"] and run_spec["settings"] == frozen["settings"], f"arm {arm} seeds/settings mismatch")
    table, totals = screen_audit.generation_table(
        screen_audit.load_jsonl(generation_path),
        contexts,
        frozen["seeds"],
        schema,
        {
            "kind": "gui",
            "arm": arm,
            "model": run_spec["model"],
            "checkpoint": run_spec["checkpoint"],
            "frozen_sha256": run_spec["frozen_sha256"],
        },
    )
    require(len(table) == 220 and totals["schema_valid"] == 220, f"arm {arm} is not 220/220 schema-valid")
    build_spec = screen_audit.load_json(spec_path)
    require(build_spec["name"] == arm and build_spec["scale"] == 0, f"arm {arm} is not the declared dose-zero build")
    return {
        "table": table,
        "totals": totals,
        "build_spec": build_spec,
        "paths": {
            "generations": generation_path,
            "audit": audit_path,
            "run_spec": run_spec_path,
            "build_spec": spec_path,
        },
    }


def interval(values):
    return np.quantile(values, [0.025, 0.975]).tolist()


def contrast_pair(pair, arms, contexts, seeds, replicates, bootstrap_seed):
    edited = arms[pair["edited"]]
    control = arms[pair["control"]]
    edited_spec = edited["build_spec"]
    control_spec = control["build_spec"]
    require(edited_spec.get("control") is False, f"{pair['edited']} is not declared as an edited arm")
    require(control_spec.get("control") is True, f"{pair['control']} is not declared as a control arm")
    require(len(edited_spec["heads"]) == len(control_spec["heads"]) == 4, f"{pair['family']} is not a matched four-head pair")
    require(edited_spec["ranking"] == control_spec["ranking"], f"{pair['family']} ranking provenance differs")
    require(edited_spec["random_seed"] == control_spec["random_seed"], f"{pair['family']} pairing seed differs")
    rng = np.random.default_rng(bootstrap_seed)
    metrics = {}
    draws = {}
    task_counts = collections.Counter(context["row"]["label"] for context in contexts.values())
    require(dict(task_counts) == {"fs+": 19, "fs-": 20, "healthy": 16}, f"unexpected task strata: {dict(task_counts)}")
    for label in ["fs+", "fs-", "healthy"]:
        tasks = [task_id for task_id, context in contexts.items() if context["row"]["label"] == label]
        indices = rng.integers(0, len(tasks), size=(replicates, len(tasks)))
        for field in FIELDS[label]:
            edited_rates = np.array(
                [np.mean([int(edited["table"][task_id, seed][field]) for seed in seeds]) for task_id in tasks]
            )
            control_rates = np.array(
                [np.mean([int(control["table"][task_id, seed][field]) for seed in seeds]) for task_id in tasks]
            )
            task_deltas = control_rates - edited_rates
            sampled = task_deltas[indices].mean(axis=1)
            draws[label, field] = sampled
            metrics[f"{label}:{field}"] = {
                "tasks": len(tasks),
                "samples_per_arm": len(tasks) * len(seeds),
                "edited_count": sum(edited["table"][task_id, seed][field] for task_id in tasks for seed in seeds),
                "control_count": sum(control["table"][task_id, seed][field] for task_id in tasks for seed in seeds),
                "edited_rate": float(edited_rates.mean()),
                "control_rate": float(control_rates.mean()),
                "control_minus_edited": float(task_deltas.mean()),
                "task_bootstrap95": interval(sampled),
            }
    selectivity_draws = draws["fs+", "answer"] - draws["fs-", "answer"]
    selectivity = (
        metrics["fs+:answer"]["control_minus_edited"] - metrics["fs-:answer"]["control_minus_edited"]
    )
    return {
        "family": pair["family"],
        "edited": pair["edited"],
        "control": pair["control"],
        "scale": 0,
        "head_count_per_arm": 4,
        "metrics": metrics,
        "differential_selectivity": {
            "definition": "(control-minus-edited) fs+ answer contrast minus (control-minus-edited) true-finish answer contrast",
            "value": selectivity,
            "task_bootstrap95": interval(selectivity_draws),
        },
        "interpretation": {
            "positive_fs_answer_contrast": "the targeted edited heads suppress false-success answers more than their matched random control",
            "positive_differential_selectivity": "the targeted edited heads have a larger false-success-specific advantage over control after subtracting the true-finish contrast",
            "healthy_valid_nonanswer": "positive means the control retains more valid non-answer actions than the targeted edit; negative means the targeted edit retains more",
        },
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, default=Path("/workspace/astra/moon-leak"))
    parser.add_argument("--power", type=Path, default=Path("/workspace/astra/astra-power"))
    parser.add_argument("--bootstrap-replicates", type=int, default=10_000)
    parser.add_argument("--bootstrap-seed", type=int, default=261029609)
    args = parser.parse_args()
    if args.bootstrap_replicates < 1:
        parser.error("bootstrap replicates must be positive")
    try:
        root = args.root.resolve(strict=True)
        power = args.power.resolve(strict=True)
        frozen_bytes, frozen, schema, _ = screen_audit.load_frozen(power)
        contexts = {context["row"]["task_id"]: context for context in frozen["contexts"]}
        arm_names = {value for pair in PAIRS for value in [pair["edited"], pair["control"]]}
        arms = {arm: load_arm(root, frozen, schema, contexts, arm) for arm in sorted(arm_names)}
        contrasts = [
            contrast_pair(pair, arms, contexts, frozen["seeds"], args.bootstrap_replicates, args.bootstrap_seed)
            for pair in PAIRS
        ]
        source_hashes = {
            "script": digest(Path(__file__)),
            "audit_module": digest(Path(screen_audit.__file__)),
            "FROZEN.json": digest(power / "FROZEN.json"),
            "schema.json": digest(power / "schema.json"),
            "cohort/manifest.json": digest(power / "cohort/manifest.json"),
        }
        for arm, value in arms.items():
            for name, path in value["paths"].items():
                source_hashes[f"{arm}/{name}"] = digest(path)
        result = {
            "status": "PASS",
            "pairs": contrasts,
            "bootstrap": {
                "unit": "task, four seeds averaged within task, paired between control and edited arm",
                "replicates": args.bootstrap_replicates,
                "seed": args.bootstrap_seed,
                "interval": "percentile95",
                "strata": {"fs+": 19, "fs-": 20, "healthy": 16},
            },
            "frozen_sha256": hashlib.sha256(frozen_bytes).hexdigest(),
            "source_sha256": source_hashes,
            "not_run": ["model server", "GPU", "generation requests", "online OSWorld evaluation"],
        }
        destination = root / "control_contrasts.json"
        screen_audit.atomic_json(destination, result)
        print(json.dumps({"status": "PASS", "output": str(destination), "pairs": contrasts}, ensure_ascii=False, indent=2))
    except Exception as exc:
        print(f"CONTROL CONTRASTS NOT READY: {type(exc).__name__}: {exc}", file=sys.stderr)
        raise SystemExit(2) from exc


if __name__ == "__main__":
    main()
