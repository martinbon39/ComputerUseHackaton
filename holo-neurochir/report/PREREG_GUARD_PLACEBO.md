# Supplementary pre-registration: does the guard's verdict matter, or does any refusal do the same? (arm D)

Written 2026-11-09, approved by Martin the same day, and committed before any episode of A, B, C or D exists.
Code and analysis: `guard_attribution/` at 8fc9c3e (`analysis_placebo.py`, `neutral_verifier.PlaceboFeci`).
It supplements `PREREG_GUARD_ATTRIBUTION.md` (frozen, b8d2ddd and 26565da). It changes nothing in that study's arms,
outcomes, primary criterion, secondaries, exclusions or stop rule. It adds one arm and one supplementary analysis, and
it declares the deviations of the frozen study's implementation.

## Why
The frozen primary criterion compares the real guard (C) with a verifier that never refuses (B). A refusal can lower
false "done" without any judgment: a refused answer often ends at the 50-step limit, which is not a false "done".
To measure this, an independent simulation was fitted to our runs
(`holo-neurochir/guard_attribution/placebo_power.py`). Its inputs:
- outcome rates of the original loop: answered right 0.588, answered wrong 0.233, never answered 0.179
  (`results_test_gh_orig_modal_test` and `results_test_gh_orig`);
- intra-task correlation of false "done" 0.53, measured between those two runs;
- post-refusal transitions from the 17 refused episodes of `results_test_gh_orig_guard_claude`.

Under that model, a verifier that refuses at random with the guard's observed rate (r = 0.23) meets the frozen
criterion in 27 % of 1,000 replications (effect −1.9 pts). This assumes the seeding holds (A, B, C and D reach the
same first answer). With seeding holding in 70 % or 40 % of episodes, it is 22 % or 17 %. The real guard, with its
offline accuracy, meets it in 100 %. The random refuser's power depends mostly on what happens after a refusal, which
our data fix poorly (5 + 5 episodes): over a grid of plausible values it ranges from 0.4 % to 78 %. So "criterion met"
alone cannot show that the verdict, rather than the act of refusing, lowers false "done".

The lab's statistics review reached the same conclusion with its own model: effect −1.7 to −2.0 pts, criterion met in
37-38 % (private repo `martinbon39/lab`, `projects/cogito/experts/stats.md` S1, commit 1ebe93e). Our effect agrees;
our rate is lower. A first version of our simulation re-checked accepted answers and gave 34.5 %; an independent
review found the bug, and the numbers here are after the fix.

## Arm D: placebo refusal
- **Loop and plumbing.** `feci_guard/run_holo_guard.py`, unchanged, run like B and C through
  `guard_attribution/arms.py`. Same checkpoint, vLLM, seeds, 50 steps, prompt v2, tasks and VM image.
- **Verifier stub.** `neutral_verifier.PlaceboFeci`:
  - Each answer sent to the verifier is refused with probability r = 0.23. This is C's rate per verifier call in the
    earlier online run: 22 refusals in 96 calls. The guard.jsonl files hold 104 decisions: 74 accepted, 22 refused,
    6 infeasible and 2 passed at the cap, of which only 96 reached the verifier. `ONLINE_GUARD_RESULT.md:12` calls all
    104 "verdicts". Per episode, the first answer was refused in 17 of 86 cases (0.20). r is fixed here, before any
    data.
  - A refusal carries one fixed message: "Verifier: the task is not complete yet. Check on the screen that every
    requirement of the task is met before answering. Continue the task." Its form follows the real guard's feedback,
    without information about the task.
  - The draw is a function of (study seed, task id, index of the verifier call in the episode), so reruns of an episode
    draw the same refusals.
  - The latency is drawn exactly as in B for the same call.
- **Rules shared with C** (they live in `GuardedAgent`): answers that declare the task infeasible are not checked; at
  most 2 refusals, then the next answer passes. As in C, when the fresh screenshot cannot be taken there is no verdict
  and the answer passes. D never has other judge errors, while C can (fail-open); C's errors are reported.
- **No Claude call** in D.

## Design
- 4 arms × 3 seeds × 120 TEST tasks = 1,440 episodes, of which 360 are new (D).
- The arms of a task run back to back, with the order rotated by task (ABCD, BCDA, CDAB, DABC).
- Each task runs on one vLLM server for all four arms.

## Exclusions, reruns, stop rule
- The frozen rules apply to A, B and C exactly as written:
  - infra-dead episodes are rerun once;
  - a task dead after its rerun is dropped from A, B and C for that seed;
  - the 10 % stop rule after seed 0 is computed on A, B and C only.
- D's episodes follow the same rerun rule.
- A (task, seed) dropped by the frozen rule is also dropped from D.
- A (task, seed) where only D is dead after its rerun is dropped from this supplementary analysis only. It is never
  dropped from the frozen analysis.

## Supplementary primary criterion
**C − D on the false-"done" rate.** Per task, false "done" is averaged over the valid seeds in each arm. The paired
difference C − D is taken over the tasks, with a bootstrap over tasks (10,000 draws, seed 0, 95 % percentile interval),
the same statistic as the frozen primary.
- **Met** if the upper bound is < 0: the guard's verdict lowers false "done" beyond what refusing at the same rate does.
- **Kill rule.** C's realised refusal rate is computed in seed 0: refusals divided by answers that got a verdict
  (not infeasible, not passed at the cap, not without a verdict). If it lies outside [0.115, 0.46] (a factor of 2
  from r), D is not a matched placebo. Then C − D, on false "done" and on score, is reported as descriptive only, and
  D is reported as "random refusal at rate 0.23".
- Expected power (same simulation):
  - 1.00 if the guard detects 68 % of false answers online, as offline;
  - 0.93 at 45 % (0.85 if seeding holds in 70 % of episodes);
  - 0.40 at 30 % (0.34).

## Secondary analyses (reported, do not decide)
1. **D − B on false "done"**: the effect of random refusal.
2. **Score.** C − D (a gain over placebo is claimed only if the lower bound is > 0) and C − B.
3. **Competing risks, per arm.** Counts of true done, false done, step cap, and other.
4. **Sign-flip p-values.** Two-sided randomisation p-values (100,000 Monte Carlo sign flips over tasks, seed 0) for
   C − D false "done" and score, alongside the bootstrap.
5. **Realised refusal rates** of C and D, per seed, and the number of episodes in C and D that end on a refused
   answer. These count as false "done" by the frozen definition, and D adds refusals.

C − B on score here uses the four-arm valid set. The frozen secondary 2 remains the reference for C − B.

Analysis script: `guard_attribution/analysis_placebo.py`, committed with this document. Tests are in
`guard_attribution/tests/test_placebo.py`: a planted C − D effect is recovered, no effect is not claimed, and the kill
rule fires.

## Declared deviations of the frozen study's implementation (`guard_attribution/README.md`)
These apply to the frozen study whether or not D runs, and will be listed in its result:
1. Step index = the loop's `steps` counter. A retried request at the same step gets a retry index k
   (seed = f(s, task, step, k)), so a parse retry does not resend the same seed.
2. The 10 % stop counts infra-dead **first attempts** among seed-0 episodes of A, B and C, before reruns.
3. Reruns of a seed run after that seed's main pass. They are not interleaved.
4. The arm order is rotated by task. With D, the rotation is ABCD, which changes when A, B and C episodes run but not
   what they are.
5. The model is served as `Holo-3.1-4B-orig` (earlier: `Holo-3.1-4B-modal-orig`). The name is not in the prompt.
6. The vLLM host is the 8 × H100 node instead of Modal (same GPU type). The VM host is the H100 node if Martin chooses
   option 2 (the prereg says GitHub runners). Both are the same across arms.
7. Step cap = the loop's step counter reached 50 (`meta.json` `steps`), not the `traj.jsonl` line count.
8. A model-server outage in the middle of an episode is scored, per the infra-dead definition. Failed requests are
   counted and reported.
9. `preflight --probe-verifier --go` makes one Claude call outside arm C, as a check before any episode.
10. `VLLM_BATCH_INVARIANT` is **off**. The kernels stay as in the earlier run, and same-seed outputs may diverge under
    batching (measured by the frozen secondary 3).

11. Code changed after the frozen study's commits (7aac210, f9c0f07, 3f66e6a) and before any episode, to add D:
    - `analysis.py`: `load()` takes the arms to read, defaulting to A, B, C. The ledger listing now excludes D rows.
      The frozen statistics are unchanged.
    - B's recorded `verifier_sha` changes from `neutral-b76422a8` to `neutral-63939f75`. It now hashes only the
      latency data and B's code, so later edits to D do not change it.
    - Every episode of every arm now saves the screen after scoring (`final_screen_after_eval.png`) next to its step
      screenshots. This takes up to about 45 s more on a dead VM, after scoring.

## Priority if the H100 window is short
The frozen study has priority. Before seed 0, the pilot measures the time per episode. If the window cannot hold
1,440 episodes at that rate plus reruns, D is not run; this is decided before any data. If time runs short during
the run, D is stopped first. D's completed seeds are reported as such, and A, B and C continue.

## Budget
- 360 more episodes, about 21 VM-hours at the earlier run's 3.5 min per episode (an estimate, to be measured by the
  pilot).
- GPU: the same 8 × H100 window, about 33 % longer.
- No Claude calls in D: 0 USD of verifier cost. The frozen study's C calls stay at about 300, about $9.

## What will be written
Whatever the outcome, the paper's §7 reports C − D with its interval and the kill-rule check.
- C − D met: §7 may say that the verdict, not refusal as such, lowers false "done", and by how much.
- C − D covering 0: §7 says the guard's online effect cannot be told apart from a refusal effect.
