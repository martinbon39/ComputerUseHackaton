# Online result: Holo-3.1-4B + Feci Guard on the OSWorld test split (120 tasks)

Rule: `PREREG_ONLINE_GUARD.md` (written before launch, three amendments, all before any comparison).
Analysis: `online_guard_analysis.py`, committed at 10:36 UTC before the Guard results were read (b52c9f6).
Raw output: `ONLINE_GUARD_RESULT.json`.

## Setup
- **Guard arm.** Holo-3.1-4B served on Modal (`Holo-3.1-4B-modal-orig`). Feci Guard is the frozen verifier `0af76fdb`, with Claude Sonnet as judge, reached through the relay on orbit. At most 2 refusals per episode, 50 steps max, GitHub Actions runners with KVM.
- **Runs.** 42468308809, 42468884640 and 42472655505. The last two rerun tasks lost to infrastructure: a GitHub 504 at setup, and a runner that lost contact with GitHub.
- **Primary comparator.** The original agent, same Modal deployment, same runners and harness (`results_test_gh_orig_modal_test`).
- **Secondary comparator.** The original agent served by the pod (`results_test_gh_orig`).
- **Coverage.** 120/120 tasks, 0 excluded. The judge returned 104 verdicts with 0 errors: 22 refusals, 74 accepted complete, 2 passed at the refusal cap, 6 infeasible answers not checked.

## Results (paired by task, bootstrap 10,000, seed 0)
| | Original (Modal) | + Feci Guard | Difference [95% CI] |
|---|---|---|---|
| **False "done" rate** (criterion 1) | 22.5 % (27/120) | **10.8 % (13/120)** | **−11.7 pts [−19.2 ; −4.2]** |
| OSWorld score (criterion 2) | 58.6 | 60.2 | +1.6 [−4.4 ; +7.7] |

**Benefit / cost (rule 5)**
- Tasks repaired (B, 0 → 1): 8.
- True successes lost (C, 1 → 0): 4.
- Net gain B − C: +4.
- False "done" avoided (E): 19, so E / C = 4.75.
  - Of these 19, **7 became successes** and **12 ended without a false "done"**: the agent reached the step cap without answering, or ended otherwise.
  - Separately, **5 tasks that were not false "done" for the original became false "done" with the Guard**. The net count therefore goes 27 → 13 (−14), not −19.
  - B = 8 includes 1 task that was not a false "done" for the original. Only **7 of the 8 repairs are repaired false "done"**.

**Noise reference.** The original against itself (pod vs Modal, same 120 tasks) flips 9 tasks 1 → 0 and 5 tasks 0 → 1.

**Secondary analysis (pod comparator).**
- False "done" rate: −13.3 pts [−20.8 ; −5.8].
- Score: +0.1 [−6.5 ; +6.6].
- B = 8, C = 8.

## Decision under the preregistered rule
- **Criterion 1 is formally met.** The false "done" rate falls from 22.5 % to 10.8 %, and the upper bound of the CI is below 0. The secondary comparator gives the same result. The fall is not attributable to the Guard (see "Attribution" below).
- **Criterion 2 is not met.** The score gain is +1.6 points, and the CI includes 0. **No OSWorld score gain is claimed.**
- **Rule 5 is formally met.** The net gain is ≥ 0 and false "done" goes down, so the rule declares the Guard useful; given the attribution below, this verdict does not show an effect of the Guard.
  - The number of true successes lost (4) is within the original's own run-to-run noise (9 flips 1 → 0).

**In one sentence.** Online, on 120 held-out tasks, the guarded run's false "task complete" claims fell from 22.5 % to 10.8 %, which formally meets the registered criterion, but about two thirds of the drop come from episodes in which the Guard never ran, so it is not attributed to the Guard; no measurable loss of score. Holo-3.1 alone rarely turns a refusal into a success. The repair gain comes from escalation to Holo4, which is measured on replays (`rescue_bench/REPORT.md`, +50 pts [22 ; 78]) and was not run online.

## Attribution (added after the result, 2026-11-08; not part of the registered analysis)
The registered criterion compares the two arms; it does not say what caused the difference. Split by what the Guard could do in each guarded episode (Modal original as comparator; `meta.json` `feci_guard.answers` and `.refusals`; recomputed in `paper/figs/guard.py`, table `paper/generated/tab_guard_online.tex`):

| Guarded episode | n | refusals | false "done", original | false "done", guarded | B (0→1) | C (1→0) | 50 steps, original | 50 steps, guarded |
|---|---|---|---|---|---|---|---|---|
| agent never answered (Guard never ran) | 28 | 0 | 9 | 0 | 1 | 1 | 17 | 28 |
| answered, Guard never refused | 75 | 0 | 12 | 10 | 5 | 1 | 2 | 0 |
| Guard refused at least once | 17 | 22 | 6 | 3 | 2 | 2 | 5 | 10 |
| answered at least once (rows 2 and 3) | 92 | 22 | 18 | 13 | 7 | 3 | 7 | 10 |
| all tasks | 120 | 22 | 27 | 13 | 8 | 4 | 24 | 38 |

- In 28 of 120 guarded episodes the agent never called `answer`, so the Guard never ran. The original had 9 false "done" on those tasks: 9 of the net drop of 14 (27 → 13) involve no Guard action.
- Never answering is within the original's own run-to-run variation: 28 tasks with the Guard, 23 for the original on Modal, 20 for the original on the pod. The guarded arm and the Modal original disagree on 11 vs 6 tasks (exact McNemar p = 0.33); the two servings of the original disagree on 5 vs 8.
- The guarded loop is the original loop up to the first `answer` (same 50-step budget, T = 0.8, unseeded, same prompt and checkpoint); a refusal only consumes a step and the episode continues. The 38 guarded episodes at the step limit are the 28 that never answered and 10 that were refused, then ran out of steps.
- Where the Guard could act (92 tasks answered at least once), false "done" goes 18 → 13; this part was not registered as a separate test and is not tested here. On the 17 tasks the Guard refused (22 refusals), false "done" goes 6 → 3, 2 tasks go 0 → 1 and 2 go 1 → 0.
- So about two thirds of the drop come from episodes in which the Guard never ran, consistent with the sampling noise of an unseeded agent. We do not claim that the Guard lowers the false "done" rate online. A seeded replication, or the same guarded loop with a neutral verifier that always returns COMPLETE on the same 120 tasks, would settle it; neither has been run.
- Registration history: three amendments, all before any comparison (09:27 benefit/cost rule, 09:37 Modal comparator, 10:43 rerun of 6 tasks; the 114-task secondary analysis registered in amendment 3 is not reported). The 7 shards rerun after setup failures are listed under Deviations, not in an amendment.

## Deviations from the preregistration
1. **Comparator** (amendment 2, before any Guard episode ran). The pod went down at about 09:30 UTC, so the agent was served by Modal. The primary comparator became the original served by the same Modal deployment. The pod-served original is reported as secondary.
2. **Rerun of infra-dead tasks.**
   - 7 shards failed at setup: a GitHub 504, and a race in the VM-image wait. They were rerun with identical settings.
   - One job lost contact with GitHub. Its 6 tasks were rerun once (amendment 3, before any comparison).
   - Final coverage is 120/120 tasks.
3. **Arms not run.** The reserve-split replication (45 tasks) and the online Holo4 escalation arm were planned but not run: the pod was lost, and the Modal budget had to stay within its cap. The escalation is measured only on replays (`rescue_bench/`).
4. **Judge route.** The judge was reached through the relay `feci_guard/guard_server.py` on our server, through an SSH tunnel limited to the relay port. It was not the Anthropic API. The verifier code is unchanged (`0af76fdb`). The Claude model is the CLI alias `sonnet`, and its version is not pinned.
