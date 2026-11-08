# Rescue benchmark

Status: **partial**; 21/48 branches completed. Updated 2026-11-08T09:54:54.865280+00:00.

This is a conditional replay experiment, not an observed reserve/test online gain.

All collected branches, including incomplete pairs (descriptive only): Guard 5/11 score1, of which 4 after a new action; control 0/10 score1, of which 0 after a new action.

## Paired primary analysis

| Arm | Official score1 / branches | After a new action | Mean official score (cluster 95% CI) |
|---|---:|---:|---|
| Claude Guard → Holo4 | 4/10 | 4 | 0.400 [0.000, 0.800] |
| Holo4 without Guard | 0/10 | 0 | 0.000 [0.000, 0.000] |

Primary: 5/12 episodes, all four K=2 branches complete with valid replay. Guard−control mean score difference: **0.400**, episode-cluster 95% CI **[0.000, 0.800]**.

After an actual initial Guard refusal: 4/6 score1 outcomes after a new action, across 3 episodes. Full repair rate CI: [0.000, 1.000]. Action-qualified score credit: 0.667, CI [0.000, 1.000]. Refused no-action successes: 0.

Official score after at least one new non-answer tool; zero otherwise. A no-action success remains in official scores and the refusal denominator but receives zero repair credit. Actions alone do not establish that replay state was initially failing.

20,000 episode-cluster bootstrap draws, fixed seed 1701. Degenerate intervals at all-zero/all-one outcomes do not establish certainty; episode-any Wilson intervals estimate a different, K=2 estimand.

Companion any-repair-in-K2 episode estimate: 2/3; Wilson95 [0.208, 0.939]. This is a different estimand from per-branch repair probability.

| Episode | Guard K0, K1 | Control K0, K1 | Primary exclusion |
|---|---|---|---|
| libreoffice_impress/550ce7e7 | K0=0.000, K1=0.000 | K0=0.000, K1=0.000 | none |
| libreoffice_impress/70bca0cc | K0=1.000, K1=1.000 | K0=0.000, K1=0.000 | none |
| libreoffice_calc/37608790 | K0=1.000, K1=1.000 | K0=0.000, K1=0.000 | none |
| libreoffice_impress/7dbc52a6 | K0=0.000, K1=0.000 | K0=0.000, K1=0.000 | none |
| multi_apps/716a6079 | K0=0.000, K1=0.000 | K0=0.000, K1=0.000 | none |
| libreoffice_impress/8979838c | K0=1.000 | pending | incomplete |
| multi_apps/d68204bf | pending | pending | incomplete |
| vlc/386dbd0e | pending | pending | incomplete |
| multi_apps/f5c13cdd | pending | pending | incomplete |
| libreoffice_writer/0b17a146 | pending | pending | incomplete |
| libreoffice_calc/1de60575 | pending | pending | incomplete |
| vlc/aa4b5023 | pending | pending | incomplete |

Strict replay + boundary: 5 episodes; paired difference 0.400, CI [0.000, 0.800].

All complete, ignoring replay validity: 5 episodes; paired difference 0.400, CI [0.000, 0.800].

The control resumes at the same recorded answer boundary without running the Guard. The treatment inserts the recorded answer and frozen Claude feedback and escalates only on refusal. No second Guard is applied during rescue. This estimates the full handoff policy, not feedback alone.

## Holo3.1 reference

The requested historical 08:36 snapshot is 0/10 in each arm: five episodes repeated twice, not ten independent episodes. Any-repair episode Wilson95 is [0, 0.434]. The paired bootstrap is degenerate at zero. It is not a concurrent third arm.

The completed contemporary Holo3.1 experiment (15 turns) has 5/18 official score1 with Guard versus 2/18 without Guard across nine common-valid episodes. Mean paired difference 0.167; independently recomputed 20k/seed1701 CI [0.000, 0.389]. The source 10k/seed0 Monte Carlo CI was [0.000, 0.444]; methods and both values are preserved in HOLO31_REFERENCE.json.

Two official successes in each Holo3.1 arm come from immediate answers without new actions on Impress/8979838c. These are replay-state drift, not continuation repairs. The three additional Guard successes follow actions (Calc2, Writer1). The reference uses 15 turns versus Holo4's 20 and a different Guard policy; no randomized Holo4-versus-Holo3.1 effect is claimed.

## Predicted online gain — not measured

Δ = p(feasible false completion) × P(Guard rejects | false completion) × r − p(true completion exposed to Guard) × P(false rejection | true completion) × loss.

Here r=0.667 is action-qualified score credit after refusal, with no-action successes credited zero. Frozen Claude detection is 45/66 and false rejection is 21/202. Loss after falsely rejecting a true success is unmeasured; scenarios below are assumptions, not measured harms.

| Split | Feasible false completions | Exposed true completions | Formula in percentage points | Break-even r if loss=1 |
|---|---:|---:|---|---:|
| reserve45_modal_original | 5/45 | 15/45 | 7.5758 * r - 3.4653 * loss | 45.7% |
| test120_modal_original | 25/120 | 60/120 | 14.2045 * r - 5.1980 * loss | 36.6% |

| Split | Assumed loss | Predicted change (pp) | Repair-only 95% CI (pp) |
|---|---:|---:|---|
| reserve45_modal_original | 0% | +5.05 | [0.000, 7.576] |
| reserve45_modal_original | 50% | +3.32 | [-1.733, 5.843] |
| reserve45_modal_original | 100% | +1.59 | [-3.465, 4.110] |
| test120_modal_original | 0% | +9.47 | [0.000, 14.205] |
| test120_modal_original | 50% | +6.87 | [-2.599, 11.606] |
| test120_modal_original | 100% | +4.27 | [-5.198, 9.007] |

repair_only_bootstrap95 conditions on prevalence, judge rates and assumed loss; excludes transport error and loss uncertainty

Transport from selected short feasible replay episodes and an external judge corpus is an assumption. Infeasible false claims and partial-score endpoints are outside this formula. Three calibration task IDs overlap reserve; none overlap test. Reserve is therefore not an independent held-out validation. Neither split was rerun here.

## Verification and limits

Initial Guard checks: 11; refusals: 6; verifier errors: 0. Infrastructure error attempts: 0. Missing or invalid replays are disclosed, never converted into successes.

Pixel replay validity does not guarantee evaluator-state identity. Zero-action positive scores are retained as official outcomes but receive zero repair credit in the prediction. A new action by itself also cannot prove the handoff state was failing. Common complete-case exclusion may induce selection bias; intervals do not capture that bias or transport uncertainty.

RESULT.json contains per-episode scores, exclusions and source hashes. Raw calls, screenshots, boundary contexts, Guard journals and official evaluator outcomes are under /home/orbit/osw/rescue_bench/. FROZEN.json checks unchanged Guard and harness sources; compatibility.json records the one-step schema check. Runner and scheduling review: VERIFY_RUNNER.md and SCHEDULING_REVIEW.md. First Calc pairing audit: FIRST_REPAIR_REVIEW.md. Complete Calc and Impress K2 repair audit: MEASURED_REPAIRS_REVIEW.md. Final numerical review is pending.
