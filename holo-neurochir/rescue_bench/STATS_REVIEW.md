# Independent statistical review

Reviewed 2026-11-08 after the 09:11 UTC scheduling amendment. Reviewer did not author `analyze.py`. This is a **provisional PASS with no statistical blocker found in the reviewed code and frozen aggregate inputs**. It is not the final numerical audit: `/home/orbit/osw/rescue_bench/` contained only `compatibility.json` and `pilot.log`, with no `branches*.jsonl`, at review time.

## Scope and independence

Reviewed only:

- `analyze.py` (`03e2373eaf1918c771f954fac4c43905bfdd92d2beca020b137ae6702ef1f0f6`)
- `PREREG.md` (`b68582cb21995e0f6784c3de4793f8f4a232826981d5eac60188c6dbe6e97502`)
- `PREVALENCE.json` (`ecf2078b937f772d419b16d3cb86b74381ca06a5fb19e45e07b7dd4f73ac2b6d`)
- `JUDGE_CLUSTERS.json` (`a723cb2638ca786e070e97b8d85dc502c8b3a8d9558c3a88d00fb2c820674b4b`)
- historical snapshot `paper/data/local/feci_guard/repair/snapshot/results.json` (`59ea8f318b7aa8501f34f189cc2f4ede990f257d715d5a552eca1e8de193819b`)

No endpoint, VM, reserve/test instruction, or trajectory was opened. The live pilot journal was not read. Repository `HEAD` and `origin/main` were equal (0 ahead, 0 behind); the required rebase could not run because the shared checkout already had unrelated unstaged changes and no upstream was configured.

## Findings

1. **K=2 dependence and paired estimand: PASS.** Both replicates remain inside the episode cluster. The point estimate is the mean of the 12 paired episode-level differences. Because every included episode has exactly K=2 in both arms, the pooled arm means inside each cluster-bootstrap draw are algebraically the same as averaging the per-episode K means. Resampling episode IDs preserves pairing and within-episode correlation. The bootstrap is deterministic (20,000 draws, seed 1701).

2. **Conditional repair denominator: PASS.** Conditional repair selects only Guard rows where `escalated` is true, i.e. an actual refusal under the registered runner contract. Pass/error branches do not enter this denominator. It reports both branch-level outcomes and an episode-any companion. A synthetic case with three escalated branches across two episodes produced the expected 2/3 full-repair rate and 11/12 mean score; a no-refusal case remained `null`, with all 20,000 bootstrap draws explicitly counted as having no refusal rather than being converted to zero.

3. **Duplicate, error, and complete-case handling: PASS.** Error attempts are retained in `infrastructure_error_attempts` and excluded from outcomes. A later successful retry can fill the slot. A second successful `(task, arm, k)` outcome hard-fails. Primary inclusion requires all four successful slots and replay validity; strict-boundary and all-complete sensitivities are separate. Synthetic checks confirmed these behaviors. One limitation to retain in the final report is that exclusion can still induce selection bias; the code discloses exclusions but cannot remove that bias.

4. **Partial official scores: PASS.** Scores are validated as finite in `[0,1]`; full repair is `score >= 1`, progress is `score > 0`, and mean official score preserves fractional credit. A synthetic `[1, 1, .25, .75]` Guard sample yielded 2 full repairs, 4 progress branches, and mean .75. The prediction correctly excludes partial-score prevalence from its binary calibration and names that unmeasured stratum. Test120 contains five exposed partial-answer episodes; they are reported in `PREVALENCE.json` and are not silently treated as binary successes or failures.

5. **Frozen prevalence and judge rates: PASS.** Inputs are exactly p(FS feasible/exposed) = 5/45 and 25/120, p(TS exposed) = 15/45 and 60/120, detection = 45/66, and false-positive rejection = 21/202. Re-summing all 90 unique task clusters in `JUDGE_CLUSTERS.json` reproduces 45/66 and 21/202 exactly. Synthetic prediction checks reproduced both gain and loss coefficients.

6. **Prediction versus measurement: PASS.** Output repeatedly labels the calculation as a scenario prediction rather than observed online gain. It exposes the unmeasured loss after a false rejection, gives loss scenarios and fixed-prevalence bounds, and states that its repair-only interval conditions on prevalence, judge rates, transport, and loss. It also names infeasible false completions, partial-score endpoints, and transport error as outside the identified estimate. No online-gain claim follows from the predicted point estimate.

7. **Historical snapshot: PASS.** The frozen Holo3.1 snapshot has 5 complete episodes, K=2, 0/10 repairs in each arm, with two incomplete episodes dropped. `analyze.py` describes it as historical, non-concurrent/non-randomized, and uses a five-episode Wilson denominator rather than treating ten correlated branches as independent episodes.

## Final-audit gate

Do not promote this provisional review to a final PASS until the complete `branches*.jsonl` set exists. The final independent audit should rerun `analyze.py` on a read-only copy or otherwise avoid overwriting canonical outputs, then reconstruct from aggregate branch fields: unique 48 successful slots; all error attempts and exclusions; per-episode K means; primary/strict/all-complete cohorts; conditional-refusal denominators; fractional-score summaries; bootstrap reproducibility; prediction coefficients; and exact agreement between `RESULT.json` and `REPORT.md`. Any mismatch in those reconstructions is a blocker. Missing branches or a partial run are reportable results, not grounds to infer efficacy.
