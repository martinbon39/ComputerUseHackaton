#!/usr/bin/env python3
"""CPU-only regression checks for rescue_bench/analyze.py."""
from __future__ import annotations

from collections import defaultdict
import importlib.util
import json
import math
from pathlib import Path
import tempfile


HERE = Path(__file__).resolve().parent


def load_analysis():
    spec = importlib.util.spec_from_file_location("rescue_bench_analysis", HERE / "analyze.py")
    if spec is None or spec.loader is None:
        raise RuntimeError("could not load analyze.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def check(condition, message):
    if not condition:
        raise AssertionError(message)


def close(actual, expected, message):
    check(math.isclose(actual, expected, rel_tol=1e-12, abs_tol=1e-12), f"{message}: {actual} != {expected}")


def branch(task, arm, k, score, tools, *, escalated=False, replay_valid=True):
    gate = None if arm == "control" else {
        "decision": "refused" if escalated else "accepted",
        "verifier": {"ok": True},
    }
    return {
        "task": task,
        "arm": arm,
        "k": k,
        "score": score,
        "tools": tools,
        "valid_model_calls": 1,
        "gate": gate,
        "replay_valid": replay_valid,
        "strict_replay_valid": replay_valid,
        "escalated": escalated,
        "replay_diff_max": 0.0,
        "boundary_diff": 0.0,
        "model_calls": 1,
        "model_call_errors": 0,
    }


def write_jsonl(path, rows):
    path.write_text("\n".join(json.dumps(row) for row in rows) + "\n")


def prepare_fixture(root, analysis):
    analysis_here = root / "rescue_bench"
    analysis_here.mkdir()
    runner_dir = root / "feci_guard"
    runner_dir.mkdir()
    (runner_dir / "rescue_runner.py").write_text("# synthetic provenance fixture\n")
    tasks = [f"domain/task{i}" for i in range(12)]
    (analysis_here / "episodes.txt").write_text("\n".join(tasks) + "\n")
    prevalence = {
        "runs": {
            "synthetic": {
                "counts": {
                    "episodes": 10,
                    "false_success_feasible_guard_exposed": 2,
                    "true_score1_answer_guard_exposed": 3,
                },
                "provenance": {"manifest": []},
            }
        }
    }
    (analysis_here / "PREVALENCE.json").write_text(json.dumps(prevalence))
    reference = {"contemporary_live_measure": {}, "comparison_warning": "synthetic fixture"}
    (analysis_here / "HOLO31_REFERENCE.json").write_text(json.dumps(reference))
    analysis.HERE = analysis_here
    return tasks


def check_mixed_fixture(analysis, root, tasks):
    rows = [
        branch(tasks[0], "guard", 0, 1.0, ["answer"], escalated=True),
        branch(tasks[0], "guard", 1, 0.0, ["<unparsable>"], escalated=True),
        branch(tasks[0], "control", 0, 0.0, ["answer"]),
        branch(tasks[0], "control", 1, 0.0, ["answer"]),
        branch(tasks[1], "guard", 0, 1.0, ["click", "answer"], escalated=True),
        branch(tasks[1], "guard", 1, 0.5, ["click"], escalated=True),
        branch(tasks[1], "control", 0, 0.0, ["click"]),
        branch(tasks[1], "control", 1, 0.25, ["click"]),
        branch(tasks[2], "guard", 0, 0.5, ["click"]),
        branch(tasks[2], "guard", 1, 0.0, ["answer"]),
        branch(tasks[2], "control", 0, 0.5, ["click"]),
        branch(tasks[2], "control", 1, 0.0, ["answer"]),
        branch(tasks[3], "control", 0, 1.0, ["click"]),
    ]
    source = root / "branches-fixture.jsonl"
    write_jsonl(source, rows)
    result = analysis.analyze(root)
    primary = result["primary"]
    guard = primary["arms"]["guard"]
    conditional = primary["conditional_repair"]

    check(primary["episodes"] == 3, "incomplete episode entered paired primary")
    check(guard["branches"] == 6, "paired primary did not retain exactly K=2 per complete episode")
    check(guard["full_successes"] == 2, "official score1 endpoint changed")
    check(guard["full_success_without_new_action"] == 1, "no-action score1 was not disclosed")
    check(guard["full_success_after_new_action"] == 1, "acted score1 count is wrong")
    close(guard["mean_official_score"], 0.5, "partial scores were not preserved in official mean")
    close(primary["paired_difference"]["mean"], 0.375, "paired mean of episode K means is wrong")

    check(conditional["refused_branches"] == 4, "non-refused branches entered conditional denominator")
    check(conditional["refused_episodes"] == 2, "non-refused episode entered conditional denominator")
    check(conditional["full_successes"] == 2, "conditional official score1 count is wrong")
    check(conditional["full_repairs_after_action"] == 1, "no-op score1 was counted as a repair")
    check(conditional["full_success_without_new_action"] == 1, "conditional no-op disclosure is wrong")
    close(conditional["mean_official_score"], 0.625, "conditional official mean is wrong")
    close(conditional["mean_action_qualified_repair_credit"], 0.375, "no-op or partial repair credit regressed")
    close(conditional["full_repair_rate"], 0.25, "action-qualified full repair rate is wrong")

    descriptive = result["all_available_descriptive"]
    check(descriptive["control"] == {"branches": 7, "score1": 1, "score1_after_action": 1},
          "incomplete available branch was not isolated in descriptive output")
    prediction = result["prediction"]
    close(prediction["repair_estimate"], 0.375, "prediction used official score instead of repair credit")
    scenario = prediction["scenarios"]["synthetic"]
    expected_gain = (2 / 10) * (45 / 66) * 0.375
    close(scenario["loss_scenarios"][0]["predicted_score_change"], expected_gain,
          "no-op score1 created prediction benefit")
    expected_interval = [
        (2 / 10) * (45 / 66) * value
        for value in conditional["repair_credit_episode_cluster_bootstrap95"]
    ]
    check(scenario["loss_scenarios"][0]["repair_only_bootstrap95"] == expected_interval,
          "prediction did not transform the repair-credit interval")

    duplicated = rows + [branch(tasks[0], "guard", 0, 0.0, ["click"], escalated=True)]
    write_jsonl(source, duplicated)
    try:
        analysis.analyze(root)
    except AssertionError as error:
        check("duplicate successful outcome" in str(error), "duplicate failed for an unrelated reason")
    else:
        raise AssertionError("duplicate successful (task, arm, k) was accepted")


def check_zero_refusal_fixture(analysis, root, tasks):
    rows = []
    for k in (0, 1):
        rows.extend([
            branch(tasks[0], "guard", k, 0.5, ["click"]),
            branch(tasks[0], "control", k, 0.0, ["click"]),
        ])
    write_jsonl(root / "branches-fixture.jsonl", rows)
    result = analysis.analyze(root)
    conditional = result["primary"]["conditional_repair"]
    check(conditional["refused_branches"] == 0, "zero-refusal fixture gained a refusal")
    check(conditional["mean_action_qualified_repair_credit"] is None, "zero-refusal credit became zero")
    check(conditional["full_repair_rate"] is None, "zero-refusal rate became zero")
    check(conditional["bootstrap_draws_with_no_refusal"] == 20000, "zero-refusal bootstrap was imputed")
    check(result["prediction"]["repair_estimate"] is None, "zero-refusal prediction became measured")
    check(all("loss_scenarios" not in scenario for scenario in result["prediction"]["scenarios"].values()),
          "zero-refusal fixture emitted prediction scenarios")


def main():
    analysis = load_analysis()
    with tempfile.TemporaryDirectory(prefix="rescue-analysis-") as temp_dir:
        root = Path(temp_dir)
        tasks = prepare_fixture(root, analysis)
        check_mixed_fixture(analysis, root, tasks)
        check_zero_refusal_fixture(analysis, root, tasks)
    print("verify_analysis: PASS")


if __name__ == "__main__":
    main()
