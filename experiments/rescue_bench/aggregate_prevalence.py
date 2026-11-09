#!/usr/bin/env python3
import argparse
import hashlib
import json
from pathlib import Path


FIELDS = (
    "score",
    "finished_by_agent",
    "infeasible_task",
    "model_declared_infeasible",
)


def sha256(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def wilson(successes, total, z=1.959963984540054):
    p = successes / total
    denominator = 1 + z * z / total
    center = (p + z * z / (2 * total)) / denominator
    half_width = z * ((p * (1 - p) / total + z * z / (4 * total * total)) ** 0.5) / denominator
    return [center - half_width, center + half_width]


def summarize(root):
    paths = sorted(root.glob("pyautogui/screenshot/*/*/*/meta.json"))
    rows = []
    manifest = []
    for path in paths:
        raw = json.loads(path.read_text())
        row = {field: raw.get(field) for field in FIELDS}
        rows.append(row)
        manifest.append({"path": str(path.relative_to(root)), "sha256": sha256(path)})

    def count(predicate):
        return sum(predicate(row) for row in rows)

    n = len(rows)
    counts = {
        "episodes": n,
        "false_success_feasible": count(
            lambda r: r["score"] == 0 and r["finished_by_agent"] and not r["infeasible_task"]
        ),
        "false_success_feasible_guard_exposed": count(
            lambda r: r["score"] == 0
            and r["finished_by_agent"]
            and not r["infeasible_task"]
            and not r["model_declared_infeasible"]
        ),
        "false_success_infeasible_completion_claim": count(
            lambda r: r["score"] == 0
            and r["finished_by_agent"]
            and r["infeasible_task"]
            and not r["model_declared_infeasible"]
        ),
        "true_score1_answer_guard_exposed": count(
            lambda r: r["score"] == 1
            and r["finished_by_agent"]
            and not r["model_declared_infeasible"]
        ),
        "true_score1_declared_infeasible_guard_bypassed": count(
            lambda r: r["score"] == 1
            and r["finished_by_agent"]
            and r["model_declared_infeasible"]
        ),
        "true_score1_nonanswer": count(lambda r: r["score"] == 1 and not r["finished_by_agent"]),
        "partial_answer_guard_exposed": count(
            lambda r: r["score"] not in (0, 1)
            and r["finished_by_agent"]
            and not r["model_declared_infeasible"]
        ),
        "partial_answer_declared_infeasible_guard_bypassed": count(
            lambda r: r["score"] not in (0, 1)
            and r["finished_by_agent"]
            and r["model_declared_infeasible"]
        ),
        "partial_nonanswer": count(lambda r: r["score"] not in (0, 1) and not r["finished_by_agent"]),
        "declared_infeasible_all_scores": count(lambda r: r["model_declared_infeasible"]),
    }
    prevalence_keys = (
        "false_success_feasible",
        "false_success_feasible_guard_exposed",
        "false_success_infeasible_completion_claim",
        "true_score1_answer_guard_exposed",
    )
    prevalence = {
        key: {
            "numerator": counts[key],
            "denominator": n,
            "rate": counts[key] / n,
            "wilson95": wilson(counts[key], n),
        }
        for key in prevalence_keys
    }
    manifest_text = "".join(f"{item['path']}\0{item['sha256']}\n" for item in manifest).encode()
    return {
        "root": str(root),
        "fields_read": list(FIELDS),
        "counts": counts,
        "prevalence": prevalence,
        "provenance": {
            "meta_files": len(manifest),
            "manifest_sha256": hashlib.sha256(manifest_text).hexdigest(),
            "manifest": manifest,
        },
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--osw-root", type=Path, default=Path("/home/orbit/osw"))
    parser.add_argument("--output", type=Path, default=Path(__file__).with_name("PREVALENCE.json"))
    args = parser.parse_args()
    runs = {
        "reserve45_modal_original": "results_confirm_gh_orig_modal_confirm",
        "test120_modal_original": "results_test_gh_orig_modal_test",
    }
    result = {
        "schema_version": 1,
        "guard_exposure_rule": "finished_by_agent and not model_declared_infeasible",
        "false_success_rule": "score == 0 and finished_by_agent; split by official infeasible_task and Guard exposure",
        "true_success_fpr_transport_rule": "score == 1 and finished_by_agent and not model_declared_infeasible",
        "partial_rule": "score not in {0, 1}; reported separately because judge_bench excluded partial scores",
        "runs": {key: summarize(args.osw_root / value) for key, value in runs.items()},
        "judge_transport": {
            "reported_false_rejections": 21,
            "reported_true_successes": 202,
            "reported_rate": 21 / 202,
            "scope": "judge_bench binary-score final-answer corpus",
            "limitation": "The frozen judge corpus excluded officially infeasible episodes before judging, so 21/202 transports to Guard-exposed non-infeasibility answers, not to successful infeasibility refusals or partial scores.",
        },
    }
    args.output.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")


if __name__ == "__main__":
    main()
