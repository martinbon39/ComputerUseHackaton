# Rescue benchmark

Status: **partial**; 4/48 branches completed. Updated 2026-11-08T09:21:48.054030+00:00.

This is a conditional replay experiment, not an observed reserve/test online gain.

| Arm | Full repairs / branches | Mean official score | Episodes with any full repair |
|---|---:|---:|---:|
| Claude Guard → Holo4 | 0/2 | 0.0 | 0/1 |
| Holo4 without Guard | 0/2 | 0.0 | 0/1 |
| Historical Holo3.1 + Guard, 15 turns | 0/10 | 0 | 0/5 |

Primary cohort: 1/12 episodes; all four branches must have a valid replay. Strict boundary sensitivity: 1 episodes.

Paired mean score difference Guard−control: 0.0; episode-cluster 95% interval [0.0, 0.0].

Conditional repair after an actual initial refusal: 0/2 branches from 1 episodes. Score bootstrap interval: [0.0, 0.0]; companion episode-any-repair Wilson interval: [0, 0.7934506856227626].

20,000 episode-cluster bootstrap draws, fixed seed 1701. Degenerate intervals at all-zero/all-one outcomes do not establish certainty; episode-any Wilson intervals estimate a different, K=2 estimand.

The control resumes at the same recorded answer boundary without running the Guard. The treatment inserts the recorded answer and the frozen Claude feedback and escalates only on refusal. No second Guard is applied during rescue. This estimates the full handoff policy, not feedback alone.

The historical 0/10 reference is five episodes repeated twice, not ten independent episodes. It used 15 turns and is not a concurrent third arm.

## Prediction (not measured online gain)

Δ = p(feasible false completion) × P(Guard rejects | false completion) × E(score after rescue | rejected) − p(true completion exposed to Guard) × P(false rejection | true completion) × E(score loss | false rejection).

Frozen judge estimates: detection 45/66; false rejection 21/202. Loss after false rejection is unmeasured. Reserve/test prevalence is aggregated from final metadata only. Calibration transfers from selected short feasible episodes and an external judge corpus; that transfer is an assumption. Infeasible false completions and partial-score endpoints are outside this repair estimate.

Prediction status: scenario prediction; not an observed online gain.

## Evidence and limitations

`RESULT.json` contains all per-episode scores and exclusions. Raw calls, screenshots, original boundary contexts, Guard journals and official outcomes are under `/home/orbit/osw/rescue_bench/`. `FROZEN.json` checks the unchanged Guard and harness sources; `compatibility.json` records the one-step schema check. Independent review: `VERIFY_RUNNER.md`; final numerical review pending.

Infrastructure error attempts: 0. Missing or invalid replays are disclosed, never converted into successes. No global gain claim is justified by a positive point estimate alone.

| Split | Predicted change, percentage points | Break-even repair if every false rejection loses its success |
|---|---|---:|
| reserve45_modal_original | 7.5758 * r - 3.4653 * loss | 45.7% |
| test120_modal_original | 14.2045 * r - 5.1980 * loss | 36.6% |

reserve45_modal_original:
- Assumed loss 0%: predicted +0.00 pp; repair-only 95% interval [0.0, 0.0] pp.
- Assumed loss 50%: predicted -1.73 pp; repair-only 95% interval [-1.73, -1.73] pp.
- Assumed loss 100%: predicted -3.47 pp; repair-only 95% interval [-3.47, -3.47] pp.

test120_modal_original:
- Assumed loss 0%: predicted +0.00 pp; repair-only 95% interval [0.0, 0.0] pp.
- Assumed loss 50%: predicted -2.60 pp; repair-only 95% interval [-2.6, -2.6] pp.
- Assumed loss 100%: predicted -5.20 pp; repair-only 95% interval [-5.2, -5.2] pp.

repair_only_bootstrap95 conditions on prevalence, judge rates and assumed loss; excludes transport error and loss uncertainty

Three calibration task IDs overlap the reserve; none overlap the test. Reserve transport is therefore not an independent held-out validation. Neither split was rerun here.
