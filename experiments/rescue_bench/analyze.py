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


def acted(row):
    return any(tool not in {"answer", "<unparsable>"} for tool in row["tools"])


def repair_credit(row):
    return row["score"] if acted(row) else 0.0


def summarize(groups, ids, seed=1701):
    result = {"episodes": len(ids), "arms": {}}
    for arm in ARMS:
        rows = [row for task in ids for row in groups[task][arm]]
        scores = [row["score"] for row in rows]
        episode_any = [any(row["score"] >= 1 for row in groups[task][arm]) for task in ids]
        result["arms"][arm] = {
            "branches": len(rows), "full_successes": sum(score >= 1 for score in scores),
            "full_success_without_new_action": sum(row["score"] >= 1 and not acted(row) for row in rows),
            "full_success_after_new_action": sum(row["score"] >= 1 and acted(row) for row in rows),
            "partial_or_full_progress": sum(score > 0 for score in scores),
            "mean_official_score": mean(scores),
            "episodes_with_any_full_success": sum(episode_any),
            "episode_any_full_success_wilson95": wilson(sum(episode_any), len(ids)),
            "model_calls": sum(row["model_calls"] for row in rows),
            "model_call_errors": sum(row["model_call_errors"] for row in rows),
        }
    detected = [row for task in ids for row in groups[task]["guard"] if row["escalated"]]
    detected_ids = [task for task in ids if any(row["escalated"] for row in groups[task]["guard"])]
    repaired_detected_ids = sum(any(row["escalated"] and repair_credit(row) >= 1 for row in groups[task]["guard"]) for task in detected_ids)
    result["conditional_repair"] = {
        "refused_branches": len(detected), "refused_episodes": len(detected_ids),
        "full_successes": sum(row["score"] >= 1 for row in detected),
        "full_repairs_after_action": sum(repair_credit(row) >= 1 for row in detected),
        "full_success_without_new_action": sum(row["score"] >= 1 and not acted(row) for row in detected),
        "full_repair_rate": mean([float(repair_credit(row) >= 1) for row in detected]),
        "mean_official_score": mean([row["score"] for row in detected]),
        "mean_action_qualified_repair_credit": mean([repair_credit(row) for row in detected]),
        "credit_definition": "Official score after at least one new non-answer tool; zero otherwise. A no-action success remains in official scores and the refusal denominator but receives zero repair credit. Actions alone do not establish that replay state was initially failing.",
        "episodes_with_any_full_repair": repaired_detected_ids,
        "episode_any_full_repair_wilson95": wilson(repaired_detected_ids, len(detected_ids)),
    }
    differences = [mean([row["score"] for row in groups[task]["guard"]]) - mean([row["score"] for row in groups[task]["control"]]) for task in ids]
    result["paired_difference"] = {"mean": mean(differences), "episodes_guard_better": sum(value > 0 for value in differences), "episodes_guard_worse": sum(value < 0 for value in differences)}
    if ids:
        rng = random.Random(seed)
        draws = {"difference": [], "guard": [], "control": [], "conditional_score": [], "conditional_repair_credit": [], "conditional_full_repair": []}
        for _ in range(20000):
            sample = rng.choices(ids, k=len(ids))
            arm_means = {arm: mean([row["score"] for task in sample for row in groups[task][arm]]) for arm in ARMS}
            for arm in ARMS:
                draws[arm].append(arm_means[arm])
            draws["difference"].append(arm_means["guard"] - arm_means["control"])
            rows = [row for task in sample for row in groups[task]["guard"] if row["escalated"]]
            draws["conditional_score"].append(mean([row["score"] for row in rows]))
            draws["conditional_repair_credit"].append(mean([repair_credit(row) for row in rows]))
            draws["conditional_full_repair"].append(mean([float(repair_credit(row) >= 1) for row in rows]))
        result["paired_difference"]["episode_cluster_bootstrap95"] = interval(draws["difference"])
        for arm in ARMS:
            result["arms"][arm]["mean_score_episode_cluster_bootstrap95"] = interval(draws[arm])
        result["conditional_repair"]["score_episode_cluster_bootstrap95"] = interval(draws["conditional_score"])
        result["conditional_repair"]["repair_credit_episode_cluster_bootstrap95"] = interval(draws["conditional_repair_credit"])
        result["conditional_repair"]["full_rate_episode_cluster_bootstrap95"] = interval(draws["conditional_full_repair"])
        result["conditional_repair"]["bootstrap_draws_with_no_refusal"] = sum(value is None for value in draws["conditional_score"])
    result["uncertainty_note"] = "20,000 episode-cluster bootstrap draws, fixed seed 1701. Degenerate intervals at all-zero/all-one outcomes do not establish certainty; episode-any Wilson intervals estimate a different, K=2 estimand."
    return result


def predict(primary):
    conditional = primary["conditional_repair"]
    repair = conditional["mean_action_qualified_repair_credit"]
    path = HERE / "PREVALENCE.json"
    result = {"label": "prediction, not measured online gain", "formula": "Delta = p_FS_feasible * d_FS * r_action_qualified_repair_credit - p_TS_exposed * fpr_TS * loss_after_false_reject", "repair_credit_definition": conditional["credit_definition"], "repair_estimate": repair, "status": "conditional repair not yet measured", "scenarios": {}, "scope": "binary feasible false completions and exposed true completions only; infeasible false completions and partial-score endpoints are not modeled", "transport_assumptions": ["Repair transfers from selected short diagnostic episodes to reserve/test feasible false completions", "Frozen judge rates transfer to these splits", "Guard-negative false completions remain failures", "No effects before the original terminal answer", "States receiving action-qualified credit were genuinely failing at the handoff; pixels alone do not prove this"], "unmeasured_parameter": "loss_after_false_reject in [0,1]"}
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
            ci = conditional.get("repair_credit_episode_cluster_bootstrap95")
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
        per[task]["strict_boundary_exclusion"] = reason or (None if task in strict else "boundary_invalid")
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
        "independent_review": {
            "runner": ["VERIFY_RUNNER.md", "SCHEDULING_REVIEW.md"],
            "analysis_logic": "STATS_REVIEW.md",
            "raw_evaluator_evidence": "MEASURED_REPAIRS_REVIEW.md",
            "completed_cohort": "FINAL_REVIEW.md",
            "note": "Reviewer-authored artifacts contain verdicts and the hashes identifying their reviewed inputs.",
        },
    }
    result["all_available_descriptive"] = {}
    for arm in ARMS:
        available = [row for task in expected for row in groups[task][arm]]
        result["all_available_descriptive"][arm] = {"branches": len(available), "score1": sum(row["score"] >= 1 for row in available), "score1_after_action": sum(row["score"] >= 1 and acted(row) for row in available)}
    gates = [row["gate"] for task in expected for row in groups[task]["guard"] if row["gate"]]
    result["observed_guard"] = {
        "initial_checks": len(gates),
        "refused": sum(gate["decision"] == "refused" for gate in gates),
        "verifier_errors": sum(not gate.get("verifier", {}).get("ok", False) for gate in gates),
    }
    reference = json.loads((HERE / "HOLO31_REFERENCE.json").read_text())
    result["contemporary_holo31"] = reference["contemporary_live_measure"]
    result["holo31_comparison_warning"] = reference["comparison_warning"]
    result["prediction"] = predict(result["primary"])
    return result


def report(result):
    primary = result["primary"]
    live = result["all_available_descriptive"]
    conditional = primary["conditional_repair"]
    contemporary = result["contemporary_holo31"]
    baseline_ci = contemporary["paired_diff_ci95_episode_bootstrap"]

    def number(value):
        return "not estimated" if value is None else f"{value:.3f}"

    def ci_text(values, scale=1):
        return "not estimated" if values is None else "[" + ", ".join(f"{scale*x:.3f}" for x in values) + "]"

    lines = [
        "# Rescue benchmark", "",
        f"Status: **{result['status']}**; {result['completed_branches']}/48 branches completed. Updated {result['generated_utc']}.", "",
        "This is a conditional replay experiment, not an observed reserve/test online gain.", "",
        f"All collected branches, including incomplete pairs (descriptive only): Guard {live['guard']['score1']}/{live['guard']['branches']} score1, of which {live['guard']['score1_after_action']} after a new action; control {live['control']['score1']}/{live['control']['branches']} score1, of which {live['control']['score1_after_action']} after a new action.", "",
        "## Paired primary analysis", "",
        "| Arm | Official score1 / branches | After a new action | Mean official score (cluster 95% CI) |",
        "|---|---:|---:|---|",
    ]
    for arm in ARMS:
        row = primary["arms"][arm]
        label = "Claude Guard → Holo4" if arm == "guard" else "Holo4 without Guard"
        lines.append(f"| {label} | {row['full_successes']}/{row['branches']} | {row['full_success_after_new_action']} | {number(row['mean_official_score'])} {ci_text(row.get('mean_score_episode_cluster_bootstrap95'))} |")
    lines += [
        "", f"Primary: {primary['episodes']}/12 episodes, all four K=2 branches complete with valid replay. Guard−control mean score difference: **{number(primary['paired_difference']['mean'])}**, episode-cluster 95% CI **{ci_text(primary['paired_difference'].get('episode_cluster_bootstrap95'))}**.", "",
        f"After an actual initial Guard refusal: {conditional['full_repairs_after_action']}/{conditional['refused_branches']} score1 outcomes after a new action, across {conditional['refused_episodes']} episodes. Full repair rate CI: {ci_text(conditional.get('full_rate_episode_cluster_bootstrap95'))}. Action-qualified score credit: {number(conditional['mean_action_qualified_repair_credit'])}, CI {ci_text(conditional.get('repair_credit_episode_cluster_bootstrap95'))}. Refused no-action successes: {conditional['full_success_without_new_action']}.", "",
        conditional["credit_definition"], "",
        primary["uncertainty_note"], "",
        f"Companion any-repair-in-K2 episode estimate: {conditional['episodes_with_any_full_repair']}/{conditional['refused_episodes']}; Wilson95 {ci_text(conditional['episode_any_full_repair_wilson95'])}. This is a different estimand from per-branch repair probability.", "",
        "| Episode | Guard K0, K1 | Control K0, K1 | Primary / strict exclusion |",
        "|---|---|---|---|",
    ]
    for task, values in result["per_episode"].items():
        scores = {arm: ", ".join(f"K{row['k']}={number(row['score'])}" for row in values[arm]) or "pending" for arm in ARMS}
        lines.append(f"| {task.split('/')[0]}/{task.split('/')[-1][:8]} | {scores['guard']} | {scores['control']} | {values['exclusion'] or 'none'} / {values['strict_boundary_exclusion'] or 'none'} |")
    for label, key in (("Strict replay + boundary", "strict_boundary_sensitivity"), ("All complete, ignoring replay validity", "all_complete_sensitivity")):
        sensitivity = result[key]
        lines += ["", f"{label}: {sensitivity['episodes']} episodes; paired difference {number(sensitivity['paired_difference']['mean'])}, CI {ci_text(sensitivity['paired_difference'].get('episode_cluster_bootstrap95'))}."]
    lines += [
        "", "The control resumes at the same recorded answer boundary without running the Guard. The treatment inserts the recorded answer and frozen Claude feedback and escalates only on refusal. No second Guard is applied during rescue. This estimates the full handoff policy, not feedback alone.", "",
        "## Holo3.1 reference", "",
        "The requested historical 08:36 snapshot is 0/10 in each arm: five episodes repeated twice, not ten independent episodes. Any-repair episode Wilson95 is [0, 0.434]. The paired bootstrap is degenerate at zero. It is not a concurrent third arm.", "",
        f"The completed contemporary Holo3.1 experiment (15 turns) has {contemporary['guard']['repaired_score1']}/{contemporary['guard']['branches']} official score1 with Guard versus {contemporary['no_guard']['repaired_score1']}/{contemporary['no_guard']['branches']} without Guard across nine common-valid episodes. Mean paired difference {number(contemporary['paired_diff_mean'])}; independently recomputed 20k/seed1701 CI {ci_text(baseline_ci['independent_recomputation']['ci95'])}. The source 10k/seed0 Monte Carlo CI was {ci_text(baseline_ci['reported_source']['ci95'])}; methods and both values are preserved in HOLO31_REFERENCE.json.", "",
        "Two official successes in each Holo3.1 arm come from immediate answers without new actions on Impress/8979838c. These are replay-state drift, not continuation repairs. The three additional Guard successes follow actions (Calc2, Writer1). The reference uses 15 turns versus Holo4's 20 and a different Guard policy; no randomized Holo4-versus-Holo3.1 effect is claimed.", "",
        "## Predicted online gain — not measured", "",
        "Δ = p(feasible false completion) × P(Guard rejects | false completion) × r − p(true completion exposed to Guard) × P(false rejection | true completion) × loss.", "",
        f"Here r={number(result['prediction'].get('repair_estimate'))} is action-qualified score credit after refusal, with no-action successes credited zero. Frozen Claude detection is 45/66 and false rejection is 21/202. Loss after falsely rejecting a true success is unmeasured; scenarios below are assumptions, not measured harms.", "",
        "| Split | Feasible false completions | Exposed true completions | Formula in percentage points | Break-even r if loss=1 |",
        "|---|---:|---:|---|---:|",
    ]
    for name, scenario in result["prediction"]["scenarios"].items():
        n = scenario["episodes"]
        lines.append(f"| {name} | {round(scenario['p_FS_feasible']*n)}/{n} | {round(scenario['p_TS_exposed']*n)}/{n} | {scenario['formula_percent_points']} | {100*scenario['repair_break_even_if_loss_one']:.1f}% |")
    lines += ["", "| Split | Assumed loss | Predicted change (pp) | Repair-only 95% CI (pp) |", "|---|---:|---:|---|"]
    for name, scenario in result["prediction"]["scenarios"].items():
        for value in scenario.get("loss_scenarios", []):
            lines.append(f"| {name} | {value['loss']:.0%} | {100*value['predicted_score_change']:+.2f} | {ci_text(value.get('repair_only_bootstrap95'),100)} |")
    lines += [
        "", result["prediction"].get("interval_scope", "No repair estimate yet."), "",
        "Transport from selected short feasible replay episodes and an external judge corpus is an assumption. Infeasible false claims and partial-score endpoints are outside this formula. Three calibration task IDs overlap reserve; none overlap test. Reserve is therefore not an independent held-out validation. Neither split was rerun here.", "",
        "## Verification and limits", "",
        f"Initial Guard checks: {result['observed_guard']['initial_checks']}; refusals: {result['observed_guard']['refused']}; verifier errors: {result['observed_guard']['verifier_errors']}. Infrastructure error attempts: {len(result['infrastructure_error_attempts'])}. Missing or invalid replays are disclosed, never converted into successes.", "",
        "Pixel replay validity does not guarantee evaluator-state identity. Zero-action positive scores are retained as official outcomes but receive zero repair credit in the prediction. A new action by itself also cannot prove the handoff state was failing. Common complete-case exclusion may induce selection bias; intervals do not capture that bias or transport uncertainty.", "",
        "Required-output retrieval failed for d682 control K1 (rearranged.png missing, boundary-invalid) and all four aa4 VLC branches (MP4 missing, replay-invalid). These official zeros are retained and qualified in the raw evidence review; successful branch execution does not imply that every evaluator getter succeeded. The f5 control K1 success is a real correction on a strict-valid branch, although its episode is excluded from the primary because other repetitions have invalid replays.", "",
        "RESULT.json contains per-episode scores, exclusions and source hashes. The data/ archive allows numerical reproduction with analyze.py --root experiments/rescue_bench/data. Raw calls, screenshots, boundary contexts, Guard journals and official evaluator outcomes are under /home/orbit/osw/rescue_bench/. FROZEN.json checks unchanged Guard and harness sources; compatibility.json records the one-step schema check. Runner and scheduling reviews: VERIFY_RUNNER.md and SCHEDULING_REVIEW.md. Raw evaluator audit: MEASURED_REPAIRS_REVIEW.md. The independent completed-cohort numerical verdict and reviewed hashes are recorded separately in FINAL_REVIEW.md.",
    ]
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
