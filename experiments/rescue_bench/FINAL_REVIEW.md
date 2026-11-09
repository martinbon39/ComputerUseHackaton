# Final independent numerical review

Reviewed 2026-11-08 after final regeneration. The reviewer did not author `analyze.py` or the result artifacts.

## Verdict

- **RAN:** independent reconstruction from the three archived JSONL journals; 20,000-draw episode-cluster bootstraps with Python `random.Random(1701)`; prediction reconstruction; reference checks; `python3 experiments/rescue_bench/verify_analysis.py`; and `bash reproduce/run_all.sh` from `/home/orbit/worktrees/rescue-bench`.
- **PASSED:** all numerical comparisons, provenance checks, durable synthetic regressions, and the required repository quickstart. Both commands exited 0; `verify_analysis.py` printed `verify_analysis: PASS`, and the repository check printed `QUICKSTART OK`.
- **CORRECT:** the final `RESULT.json` and `REPORT.md` match the archived branch records for the registered primary, strict-boundary sensitivity, all-complete sensitivity, conditional repair, action-qualified prediction, references, and disclosed exclusions. No statistical blocker was found.
- **NOT RUN:** screenshot inspection, model-output semantic review, evaluator/getter validation, VM or endpoint checks, and worker-process/runtime review. Those were explicitly outside this numerical audit. The report carries forward the separate raw-evidence finding that required-output retrieval failed for d682 control K1 and all four aa4 VLC branches.

## Reviewed artifacts

| Artifact | SHA-256 |
|---|---|
| `analyze.py` | `5278e1f3570d0513aa8beaa05ce287612db8e3deb4f1efa650472c7bfebfef42` |
| `REPORT.md` | `f6102faeeea0b82f4d44738cb070050598ba2102909482d33896bcd113aee927` |
| `RESULT.json` | `f9629465c61ced492239b66954c9321e700d84d66f7ecb8ea0fd5d2ce2cffdfa` |
| `data/branches.jsonl` (4 rows) | `0d923702879d8c8212da4d4e0d263510b47c8822578c77b12d2022b0345b68e6` |
| `data/branches.s0-of-2.jsonl` (20 rows) | `d7c654ccf0204889cfa3f03649ee16bbe9582292489e9cff1a4be9ba3401a5f5` |
| `data/branches.s1-of-2.jsonl` (24 rows) | `8a96e76130ee3a356adc62cc1a21a39a34969ae908b853efb5f3126716281be4` |

The 48 rows form exactly the 12 tasks × 2 arms × K=2 expected slots. All `(task, arm, k)` keys are unique, all slots are present, and no archived row contains an infrastructure-error outcome. The branch hashes embedded in `RESULT.json` match these files byte for byte.

## Independent reconstruction

The reconstruction used only archived scalar fields such as task, arm, K, official score, replay validity, escalation, tool names, and call counts. It did not import or call `analyze.py`.

| Cohort | Episodes | Guard official score1 | Control official score1 | Guard after-action score1 | Control after-action score1 | Mean score difference | Episode-cluster bootstrap 95% CI |
|---|---:|---:|---:|---:|---:|---:|---:|
| Registered primary | 9 | 11/18 | 2/18 | 9/18 | 0/18 | 0.500 | [0.222222, 0.777778] |
| Strict boundary | 8 | 10/16 | 2/16 | 8/16 | 0/16 | 0.500 | [0.125, 0.875] |
| All complete | 12 | 11/24 | 3/24 | 9/24 | 1/24 | 0.333333 | [0.041667, 0.625] |

Primary arm means independently reconstruct to 11/18 = 0.611111 for Guard and 2/18 = 0.111111 for control. Five primary episodes favor Guard, none favor control. The three common primary exclusions are the two VLC episodes and `multi_apps/f5c13cdd`; each is excluded because at least one of its four branches is replay-invalid.

The sole strict-only exclusion is `multi_apps/d68204bf`: it remains in the registered primary because all four branches pass the primary replay criterion, while control K1 fails the boundary criterion. `per_episode` correctly records primary exclusion `null` and strict exclusion `boundary_invalid`. Its official zero remains in the primary.

The all-complete sensitivity retains the genuine f5 control K1 correction: its control scores are `[0, 1]`, and K1 includes new actions. This accounts for the one control after-action score1 in the 12-episode sensitivity; it does not enter the 9-episode primary because other f5 repetitions are replay-invalid.

## Conditional repair and uncertainty

The primary contains 11 refused Guard branches across six episodes. Nine reach official score1 after a new action, two remain zero, and none is a no-action score1. Therefore:

- action-qualified full-repair rate = 9/11 = 0.818182;
- action-qualified mean repair credit = 9/11 = 0.818182;
- episode-cluster bootstrap 95% interval for both = [3/7, 1] = [0.428571, 1];
- five of six refused episodes have at least one full repair;
- one of 20,000 primary bootstrap draws contains no refusal and is disclosed and omitted from the conditional percentile distribution.

The strict sensitivity independently reconstructs to 8/10 action-qualified repairs with interval [1/3, 1]. The all-complete sensitivity reconstructs to 9/13 with interval [1/3, 1]. Official no-action score1 outcomes are retained in arm-level official counts but contribute zero action-qualified repair credit; in the final primary they occur twice in each arm and not among refused branches.

All bootstrap intervals above were independently regenerated by resampling episode IDs with replacement, keeping both K repetitions and both arms inside each episode cluster, for 20,000 draws with seed 1701. They exactly match `RESULT.json`.

## References and prediction

The report keeps the two Holo3.1 references distinct:

- historical 08:36 snapshot: five valid episodes, 0/10 official score1 in each arm, a non-concurrent partial snapshot;
- completed contemporary experiment: nine common-valid episodes, Guard 5/18 versus no-Guard 2/18, paired mean difference 0.167. The independently regenerated 20,000-draw/seed-1701 interval is [0, 0.388889], while the preserved source 10,000-draw/seed-0 Monte Carlo interval is [0, 0.444].

The online-gain section is correctly labelled a prediction rather than a measurement. Using independently reconstructed repair credit `r = 9/11`, detection 45/66, and false rejection 21/202 gives:

| Split | Gain coefficient | Loss coefficient | Predicted change if loss=0 | loss=0.5 | loss=1 |
|---|---:|---:|---:|---:|---:|
| Reserve45 | 0.075758 | 0.034653 | +0.061983 | +0.044657 | +0.027330 |
| Test120 | 0.142045 | 0.051980 | +0.116219 | +0.090229 | +0.064239 |

Every scenario and repair-only interval in `RESULT.json` equals `gain_coefficient × r − loss_coefficient × assumed_loss`, with the repair-credit interval transformed by the same formula. Reserve has three calibration-task overlaps and is correctly disclosed as not independently held out; test has zero overlap. Loss after false rejection, transport error, infeasible false claims, and partial-score endpoints remain unmeasured and outside these intervals.

## Report consistency and limits

`REPORT.md` agrees with `RESULT.json` on the primary 9/12 cohort, 11/18 versus 2/18 official outcomes, 9/11 conditional repairs, strict 8-episode and all-complete 12-episode sensitivities, prediction scenarios, and both Holo3.1 references. It explicitly states that required-output retrieval failed for d682 control K1 and all four aa4 VLC branches, retains their official zeros, and describes the f5 control K1 success as a real correction excluded from primary only because other episode repetitions fail replay validity.

The positive primary interval is evidence for this selected conditional replay cohort under its registered complete-case rule. It is not an observed reserve/test gain. Complete-case exclusion, replay-state identity, output-getter failures, prevalence and judge-rate uncertainty, false-rejection loss, and transport remain material limitations as described in the report.
