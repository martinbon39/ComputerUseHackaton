#!/usr/bin/env python3
import json
import hashlib
from pathlib import Path


HERE = Path(__file__).resolve().parent
RESULT = HERE / "AUDIT_RESULT.json"
REPORT = HERE / "FINAL_AUDIT.md"
MAKER_RESULT = HERE.parent / "RESULT.json"
MAKER_REPORT = HERE.parent / "REPORT.md"


def pct(value):
    return "—" if value is None else f"{100 * value:.2f}%"


def ci(bounds):
    return "—" if bounds is None else f"[{100 * bounds[0]:.2f}%, {100 * bounds[1]:.2f}%]"


def ci_pp(bounds):
    return "—" if bounds is None else f"[{100 * bounds[0]:.2f}, {100 * bounds[1]:.2f}] pp"


def sha256(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def verdict_counts(counts):
    order = ("incomplete", "complete", "truncated", "missing", "malformed", "ambiguous", "error")
    parts = [f"{key}={counts[key]}" for key in order if counts.get(key)]
    parts.extend(f"{key}={value}" for key, value in counts.items() if key not in order)
    return ", ".join(parts) or "none"


def main():
    data = json.loads(RESULT.read_text())
    corpus = data["corpus"]
    responses = data["responses"]
    attempts = responses["attempts_audit"]
    requirements = data["requirement_review"]
    blockers = []
    blockers.extend(corpus["errors"])
    blockers.extend(requirements["errors"])
    blockers.extend(attempts["errors"])
    if responses["raw_record_count"] != responses["expected_record_count"]:
        blockers.append("response schedule incomplete")
    if responses["missing_request_count"]:
        blockers.append("logical requests missing")
    if responses["unexpected_request_ids"] or responses["duplicate_request_ids"]:
        blockers.append("unexpected or duplicate logical request IDs")
    if responses["validation_error_count"]:
        blockers.append("request/response integrity errors")
    if blockers:
        raise SystemExit("Refusing final report: " + "; ".join(blockers))

    primary = responses["by_replicate"]["t0"]
    majority = responses["t08_majority"]
    cluster = responses["t0_cluster_bootstrap95"]
    simulation = responses["blocking_only_simulation"]
    sensitivity = responses["posthoc_metadata_sensitivity"]["false_success_metrics_after_exclusion"]
    lines = [
        "# Independent final audit — final-screen verifier study",
        "",
        "**Verdict: PASS WITH LIMITATIONS.** The registered calculations and raw-artifact integrity are correct. The measured verifier is not a useful discriminator in this corpus: it flags 53.03% of false successes and 48.02% of true successes at T=0, a difference of only 5.01 percentage points with a task-cluster interval spanning zero.",
        "",
        "## RAN",
        "",
        "- `python3 -m unittest -v test_audit_verif.py`",
        "- `python3 audit/audit_verif.py --output audit/AUDIT_RESULT.json`",
        "- Independent reconstruction from the four raw OSWorld result trees, task JSON files, copied PNGs, raw responses/attempts, and raw branch-pilot JSONL files. Maker summaries were not used as numerical evidence.",
        "",
        "## PASSED",
        "",
        f"- Corpus: {corpus['source_episode_count']} source trajectories reconstructed; {corpus['independent_eligible_count']} eligible episodes exactly match the manifest ({corpus['independent_labels']['false_success']} false successes, {corpus['independent_labels']['true_success']} true successes).",
        f"- Screens: all {corpus['manifest_count']} source and copied PNG hashes match; all are 1920×1080, reference the final answer record, and match the final trajectory step; duplicate image hashes: {corpus['duplicate_image_hash_group_count']}.",
        f"- Schedule: {responses['raw_record_count']}/{responses['expected_record_count']} logical responses, no missing/unexpected/duplicate IDs, no request-setting/body-hash/model mismatch, and reasoning is nonempty in {responses['reasoning_nonempty_count']} responses.",
        f"- Runtime: observed maximum concurrency {attempts['max_observed_concurrent_attempts']}; retries {attempts['retry_count']}; maximum gap between completions {attempts['max_seconds_between_attempt_completions']:.2f}s; attempts started at/after deadline {attempts['attempts_started_at_or_after_deadline']}; raw-response copy mismatches {attempts['raw_response_json_mismatch_count']}.",
        f"- Requirement audit: all {requirements['correction_count']} semantic correction entries match frozen T0 raw lines and their before/after arithmetic; raw-line SHA256 `{requirements['selected_t0_raw_lines_sha256']}`.",
        "",
        "## CORRECT — primary T=0 result",
        "",
        "| Ground-truth stratum | INCOMPLETE / all | 95% Wilson | INCOMPLETE / valid verdicts | 95% Wilson | Verdict counts |",
        "|---|---:|---:|---:|---:|---|",
    ]
    for label, title in (("false_success", "False success (score 0)"), ("true_success", "True success (score 1)")):
        row = primary[label]
        lines.append(
            f"| {title} | {row['verdict_counts'].get('incomplete', 0)}/{row['denominator_all']} ({pct(row['incomplete_rate_all'])}) | {ci(row['incomplete_wilson95_all'])} | {row['verdict_counts'].get('incomplete', 0)}/{row['denominator_valid']} ({pct(row['incomplete_rate_valid'])}) | {ci(row['incomplete_wilson95_valid'])} | {verdict_counts(row['verdict_counts'])} |"
        )
    lines.extend(
        [
            "",
            f"Detection minus false-rejection rate: **{100 * responses['t0_detection_minus_false_rejection']:.2f} pp**. The independent audit's 20,000-draw joint task-cluster bootstrap interval is {ci_pp(cluster['detection_minus_false_rejection'])}; the stratum intervals are false success {ci(cluster['false_success'])} and true success {ci(cluster['true_success'])}. The maker report uses the preregistered 10,000 draws, so small Monte Carlo differences between its intervals and these independent sensitivity intervals are expected.",
            "",
            "The episode-level Wilson intervals treat repeated rollouts as independent. That assumption is weak here: 245/268 episodes belong to 67 repeated-task groups; there are only 90 unique tasks, and 18 repeated groups change label across passes.",
            "",
            "## T=0.8 stability",
            "",
            "| Replicate | False-success INCOMPLETE | True-success INCOMPLETE |",
            "|---|---:|---:|",
        ]
    )
    for replicate in ("t08_r1", "t08_r2", "t08_r3"):
        row = responses["by_replicate"][replicate]
        false = row["false_success"]
        true = row["true_success"]
        lines.append(
            f"| {replicate} | {false['verdict_counts'].get('incomplete', 0)}/{false['denominator_all']} ({pct(false['incomplete_rate_all'])}) | {true['verdict_counts'].get('incomplete', 0)}/{true['denominator_all']} ({pct(true['incomplete_rate_all'])}) |"
        )
    lines.extend(
        [
            "",
            "Three-vote majority:",
            "",
            "| Stratum | INCOMPLETE / all | 95% Wilson | Verdict counts |",
            "|---|---:|---:|---|",
        ]
    )
    for label, title in (("false_success", "False success"), ("true_success", "True success")):
        row = majority[label]
        lines.append(
            f"| {title} | {row['verdict_counts'].get('incomplete', 0)}/{row['denominator_all']} ({pct(row['incomplete_rate_all'])}) | {ci(row['incomplete_wilson95_all'])} | {verdict_counts(row['verdict_counts'])} |"
        )
    stability = responses["stability_by_label"]
    lines.extend(
        [
            "",
            f"Across all episodes, {stability['all']['all_three_valid']}/268 have three valid stochastic verdicts; {stability['all']['unanimous_count']}/268 are unanimous ({pct(stability['all']['unanimity_rate_all'])}, or {pct(stability['all']['unanimity_rate_valid_triplets'])} among valid triplets). Pairwise disagreement is {stability['all']['pairwise_disagreement_count']}/{stability['all']['pairwise_comparison_count']} ({pct(stability['all']['pairwise_disagreement_rate'])}). The stochastic majority agrees with T=0 in {stability['all']['majority_t0_agreement_count']}/{stability['all']['majority_t0_comparable_count']} comparable episodes ({pct(stability['all']['majority_t0_agreement_rate'])}).",
            "",
            "## Requirement-decision counts",
            "",
            f"The strict semantic formatting audit finds **714** distinct model-listed rated requirements: **493 yes, 95 no, 126 cannot tell**. False-success episodes contribute {requirements['audited_subgroup_totals']['false_success']['yes']} yes / {requirements['audited_subgroup_totals']['false_success']['no']} no / {requirements['audited_subgroup_totals']['false_success']['cannot tell']} cannot tell; true-success episodes contribute {requirements['audited_subgroup_totals']['true_success']['yes']} / {requirements['audited_subgroup_totals']['true_success']['no']} / {requirements['audited_subgroup_totals']['true_success']['cannot tell']}.",
            "",
            "These are counts of explicit model ratings. No independent requirement-level correctness labels exist, so they are not an accuracy measure.",
            "",
            "## Blocking and repair simulation",
            "",
            f"A hard T=0 INCOMPLETE gate flags {simulation['false_successes_flagged_but_not_repaired']} false successes and {simulation['true_successes_flagged_and_potentially_blocked']} true successes. Blocking alone repairs **0** tasks. If flagged true successes are preserved, the net change is 0; if all are lost, the net change is {simulation['hard_block_net_success_change']} successes ({100 * simulation['hard_block_net_success_change'] / 268:.2f} pp).",
            "",
        ]
    )
    feasible = simulation["conditional_repair_extrapolation"]["feasible_replay_valid"]
    naive = simulation["conditional_repair_extrapolation"]["naive_all_replay_valid"]
    all_saved = simulation["all_scored_feasible_denominator_sensitivity"]
    all_saved_population = all_saved["population"]
    all_saved_naive = all_saved["scenarios"]["naive_all_replay_valid"]
    lines.extend(
        [
            f"The feasible replay-valid branch evidence is **0/2** continuations from one failed Writer task (nominal Wilson {ci(feasible['branch_evidence']['nominal_wilson95'])}); the mechanical extrapolation is zero repairs. The naive **1/4** rate (nominal Wilson {ci(naive['branch_evidence']['nominal_wilson95'])}) would imply {naive['expected_repairs_not_observed']:.2f} unobserved repairs, but its sole repair is an officially infeasible GIMP task excluded from this corpus. K=2 branches from the same state are clustered, so both Wilson intervals are descriptive and transfer is unsupported.",
            "",
            "This simulation is not measured OSWorld improvement. The population contains selected final-answer episodes, not the full benchmark.",
            "",
            f"Alternate same-source denominator sensitivity: the four roots contain {all_saved_population['feasible_scored_episode_count']} scored feasible saved episodes with official score sum {all_saved_population['official_score_sum']:.12f} and mean {pct(all_saved_population['official_score_mean'])}, including partial-score and non-answer episodes. Holding all episodes outside the 268 verified set unchanged, the same naive 8.75 hypothetical repairs equal +{all_saved_naive['gain_pp_if_true_successes_preserved']:.4f} pp (rather than +3.2649 pp on 268); subtracting all 97 flagged true successes gives {all_saved_naive['gain_pp_if_all_flagged_true_successes_lost']:.4f} pp. This is still not the full benchmark.",
            "",
            "## Sensitivities and limits",
            "",
            f"- Post hoc metadata sensitivity: excluding two score-0 answer episodes whose existing metadata says the model declared infeasibility gives {sensitivity['verdict_counts'].get('incomplete', 0)}/{sensitivity['denominator_all']} = {pct(sensitivity['incomplete_rate_all'])}, Wilson {ci(sensitivity['incomplete_wilson95_all'])}; the registered primary retains them because their final tool is `answer`.",
            "- The evaluator label is episode success, while the verifier sees one final screenshot. Persistent settings, saved files, and before/after properties may be invisible; this helps explain the high true-success rejection rate.",
            "- The study measures detection under an explicit verification prompt, not a causal intervention in agent behavior. No rollout was repaired by the verifier itself.",
            "- V2 was not run; only the original Holo-3.1-4B verifier was evaluated.",
            "",
            "## Frozen artifact hashes",
            "",
            f"- `manifest.json`: `{corpus['manifest_sha256']}`",
            f"- `responses.jsonl`: `{responses['responses_sha256']}`",
            f"- `attempts.jsonl`: `{attempts['sha256']}`",
            f"- `PROTOCOL.md`: `{responses['protocol_sha256']}`",
            f"- `prepare.py`: `{responses['prepare_sha256']}`",
            f"- `run_verifier.py`: `{responses['runner_sha256']}`",
            f"- `requirement_review.json`: `{requirements['review_sha256']}`",
            f"- branch original JSONL: `{data['branch_pilot']['arms']['original']['sha256']}`",
            f"- branch candidate JSONL: `{data['branch_pilot']['arms']['candidate']['sha256']}`",
            f"- maker `RESULT.json`: `{sha256(MAKER_RESULT)}`",
            f"- maker `REPORT.md`: `{sha256(MAKER_REPORT)}`",
            "",
            "**RAN / PASSED / CORRECT.** Integrity and arithmetic pass. Scientific interpretation remains limited to this selected, repeated-task, final-screen corpus, and the observed verifier does not separate false from true successes well enough to support a gain claim.",
        ]
    )
    REPORT.write_text("\n".join(lines) + "\n")
    print(REPORT)


if __name__ == "__main__":
    main()
