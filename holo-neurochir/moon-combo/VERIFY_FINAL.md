# Final consistency verification

**Status: PASS**  
**RAN:** yes · **PASSED:** yes · **CORRECT:** yes · **NOT RUN:** none.

Read-only reconciliation covered 1,100 raw generation rows (five arms × 220), `RESULT.json`, three analysis files, three admission audits, U12/U32/K32/key verifier reports, `REPORT.md`, and `cleanup.json`. No GPU, server call, or weight rescan was performed.

## Result

All reported candidates remain REJECT; no online candidate is admitted.

All raw arms have the same 220 `(task_id, seed)` rows: 76 fs+ across 19 tasks, 80 fs− across 20 tasks, and 64 healthy across 16 tasks. `RESULT.json` matches raw summaries and SHA-256 values for U12/U32/K32; the three analyses match `RESULT.json`.

The task-level fs− audit matches raw rows: A 18 four-of-four / 1 zero; B 14 / 2; U12 14 / 2; U32 14 / 2; K32 15 / 3. K32’s only B differences are Writer `66399…` 1→0, Multi-apps `227d…` 3→4, and Impress `2cd…` 3→2, therefore it does not restore B globally.

## Verifier chain

- U12 keeps the original failed keyset report and has a passing strict role-contract resolution with passing negative controls.
- U32 and K32 numerical verifier reports are PASS with 724 tensors, 64 protected writers, and no recorded failures.
- Key provenance JSON is PASS and the Markdown status is PASS (no stale `FAIL` marker).
- `cleanup.json` attests all seven owned pod PIDs absent, candidate checkpoint paths absent, tunnel absent, and capture SHA matching local provenance. This verifies the cleanup claim from that artifact; no live process probe was performed here.

## Check table

| Check | Result |
|---|---|
| raw_completeness_and_pairing | PASS |
| raw_strata_counts | PASS |
| result_cohort_and_draw_accounting | PASS |
| U12_result_raw_summary_and_sha | PASS |
| U12_analysis_matches_result | PASS |
| U32_result_raw_summary_and_sha | PASS |
| U32_analysis_matches_result | PASS |
| K32_result_raw_summary_and_sha | PASS |
| K32_analysis_matches_result | PASS |
| U12_behavior_audit_raw_metrics_and_reject | PASS |
| U32_behavior_audit_raw_metrics_and_reject | PASS |
| K32_behavior_audit_raw_metrics_and_reject | PASS |
| K32_true_finish_task_level_nuance | PASS |
| U12_preserved_initial_failure_and_strict_resolution | PASS |
| U32_weight_verifier | PASS |
| K32_weight_verifier | PASS |
| key_provenance_verifier_and_markdown_status | PASS |
| REPORT_markdown_decision_counts_and_K32_nuance | PASS |
| RESULT_all_admission_decisions_reject | PASS |
| cleanup_attestation_from_cleanup_json | PASS |
