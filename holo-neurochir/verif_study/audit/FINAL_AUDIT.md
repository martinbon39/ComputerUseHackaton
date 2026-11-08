# Independent final audit — final-screen verifier study

**Verdict: PASS WITH LIMITATIONS.** The registered calculations and raw-artifact integrity are correct. The measured verifier is not a useful discriminator in this corpus: it flags 53.03% of false successes and 48.02% of true successes at T=0, a difference of only 5.01 percentage points with a task-cluster interval spanning zero.

## RAN

- `python3 -m unittest -v test_audit_verif.py`
- `python3 audit/audit_verif.py --output audit/AUDIT_RESULT.json`
- Independent reconstruction from the four raw OSWorld result trees, task JSON files, copied PNGs, raw responses/attempts, and raw branch-pilot JSONL files. Maker summaries were not used as numerical evidence.

## PASSED

- Corpus: 352 source trajectories reconstructed; 268 eligible episodes exactly match the manifest (66 false successes, 202 true successes).
- Screens: all 268 source and copied PNG hashes match; all are 1920×1080, reference the final answer record, and match the final trajectory step; duplicate image hashes: 0.
- Schedule: 1072/1072 logical responses, no missing/unexpected/duplicate IDs, no request-setting/body-hash/model mismatch, and reasoning is nonempty in 1072 responses.
- Runtime: observed maximum concurrency 4; retries 0; maximum gap between completions 25.07s; attempts started at/after deadline 0; raw-response copy mismatches 0.
- Requirement audit: all 27 semantic correction entries match frozen T0 raw lines and their before/after arithmetic; raw-line SHA256 `e2e8ed64763c6b0f6e1b5f938c310ecec6bcb79ececd0ff38d16e0c0319f2455`.

## CORRECT — primary T=0 result

| Ground-truth stratum | INCOMPLETE / all | 95% Wilson | INCOMPLETE / valid verdicts | 95% Wilson | Verdict counts |
|---|---:|---:|---:|---:|---|
| False success (score 0) | 35/66 (53.03%) | [41.16%, 64.57%] | 35/63 (55.56%) | [43.32%, 67.15%] | incomplete=35, complete=28, truncated=2, missing=1 |
| True success (score 1) | 97/202 (48.02%) | [41.23%, 54.88%] | 97/199 (48.74%) | [41.89%, 55.65%] | incomplete=97, complete=102, truncated=2, missing=1 |

Detection minus false-rejection rate: **5.01 pp**. The independent audit's 20,000-draw joint task-cluster bootstrap interval is [-13.48, 23.16] pp; the stratum intervals are false success [36.84%, 68.66%] and true success [36.82%, 59.51%]. The maker report uses the preregistered 10,000 draws, so small Monte Carlo differences between its intervals and these independent sensitivity intervals are expected.

The episode-level Wilson intervals treat repeated rollouts as independent. That assumption is weak here: 245/268 episodes belong to 67 repeated-task groups; there are only 90 unique tasks, and 18 repeated groups change label across passes.

## T=0.8 stability

| Replicate | False-success INCOMPLETE | True-success INCOMPLETE |
|---|---:|---:|
| t08_r1 | 37/66 (56.06%) | 100/202 (49.50%) |
| t08_r2 | 44/66 (66.67%) | 102/202 (50.50%) |
| t08_r3 | 38/66 (57.58%) | 89/202 (44.06%) |

Three-vote majority:

| Stratum | INCOMPLETE / all | 95% Wilson | Verdict counts |
|---|---:|---:|---|
| False success | 40/66 (60.61%) | [48.55%, 71.50%] | incomplete=40, complete=25, missing=1 |
| True success | 98/202 (48.51%) | [41.72%, 55.37%] | incomplete=98, complete=103, missing=1 |

Across all episodes, 258/268 have three valid stochastic verdicts; 178/268 are unanimous (66.42%, or 68.99% among valid triplets). Pairwise disagreement is 162/784 (20.66%). The stochastic majority agrees with T=0 in 227/260 comparable episodes (87.31%).

## Requirement-decision counts

The strict semantic formatting audit finds **714** distinct model-listed rated requirements: **493 yes, 95 no, 126 cannot tell**. False-success episodes contribute 124 yes / 47 no / 28 cannot tell; true-success episodes contribute 369 / 48 / 98.

These are counts of explicit model ratings. No independent requirement-level correctness labels exist, so they are not an accuracy measure.

## Blocking and repair simulation

A hard T=0 INCOMPLETE gate flags 35 false successes and 97 true successes. Blocking alone repairs **0** tasks. If flagged true successes are preserved, the net change is 0; if all are lost, the net change is -97 successes (-36.19 pp).

The feasible replay-valid branch evidence is **0/2** continuations from one failed Writer task (nominal Wilson [0.00%, 65.76%]); the mechanical extrapolation is zero repairs. The naive **1/4** rate (nominal Wilson [4.56%, 69.94%]) would imply 8.75 unobserved repairs, but its sole repair is an officially infeasible GIMP task excluded from this corpus. K=2 branches from the same state are clustered, so both Wilson intervals are descriptive and transfer is unsupported.

This simulation is not measured OSWorld improvement. The population contains selected final-answer episodes, not the full benchmark.

Alternate same-source denominator sensitivity: the four roots contain 315 scored feasible saved episodes with official score sum 210.118782996693 and mean 66.70%, including partial-score and non-answer episodes. Holding all episodes outside the 268 verified set unchanged, the same naive 8.75 hypothetical repairs equal +2.7778 pp (rather than +3.2649 pp on 268); subtracting all 97 flagged true successes gives -28.0159 pp. This is still not the full benchmark.

## Sensitivities and limits

- Post hoc metadata sensitivity: excluding two score-0 answer episodes whose existing metadata says the model declared infeasibility gives 33/64 = 51.56%, Wilson [39.58%, 63.37%]; the registered primary retains them because their final tool is `answer`.
- The evaluator label is episode success, while the verifier sees one final screenshot. Persistent settings, saved files, and before/after properties may be invisible; this helps explain the high true-success rejection rate.
- The study measures detection under an explicit verification prompt, not a causal intervention in agent behavior. No rollout was repaired by the verifier itself.
- V2 was not run; only the original Holo-3.1-4B verifier was evaluated.

## Frozen artifact hashes

- `manifest.json`: `67cc43166d6b13094f858fd11cc631a2c21aa5379638837fa71572255a673fdc`
- `responses.jsonl`: `86b45eb5a71d61fd8d07291428117746a6acfac0a80567a303f24a63399b004d`
- `attempts.jsonl`: `86b45eb5a71d61fd8d07291428117746a6acfac0a80567a303f24a63399b004d`
- `PROTOCOL.md`: `737ee316595423f64927400e298857b8b88a89f3e1ba6a2365501acd5dab9b7d`
- `prepare.py`: `7b55f7a69a87a7faff004f94c60df63acc5176db39c10a3209763ba9fe831294`
- `run_verifier.py`: `84e2456ac6e655fab088d644f38e29ead9f8344642ab2ca3325c62cc6ab83640`
- `requirement_review.json`: `cec6de383cffed256dce3fa55726096b088f25d366461843f1160cc0c94d8e12`
- branch original JSONL: `1675e99a3c60d8963ed89dd6323f0305954bc24c8c2d7732a7b0ce522a2e2fc4`
- branch candidate JSONL: `6c63911fc3082e4092f7b9abdf2445492bc3475657495570bf4a60599b928694`
- maker `RESULT.json`: `bcfe3c7c17be1bd6694ff9674c61d8c03aba563cabc3c5e330628316c284c612`
- maker `REPORT.md`: `a5826427ca36c1e7f0faca761c25709b976ef1a2fa1feceead6100f2412cfe9b`

**RAN / PASSED / CORRECT.** Integrity and arithmetic pass. Scientific interpretation remains limited to this selected, repeated-task, final-screen corpus, and the observed verifier does not separate false from true successes well enough to support a gain claim.
