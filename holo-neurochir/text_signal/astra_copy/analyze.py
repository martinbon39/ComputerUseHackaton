import os
os.environ.update(OMP_NUM_THREADS="2", MKL_NUM_THREADS="2", OPENBLAS_NUM_THREADS="2")
import collections
import datetime
import hashlib
import json
import math
from pathlib import Path

import numpy as np

STATE = Path(__file__).resolve().parent
BOOTSTRAPS = 100000
BOOTSTRAP_SEED = 20261108
STRATA = ["fs+", "fs-", "healthy"]


def interval(draws):
    return np.quantile(draws, [0.025, 0.975]).tolist()


def wilson(successes, n):
    z = 1.959963984540054
    p = successes / n
    denominator = 1 + z * z / n
    center = (p + z * z / (2 * n)) / denominator
    radius = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / denominator
    return [center - radius, center + radius]


def analysis(rows, manifest, arms):
    rng = np.random.default_rng(BOOTSTRAP_SEED)
    result = {"arms": {}, "contrasts": {}, "contexts": {}}
    draws = {}
    for label in STRATA:
        contexts = [r for r in manifest if r["label"] == label]
        ids = [r["task_id"] for r in contexts]
        index = rng.integers(0, len(ids), size=(BOOTSTRAPS, len(ids)))
        result["contexts"][label] = {"n_tasks": len(ids), "task_ids": ids}
        for arm in arms:
            arm_rows = [rows[arm][task] for task in ids]
            context_rates = np.array([sum(x["answer"] for x in rr) / len(rr) for rr in arm_rows])
            generated = [x for rr in arm_rows for x in rr]
            n = len(generated)
            answer = sum(x["answer"] for x in generated)
            draws[(arm, label)] = context_rates[index].mean(axis=1)
            result["arms"].setdefault(arm, {})[label] = {
                "n_tasks": len(ids), "n_generations": n, "answer": answer,
                "answer_rate": answer / n, "wilson95_descriptive": wilson(answer, n),
                "task_bootstrap95": interval(draws[(arm, label)]),
                "valid_nonanswer": sum(x["valid_nonanswer"] for x in generated),
                "invalid": sum(x["invalid"] for x in generated),
                "transport_error": sum(bool(x.get("error")) for x in generated),
                "truncated": sum(bool(x.get("truncated")) for x in generated),
                "schema_invalid_without_transport_error": sum(x["invalid"] and not x.get("error") for x in generated),
                "context_answer_rates": dict(zip(ids, context_rates.tolist())),
                "tools": dict(collections.Counter(x.get("tool") for x in generated)),
            }
    contrasts = [(arm, "A") for arm in arms if arm != "A"] if "A" in arms else []
    if "C" in arms and "D" in arms:
        contrasts.append(("C", "D"))
    for treatment, reference in contrasts:
        contrast = {"treatment": treatment, "reference": reference, "strata": {}}
        for label in STRATA:
            tr = result["arms"][treatment][label]
            ref = result["arms"][reference][label]
            delta = tr["answer_rate"] - ref["answer_rate"]
            contrast["strata"][label] = {
                "delta": delta, "task_bootstrap95": interval(draws[treatment, label] - draws[reference, label]),
                "context_deltas": {task: tr["context_answer_rates"][task] - ref["context_answer_rates"][task]
                                   for task in tr["context_answer_rates"]},
            }
        selectivity_draws = ((draws[treatment, "fs+"] - draws[reference, "fs+"]) -
                            (draws[treatment, "fs-"] - draws[reference, "fs-"]))
        contrast["selectivity"] = {
            "delta_fs_minus_delta_true": contrast["strata"]["fs+"]["delta"] - contrast["strata"]["fs-"]["delta"],
            "task_bootstrap95": interval(selectivity_draws),
            "interpretation": "negative means greater suppression of false than true finishes",
        }
        result["contrasts"][f"{treatment}-{reference}"] = contrast
    return result


def main():
    frozen_bytes = (STATE / "FROZEN.json").read_bytes()
    frozen = json.loads(frozen_bytes)
    manifest = [x["row"] for x in frozen["contexts"]]
    expected = {x["row"]["task_id"]: x for x in frozen["contexts"]}
    data, completeness, hashes = {}, {}, {}
    for arm in "ABCD":
        path = STATE / "runs" / arm / "generations.jsonl"
        if not path.exists():
            completeness[arm] = {"status": "NOT_RUN", "completed": 0}
            continue
        hashes[str(path.relative_to(STATE))] = hashlib.sha256(path.read_bytes()).hexdigest()
        values = [json.loads(line) for line in path.read_text().splitlines()]
        keys = {(x["row"]["task_id"], x["seed"]) for x in values}
        assert len(keys) == len(values), f"duplicate {arm}"
        grouped = collections.defaultdict(list)
        for value in values:
            task = value["row"]["task_id"]
            assert task in expected and value["arm"] == arm
            assert value["row"] == expected[task]["row"]
            assert value["payload_sha256"] == expected[task]["payload_sha256"]
            assert value["seed"] in frozen["seeds"]
            grouped[task].append(value)
        is_complete = keys == {(r["task_id"], seed) for r in manifest for seed in frozen["seeds"]}
        completeness[arm] = {"status": "COMPLETE" if is_complete else "PARTIAL", "completed": len(values),
                             "expected": len(manifest) * len(frozen["seeds"])}
        if is_complete:
            data[arm] = grouped
    arms = sorted(data)
    result = {
        "created_utc": datetime.datetime.now(datetime.timezone.utc).isoformat(),
        "status": "COMPLETE" if len(arms) == 4 else "PARTIAL",
        "independent_audit_artifact": "VERIFY_FINAL.json",
        "frozen_sha256": hashlib.sha256(frozen_bytes).hexdigest(), "raw_sha256": hashes,
        "completeness": completeness,
        "method": {"paired_seeds": frozen["seeds"], "bootstrap_replicates": BOOTSTRAPS,
                   "bootstrap_seed": BOOTSTRAP_SEED, "bootstrap_unit": "task, stratified, paired across arms",
                   "bootstrap_interval": "percentile95", "delta": "candidate minus reference",
                   "wilson_warning": "descriptive pooled Bernoulli interval; ignores within-context dependence",
                   "errors": "retained as invalid/nonanswer in scheduled denominator"},
        "full_cohort": analysis(data, manifest, arms),
        "excluding_C_construction_and_preservation": analysis(
            data, [r for r in manifest if not (r["construction_C_overlap"] or r["preservation_C_overlap"])], arms),
    }
    (STATE / "RESULT.json").write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n")
    print(json.dumps({"status": result["status"], "completeness": completeness,
                      "contrasts": {k: {"fs": v["strata"]["fs+"], "true": v["strata"]["fs-"],
                                        "selectivity": v["selectivity"]}
                                    for k, v in result["full_cohort"]["contrasts"].items()}}, indent=2))


if __name__ == "__main__":
    main()
