# Pre-registration: is the online drop in false "done" caused by the guard or by the loop?

Written 2026-11-08 ~22:45 UTC, before any run of this study. No episode of arms A, B or C below exists at the time of
writing. Analysis script to be committed before any result is read, as for `PREREG_ONLINE_GUARD.md` (b52c9f6).

## Why
The pre-registered online test (`PREREG_ONLINE_GUARD.md`, result `ONLINE_GUARD_RESULT.md`) met its criterion: false "done"
22.5 % → 10.8 % on the 120 TEST tasks. The post-submission review showed the drop is not attributable to the guard:
in 28 of the 120 guarded episodes the agent never called `answer`, so the guard never ran, and 9 of the 14 avoided false
"done" are on those tasks (paper §7, Table `tab:guard-online`). The agent samples at T = 0.8 with no seed, so two runs of
the same agent differ (never-answered: 28 guarded, 23 original on Modal, 20 original on the pod).

## What is already known about the two loops (code diff, 2026-11-08)
`GuardedAgent.run` (`feci_guard/run_holo_guard.py:124`) was compared line by line with the original loop
(`HoloComputerAgent.run`, RealtimeGUI @a763361 `Agent/holo_agent/agent.py:217-299`, run by the runner workflow
`holo_repro/run_holo.py`). Up to the first `answer` call the two loops are the same code path: same `max_steps` (50),
same parse-retry and error limits, same sampling (T 0.8, top_p 0.9, max_tokens 3072, reasoning medium, no seed),
same history (last 3 screenshots), same prompt (v2, byte-identical `system_prompt.txt` on 120/120 tasks), same
infeasible handling. Differences:
1. On `answer`, the guarded loop takes an extra fresh screenshot and calls the verifier (median latency ≈ 6-9 s) before
   deciding. The original stops at once.
2. A refusal consumes one step, appends the verifier's feedback as a tool output, and the episode continues (max 2
   refusals). The original never continues after `answer`.
3. Logger name (cosmetic).
So, before the first `answer`, any difference between A and B can only come from sampling randomness or environment
timing, not from code. Arms are therefore run with fixed sampling seeds.

## Arms (same 120 TEST tasks, `osworld/split_test.json`, same seeds)
- **A — original loop**: `holo_repro/run_holo.py`, no guard.
- **B — guarded loop, neutral verifier**: `run_holo_guard.py` with a stub verifier that always returns COMPLETE, after a
  delay drawn from the recorded latencies of the real verifier in `results_test_gh_orig_guard_claude`
  (`meta.json` → `feci_guard.verifier_latency_s`), so that the only difference with C is the verdict.
- **C — guarded loop, real guard**: `run_holo_guard.py` with the frozen verifier (sha `0af76fdbacc72317`, Claude Sonnet,
  passive mode, max 2 refusals, fail-open, infeasible answers not checked), identical to the earlier online run.

Common to all arms: Holo-3.1-4B original checkpoint (sha256 as in `osworld/modal_deploys/20261108T093735_*`), same vLLM
version and args, same GPU type, max 50 steps, prompt v2, the same OSWorld copy and VM image.
**Seeds**: 3 seeds s ∈ {0, 1, 2}. For each request, the vLLM sampling seed is a fixed function of (s, task id, step
index), identical across arms. The seed plumbing is a code change to be made, tested on one task, and committed before
any arm runs; with it, A and B should produce identical actions up to the first `answer` when the environment is
deterministic. vLLM batching is not bitwise deterministic, so this is checked, not assumed (secondary 3).
**Design**: 3 arms × 3 seeds × 120 tasks = 1,080 episodes. Arm order is interleaved by task so that time-of-day and
server-load drifts hit all arms alike.

## Outcomes (per episode, as in `online_guard_analysis.py`)
- false "done": last tool `answer` and score 0;
- score: official OSWorld score;
- never answered: no `answer` call in the episode;
- step cap: 50 steps reached.

## Primary criterion (the one that decides)
**B vs C on the false-"done" rate.** Per task, average false "done" over the 3 seeds in each arm; paired difference
C − B over the 120 tasks; bootstrap over tasks, 10,000 draws, seed 0, 95 % percentile interval.
The guard is said to reduce false "done" **only if the upper bound of the interval is < 0.**

## Secondary analyses (reported, do not decide)
1. **A vs B** (effect of the loop with a neutral verdict), same statistic. Expected ≈ 0 given the diff above.
2. **Score C − B** with the same statistic. No score gain is claimed unless the lower bound is > 0.
3. **Seed fidelity**: share of (task, seed) pairs where A and B take identical actions up to the first `answer`.
4. **Never-answered and step-cap rates** in each arm; and the primary criterion restricted to tasks where the C episode
   called `answer` at least once in every seed (descriptive only; this subset is post-treatment).
5. **Benefit / cost of C vs B**: B_rep (score 0 → 1), C_lost (1 → 0), false "done" avoided, as in rule 5 of
   `PREREG_ONLINE_GUARD.md`, using per-seed pairs.
6. Per seed, the same primary statistic, to show the spread.

## Exclusions and reruns
An episode is infra-dead if it plays 0 steps or the runner fails before scoring (setup error, lost runner, model check
failure). Infra-dead episodes are rerun once with the same seed and settings; if still dead, the task is dropped from
all three arms for that seed. Every rerun and drop is listed in the result. No other exclusion. No hand-picked subset:
all 120 TEST tasks, or none.

## Budget and stop rule
- Compute: the H100s provided for 2026-11-09 serve the agent; VMs on the GitHub runners as before. Claude verifier calls
  only in C: about 100 per seed (≈ 300 in all, ≈ 0.03 $ each).
- Hard stop: if after the first seed of all three arms more than 10 % of episodes are infra-dead, stop and fix the
  infrastructure before continuing. Seeds already run are kept and reported.
- If the H100s are not available, the study is not run on a sub-sample; it waits.

## What will be written
Whatever the outcome, the paper §7 and `ONLINE_GUARD_RESULT.md` will report the primary criterion with its interval,
the A vs B result, and any deviation from this document. If the primary criterion is not met, the paper keeps the
statement that the online drop is not attributed to the guard.
