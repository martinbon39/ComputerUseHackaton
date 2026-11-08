# Independent final statistical verification

**RAN/PASSED/CORRECT**

Command: `/workspace/venv/bin/python /workspace/astra/proof-anchor/verify_results.py --expect-result-sha 00525ab78b91af451c5c812c3dc446c7939e52f739e70a7c6db25e7e311511fd --expect-report-sha 3da344d15ee1ae2c148690fffaac2c58882b865d49a766de34f18b32e86b6682`

Exit code: 0.

The checker independently reconstructs margins, paired bootstrap summaries, exact rank statistics, cosine neighbors, label permutations, oracle power and supplemental score diagnostics. It does not import the maker’s analysis functions.

- **RAN:** All requested numerical groups and report tables.
- **PASSED:** 10098 checks; all groups passed.
- **CORRECT:** The frozen results and report agree with the stored evidence within the declared exploratory scope.

- provenance_and_immutable_core: {"passed": true, "referenced_artifacts": 15, "core_sha256": "80ab8c7ec4b031ea82c339f53294752d84351a3c82673f62c6d7d127023f4398"}
- raw_cohort: {"passed": true, "forwards": 156, "tasks": 39, "labels": {"false_finish": 19, "true_finish": 20}, "capture_hashes": 39}
- anchoring: {"passed": true, "paired_bootstraps": 10000, "interaction_label_permutations": 10000, "ratios_recomputed": true, "nonnull_tasks": 38}
- original_probe_statistics: {"passed": true, "configurations": 72, "baseline_summaries": 8, "paired_baseline_comparisons": 291, "original_mlp_warning_count": 702}
- cosine_and_permutations: {"passed": true, "raw_residual_knn_vectors": 36, "complete_permutations": 1000, "tail_count_including_ties": 41, "unadjusted_p": 0.04195804195804196}
- oracle_power: {"passed": true, "independently_checked_exact_thresholds": {"one_sided_05": 250, "two_sided_05": 261, "familywise_72": 301}, "replayed_effects": 91, "simulations_per_effect": 20000}
- mlp_sensitivity: {"passed": true, "score_vectors": 18, "fold_diagnostics": 702, "warning_folds": 232, "no_model_refit": true}
- report: {"passed": true, "checked_table_numbers": 416, "primary_probe_cells": 72, "supplemental_cells": 18, "interpretation_limits_present": true}

**NOT RUN / limits:**

- No model or GPU execution; no source or weight mutation.
- No fresh logistic or MLP cohort fits; their statistics were recomputed from stored OOF scores.
- No supplemental MLP permutation test, as declared in the amendment.
- Source, evaluator, replay, and weight audit contents were linked by hashes; their external original files were not re-read here.
- No claim of future-performance confidence coverage, absence of a discriminator, or behavioral improvement.

**Verified versions:**

- `RESULT.json`: `00525ab78b91af451c5c812c3dc446c7939e52f739e70a7c6db25e7e311511fd`
- `RESULT_CORE.json`: `80ab8c7ec4b031ea82c339f53294752d84351a3c82673f62c6d7d127023f4398`
- `REPORT.md`: `d1ada976f4979755cc8e4f369a385e8eb90dd9ff392c8596fe5034c3965cc0f5`
- `verify_results.py`: `06aac0c7a7657153343a1ef5cee3bbb5451c15e308553aa837c98b4ae4729de9`

The original 72-probe family and the 18-cell post-result optimization sensitivity remain distinct. Fixed-OOF bootstrap intervals are descriptive; the corrected 1,000-permutation primary test cannot reject at 5%.

The final report subsequently received one sentence distinguishing margin attenuation from a change in tool ranking. Removing that exact addition reconstructs the numerically audited report SHA256 `3da344d15ee1ae2c148690fffaac2c58882b865d49a766de34f18b32e86b6682`. The new report SHA256 is `d1ada976f4979755cc8e4f369a385e8eb90dd9ff392c8596fe5034c3965cc0f5`; `RESULT.json` is unchanged. A targeted read-only check confirmed 37 positive condition-b margins out of 39, exit code 0. Its complete reproduction command is retained in `VERIFY_FINAL.json` under `report_revision_check`. The numerical checker was not rerun.
