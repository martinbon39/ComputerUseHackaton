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

## Targeted update during collection — contemporary reference and no-action outcomes

Reviewed the updated `analyze.py` (`bd67d19897ca0a5dae5f6ac81430b836ea82fa7293e2956c13d9b8427bb97170`) and `HOLO31_REFERENCE.json` (`8293760ce851119dfda22deb398953273ab222d314896a02b9a7d2b6cd87822d`). This remains an audit of analysis logic during collection, not a final cohort verdict. No runner, endpoint, VM, live branch data, instruction, or trajectory was inspected.

### Findings on revision `bd67d1` — resolved in revision `a91a5d`

1. **Resolved: a score-1 branch with no new action was counted and modeled as a repair.** Revision `a91a5d` preserves it in the preregistered official-score endpoint but assigns zero action-qualified repair credit, keeps it in the refusal denominator, and excludes it from repair-labelled rates, episode repair counts, repair-credit bootstrap, and prediction benefit.

2. **Resolved and correction to this review: the Holo3.1 intervals use different finite Monte Carlo specifications.** The nine included episode differences are `[1, 0.5, 0, 0, 0, 0, 0, 0, 0]`, with mean 1/6. The source analysis used 10,000 draws and seed 0 and reported `[0, 0.444]`; the rescue-analysis recomputation uses 20,000 draws and seed 1701 and gives `[0, 0.3888889]`. My previous statement that this could not be Monte Carlo ambiguity was too strong: the exact bootstrap distribution identifies the population percentile, but a finite Monte Carlo estimate can fluctuate across seeds and draw counts. `HOLO31_REFERENCE.json` now preserves and labels both methods instead of treating either as the other.

### Checks that pass

- **Primary versus available data:** a temporary mixed-completeness fixture confirmed that `primary` includes only complete, common-valid K=2 episode pairs, while `all_available_descriptive` includes every successful available branch and is explicitly labelled descriptive. An incomplete branch affected only the descriptive count.
- **No double counting between those sections:** primary and descriptive values are separate named summaries; the descriptive section is not added to the primary denominator. Within each summary, every successful slot appears once because duplicate successful `(task, arm, k)` keys still hard-fail.
- **Calibration overlap:** the task-ID extraction works on temporary manifests. The frozen aggregate manifests yield exactly three reserve overlaps (`37608790-...`, `386dbd0e-...`, `aa4b5023-...`) and zero test overlaps. The report correctly says reserve transport is not an independent held-out validation.
- **Contemporary versus historical baselines:** `HOLO31_REFERENCE.json` keeps the completed contemporary 18-branch-per-arm primary distinct from the frozen historical 0/10 snapshot, and the report warns that neither is a randomized Holo4 arm.

Those findings concerned analysis and reporting only and are resolved below. They did not imply any verdict about the still-collecting rescue cohort.

## Provisional re-review — revision `a91a5d`

**Provisional PASS for the corrected analysis logic; no blocker found in this revision. This is not the final numerical cohort audit.** Reviewed hashes: `analyze.py` `a91a5df382215852343c8d2a1b80914175bcff5ba25e644b1e7edbbcf2c8673d`, `PREREG.md` `60dbb022bc7be548d53a92bf5d8ee645e1ff3f93946d136b7ec5950bc0607941`, and `HOLO31_REFERENCE.json` `f4b8d3d9459830316250c9c6c71aa1166b0cc6d2b14a841c966272aaf05c8f23`. No runner, VM, endpoint, or live branch artifact was read.

Temporary CPU fixtures covered a no-action score1, an acted score1, an acted partial score, an episode with Guard checks but no refusal, an incomplete episode contributing only to the descriptive summary, and a separate complete dataset with zero refusals.

- **Official endpoint and repair credit: PASS.** In the mixed fixture, the Guard official endpoint retained 2/6 score1, split into one no-action success and one success after action. Among four refused branches, official mean score was .625 while action-qualified repair credit was .375. The no-action score1 received zero credit; the acted score1 received 1; the acted partial score received .5; the failed branch received 0. The action-qualified full-repair rate was 1/4. All four refusals remained in the denominator.
- **No-refusal handling: PASS.** The complete non-refusal episode remained in the paired official primary but did not enter the conditional denominator. In a cohort with zero refusals, conditional credit and rate remained `null`, all 20,000 conditional bootstrap draws were explicitly recorded as no-refusal, prediction remained unestimated, and no loss scenarios were emitted.
- **Bootstrap and prediction: PASS.** Conditional credit and full-rate intervals resample episode clusters and filter draws with no refusal rather than converting them into failures. Prediction uses `mean_action_qualified_repair_credit` and its matching cluster interval. In the fixture it used r=.375, not the official conditional mean .625; the loss-zero reserve prediction exactly equaled `(2/10) × (45/66) × .375`, and its interval was the transformed repair-credit interval.
- **Primary versus descriptive: PASS.** The incomplete branch appeared only in `all_available_descriptive`; it did not enter the complete common-valid K=2 primary. Official score1 and after-action counts are shown side by side without adding descriptive observations to primary denominators.
- **Report labels: PASS.** The report calls the preregistered outcome “Official score1”, labels after-action results separately, states the conditional result as “score1 outcomes after a new action”, discloses refused no-action successes, defines r as action-qualified credit with no-action credit zero, and retains the evaluator-state caveat that action alone does not prove the state was initially failing.
- **Holo3.1 intervals: PASS, with a non-impacting method-text discrepancy.** Recomputing the published nine episode differences with the rescue method (20,000 draws, seed 1701) reproduces `[0, 0.3888889]`. The report separately names that recomputation and the source 10,000-draw/seed-0 Monte Carlo result `[0, 0.444]`; the historical 0/10 snapshot remains distinct. `HOLO31_REFERENCE.json` describes the upper index as `floor(.975*draws)-1`, while `analyze.py::interval()` uses zero-based index `floor(.975*draws)`. Both indices yield .3888889 here because of ties, so the reported interval is unaffected; the method text should still be aligned with the implementation.
- **Clarification timing and scope: PASS.** The 09:35 clarification preserves the official endpoint and all outcomes while defining a conservative action-qualified prediction credit. It does not relabel the prediction as observed gain.

Final status still depends on reconstructing the completed cohort from its frozen branch results and matching `RESULT.json` and `REPORT.md`; that audit remains pending.
