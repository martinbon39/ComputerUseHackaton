"""Episode-cluster analysis of the preregistered rescue cohort."""
from __future__ import annotations

import argparse
from collections import defaultdict
from datetime import datetime, timezone
import hashlib
import json
import math
from pathlib import Path
import random

HERE = Path(__file__).resolve().parent
ARMS = ("guard", "control")


def wilson(successes, total):
    if not total:
        return None
    z = 1.959963984540054
    p = successes / total
    d = 1 + z * z / total
    center = (p + z * z / (2 * total)) / d
    half = z * math.sqrt(p * (1 - p) / total + z * z / (4 * total * total)) / d
    return [max(0, center - half), min(1, center + half)]


def interval(values):
    values = sorted(value for value in values if value is not None)
    if not values:
        return None
    return [values[int(.025 * len(values))], values[min(len(values) - 1, int(.975 * len(values)))]]


def mean(values):
    return sum(values) / len(values) if values else None


def summarize(groups, ids, seed=1701):
    result = {"episodes": len(ids), "arms": {}}
    for arm in ARMS:
        rows = [row for task in ids for row in groups[task][arm]]
        scores = [row["score"] for row in rows]
        episode_any = [any(row["score"] >= 1 for row in groups[task][arm]) for task in ids]
        result["arms"][arm] = {
            "branches": len(rows), "full_repairs": sum(score >= 1 for score in scores),
            "partial_or_full_progress": sum(score > 0 for score in scores),
            "mean_official_score": mean(scores),
            "episodes_with_any_full_repair": sum(episode_any),
            "episode_any_full_repair_wilson95": wilson(sum(episode_any), len(ids)),
            "model_calls": sum(row["model_calls"] for row in rows),
            "model_call_errors": sum(row["model_call_errors"] for row in rows),
        }
    detected = [row for task in ids for row in groups[task]["guard"] if row["escalated"]]
    detected_ids = [task for task in ids if any(row["escalated"] for row in groups[task]["guard"])]
    repaired_detected_ids = sum(any(row["escalated"] and row["score"] >= 1 for row in groups[task]["guard"]) for task in detected_ids)
    result["conditional_repair"] = {
        "refused_branches": len(detected), "refused_episodes": len(detected_ids),
        "full_repairs": sum(row["score"] >= 1 for row in detected),
        "full_repair_rate": mean([float(row["score"] >= 1) for row in detected]),
        "mean_official_score": mean([row["score"] for row in detected]),
        "episodes_with_any_full_repair": repaired_detected_ids,
        "episode_any_full_repair_wilson95": wilson(repaired_detected_ids, len(detected_ids)),
    }
    differences = [mean([row["score"] for row in groups[task]["guard"]]) - mean([row["score"] for row in groups[task]["control"]]) for task in ids]
    result["paired_difference"] = {"mean": mean(differences), "episodes_guard_better": sum(value > 0 for value in differences), "episodes_guard_worse": sum(value < 0 for value in differences)}
    if ids:
        rng = random.Random(seed)
        draws = {"difference": [], "guard": [], "control": [], "conditional_score": [], "conditional_full_repair": []}
        for _ in range(20000):
            sample = rng.choices(ids, k=len(ids))
            arm_means = {arm: mean([row["score"] for task in sample for row in groups[task][arm]]) for arm in ARMS}
            for arm in ARMS:
                draws[arm].append(arm_means[arm])
            draws["difference"].append(arm_means["guard"] - arm_means["control"])
            rows = [row for task in sample for row in groups[task]["guard"] if row["escalated"]]
            draws["conditional_score"].append(mean([row["score"] for row in rows]))
            draws["conditional_full_repair"].append(mean([float(row["score"] >= 1) for row in rows]))
        result["paired_difference"]["episode_cluster_bootstrap95"] = interval(draws["difference"])
        for arm in ARMS:
            result["arms"][arm]["mean_score_episode_cluster_bootstrap95"] = interval(draws[arm])
        result["conditional_repair"]["score_episode_cluster_bootstrap95"] = interval(draws["conditional_score"])
        result["conditional_repair"]["full_rate_episode_cluster_bootstrap95"] = interval(draws["conditional_full_repair"])
        result["conditional_repair"]["bootstrap_draws_with_no_refusal"] = sum(value is None for value in draws["conditional_score"])
    result["uncertainty_note"] = "20,000 episode-cluster bootstrap draws, fixed seed 1701. Degenerate intervals at all-zero/all-one outcomes do not establish certainty; episode-any Wilson intervals estimate a different, K=2 estimand."
    return result


def predict(primary):
    conditional = primary["conditional_repair"]
    repair = conditional["mean_official_score"]
    path = HERE / "PREVALENCE.json"
    result = {"label": "prediction, not measured online gain", "formula": "Delta = p_FS_feasible * d_FS * r_score_after_reject - p_TS_exposed * fpr_TS * loss_after_false_reject", "status": "conditional repair not yet measured", "scenarios": {}, "scope": "binary feasible false completions and exposed true completions only; infeasible false completions and partial-score endpoints are not modeled", "transport_assumptions": ["Repair transfers from selected short diagnostic episodes to reserve/test feasible false completions", "Frozen judge rates transfer to these splits", "Guard-negative false completions remain failures", "No effects before the original terminal answer"], "unmeasured_parameter": "loss_after_false_reject in [0,1]"}
    if not path.exists():
        result["status"] = "prevalence missing"
        return result
    prevalence = json.loads(path.read_text())
    calibration_ids = {Path(line).name for line in (HERE / "episodes.txt").read_text().splitlines() if line.strip()}
    for name, run in prevalence["runs"].items():
        n = run["counts"]["episodes"]
        fs = run["counts"]["false_success_feasible_guard_exposed"] / n
        ts = run["counts"]["true_score1_answer_guard_exposed"] / n
        detection, false_rejection = 45 / 66, 21 / 202
        gain_coefficient = fs * detection
        loss_coefficient = ts * false_rejection
        overlap = sorted(calibration_ids & {Path(item["path"]).parent.name for item in run["provenance"]["manifest"]})
        entry = {"episodes": n, "calibration_task_overlap": overlap, "p_FS_feasible": fs, "p_TS_exposed": ts,
                 "gain_coefficient": gain_coefficient, "loss_coefficient": loss_coefficient,
                 "formula_percent_points": f"{100*gain_coefficient:.4f} * r - {100*loss_coefficient:.4f} * loss",
                 "repair_break_even_if_loss_one": loss_coefficient / gain_coefficient,
                 "unidentified_parameter_bounds_at_fixed_prevalence": [-loss_coefficient, gain_coefficient]}
        if repair is not None:
            entry["loss_scenarios"] = [{"loss": loss, "predicted_score_change": gain_coefficient * repair - loss_coefficient * loss} for loss in (0, .5, 1)]
            ci = conditional.get("score_episode_cluster_bootstrap95")
            if ci:
                for scenario in entry["loss_scenarios"]:
                    scenario["repair_only_bootstrap95"] = [gain_coefficient * value - loss_coefficient * scenario["loss"] for value in ci]
            result["status"] = "scenario prediction; not an observed online gain"
        result["scenarios"][name] = entry
    result["interval_scope"] = "repair_only_bootstrap95 conditions on prevalence, judge rates and assumed loss; excludes transport error and loss uncertainty"
    return result


def analyze(root):
    sources = sorted(root.glob("branches*.jsonl"))
    rows = [json.loads(line) for source in sources for line in source.read_text().splitlines() if line.strip()]
    expected = ["/".join(Path(line).parts[-2:]) for line in (HERE / "episodes.txt").read_text().splitlines() if line.strip()]
    groups = defaultdict(lambda: defaultdict(list))
    errors = []
    keys = set()
    for row in rows:
        assert row["task"] in expected and row["arm"] in ARMS and row["k"] in (0, 1)
        if "error" in row:
            errors.append(row)
            continue
        key = row["task"], row["arm"], row["k"]
        assert key not in keys, f"duplicate successful outcome: {key}"
        keys.add(key)
        assert math.isfinite(row["score"]) and 0 <= row["score"] <= 1
        assert row["valid_model_calls"] <= 20
        assert row["arm"] != "control" or row["gate"] is None
        groups[row["task"]][row["arm"]].append(row)
    kept, strict, complete, excluded, per = [], [], [], {}, {}
    for task in expected:
        all_rows = [row for arm in ARMS for row in groups[task][arm]]
        reason = "incomplete" if any({row["k"] for row in groups[task][arm]} != {0, 1} for arm in ARMS) else None
        if reason is None:
            complete.append(task)
            if not all(row["replay_valid"] for row in all_rows):
                reason = "replay_invalid"
        if reason is None:
            kept.append(task)
            if all(row["strict_replay_valid"] for row in all_rows):
                strict.append(task)
        else:
            excluded[task] = reason
        per[task] = {arm: [{key: row.get(key) for key in ("k", "score", "escalated", "replay_diff_max", "boundary_diff", "replay_valid", "strict_replay_valid", "valid_model_calls", "tools")} for row in sorted(groups[task][arm], key=lambda row: row["k"])] for arm in ARMS}
        per[task]["exclusion"] = reason
    result = {
        "generated_utc": datetime.now(timezone.utc).isoformat(),
        "status": "complete" if len(keys) == 48 else "partial",
        "expected_episodes": 12, "expected_branches": 48, "completed_branches": len(keys),
        "infrastructure_error_attempts": errors, "excluded": excluded,
        "primary": summarize(groups, kept), "strict_boundary_sensitivity": summarize(groups, strict),
        "all_complete_sensitivity": summarize(groups, complete), "per_episode": per,
        "historical_holo31": {"source": "paper/data/local/feci_guard/repair/snapshot/results.json", "snapshot_utc": "2026-11-08T08:36:00Z", "episodes": 5, "K": 2, "guard_full_repairs": 0, "guard_branches": 10, "control_full_repairs": 0, "control_branches": 10, "guard_refused_branches": 6, "guard_refused_then_repaired": 0, "any_episode_wilson95": wilson(0, 5), "comparison": "historical, not concurrent/randomized; 15 new turns versus 20 in rescue"},
        "guard_detection": {"false_success_rejected": 45, "false_success_total": 66, "true_success_rejected": 21, "true_success_total": 202, "source": "judge_bench/RESULT.json", "repair_losses_on_true_successes": "not measured"},
        "provenance": {"branches_sha256": {str(source): hashlib.sha256(source.read_bytes()).hexdigest() for source in sources}, "runner_sha256": hashlib.sha256((HERE.parent / "feci_guard/rescue_runner.py").read_bytes()).hexdigest()},
        "prediction": {"label": "prediction, not measured online gain", "formula": "Delta = p_FS_feasible * d_FS * r_score_after_reject - p_TS_exposed * fpr_TS * loss_after_false_reject", "status": "pending prevalence artifact or measured conditional repair", "unmeasured_strata": "infeasible false completions and partial-score endpoints; repair measured only on selected feasible short episodes"},
        "independent_review": "VERIFY_RUNNER.md; final numerical review pending",
    }
    result["prediction"] = predict(result["primary"])
    return result


def report(result):
    primary = result["primary"]
    lines = ["# Rescue benchmark", "", f"Status: **{result['status']}**; {result['completed_branches']}/48 branches completed. Updated {result['generated_utc']}.", "", "This is a conditional replay experiment, not an observed reserve/test online gain.", "", "| Arm | Full repairs / branches | Mean official score | Episodes with any full repair |", "|---|---:|---:|---:|"]
    for arm in ARMS:
        row = primary["arms"][arm]
        lines.append(f"| {'Claude Guard → Holo4' if arm == 'guard' else 'Holo4 without Guard'} | {row['full_repairs']}/{row['branches']} | {row['mean_official_score']} | {row['episodes_with_any_full_repair']}/{primary['episodes']} |")
    lines += ["| Historical Holo3.1 + Guard, 15 turns | 0/10 | 0 | 0/5 |", "", f"Primary cohort: {primary['episodes']}/12 episodes; all four branches must have a valid replay. Strict boundary sensitivity: {result['strict_boundary_sensitivity']['episodes']} episodes.", "", f"Paired mean score difference Guard−control: {primary['paired_difference'].get('mean')}; episode-cluster 95% interval {primary['paired_difference'].get('episode_cluster_bootstrap95')}.", "", f"Conditional repair after an actual initial refusal: {primary['conditional_repair']['full_repairs']}/{primary['conditional_repair']['refused_branches']} branches from {primary['conditional_repair']['refused_episodes']} episodes. Score bootstrap interval: {primary['conditional_repair'].get('score_episode_cluster_bootstrap95')}; companion episode-any-repair Wilson interval: {primary['conditional_repair']['episode_any_full_repair_wilson95']}.", "", primary["uncertainty_note"], "", "The control resumes at the same recorded answer boundary without running the Guard. The treatment inserts the recorded answer and the frozen Claude feedback and escalates only on refusal. No second Guard is applied during rescue. This estimates the full handoff policy, not feedback alone.", "", "The historical 0/10 reference is five episodes repeated twice, not ten independent episodes. It used 15 turns and is not a concurrent third arm.", "", "## Prediction (not measured online gain)", "", "Δ = p(feasible false completion) × P(Guard rejects | false completion) × E(score after rescue | rejected) − p(true completion exposed to Guard) × P(false rejection | true completion) × E(score loss | false rejection).", "", "Frozen judge estimates: detection 45/66; false rejection 21/202. Loss after false rejection is unmeasured. Reserve/test prevalence is aggregated from final metadata only. Calibration transfers from selected short feasible episodes and an external judge corpus; that transfer is an assumption. Infeasible false completions and partial-score endpoints are outside this repair estimate.", "", f"Prediction status: {result['prediction']['status']}.", "", "## Evidence and limitations", "", "`RESULT.json` contains all per-episode scores and exclusions. Raw calls, screenshots, original boundary contexts, Guard journals and official outcomes are under `/home/orbit/osw/rescue_bench/`. `FROZEN.json` checks the unchanged Guard and harness sources; `compatibility.json` records the one-step schema check. Independent review: `VERIFY_RUNNER.md`; final numerical review pending.", "", f"Infrastructure error attempts: {len(result['infrastructure_error_attempts'])}. Missing or invalid replays are disclosed, never converted into successes. No global gain claim is justified by a positive point estimate alone."]
    lines += ["", "| Split | Predicted change, percentage points | Break-even repair if every false rejection loses its success |", "|---|---|---:|"]
    for name, scenario in result["prediction"]["scenarios"].items():
        lines.append(f"| {name} | {scenario['formula_percent_points']} | {100*scenario['repair_break_even_if_loss_one']:.1f}% |")
    for name, scenario in result["prediction"]["scenarios"].items():
        if "loss_scenarios" in scenario:
            lines += ["", name + ":"]
            for value in scenario["loss_scenarios"]:
                ci = value.get("repair_only_bootstrap95")
                text_ci = [round(100*x, 2) for x in ci] if ci else None
                lines.append(f"- Assumed loss {value['loss']:.0%}: predicted {100*value['predicted_score_change']:+.2f} pp; repair-only 95% interval {text_ci} pp.")
    lines += ["", result["prediction"].get("interval_scope", "No repair estimate yet."), "", "Three calibration task IDs overlap the reserve; none overlap the test. Reserve transport is therefore not an independent held-out validation. Neither split was rerun here."]
    return "\n".join(lines) + "\n"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", type=Path, default=Path.home() / "osw/rescue_bench")
    args = ap.parse_args()
    result = analyze(args.root)
    (HERE / "RESULT.json").write_text(json.dumps(result, indent=2, ensure_ascii=False) + "\n")
    (HERE / "REPORT.md").write_text(report(result))
    print(json.dumps({key: result[key] for key in ("status", "completed_branches", "excluded")}))


if __name__ == "__main__":
    main()
