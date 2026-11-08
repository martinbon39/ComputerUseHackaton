# Feci Guard — results

## Verifier, hand tests (2026-11-08)
| capture | truth | passive (Claude Sonnet) | active (Claude Sonnet) |
|---|---|---|---|
| vlc/386dbd0e final screen (global hotkey) | false success | COMPLETE (setting not visible: cannot_tell) | NEED_CHECK: open Tools > Preferences > Hotkeys |
| vlc/9195653c final screen (max volume 200 %) | true success | COMPLETE | not run |
Latency 6.5-10.6 s, about $0.04 per check. A single final screen cannot show a saved setting, which is why the
active mode exists.

## End-to-end, 1 task on an orbit VM (guard on, passive, Claude Sonnet)
`libreoffice_impress/550ce7e7` (strike through lines 1 and 2). The original recorded a false success on this task in
results_diag. Journal: `smoke/impress_550ce7e7_guard.md`.
- Step 29: the agent answered "done". The guard REFUSED it: "the strike-through stops at 'Requ'; 'ests.' is plain
  text". The evidence was correct, as the screenshot shows.
- Steps 30-33: the agent followed the feedback (Home/Shift+End, strike-through, Ctrl+S).
- Step 34: answered again. COMPLETE, so the answer passed.
- The official evaluator still scored **0**. It compares the saved .pptx with a reference file, and the remaining
  difference is not visible on screen (the final screenshot shows both lines fully struck through). This is the
  limit of a screen-only verifier: the guard fixed what can be seen, and the evaluator checks what cannot.

## Offline: three judges on the same 268 episodes (judge_bench, final screen only)
Claude Sonnet with the Feci Guard verifier catches 68 % of false successes [56–78] and wrongly rejects 10 % of true
successes [7–15]. That is a gap of +58 pts, task-bootstrap CI [+41, +74]. Holo-3.1-4B: 53 % / 48 % (+5, [−13, +23]).
Holo4-27B: 47 % / 31 % (+16, [−3, +33]). Table and caveat (prompt differs for Claude) in README.md;
source `../judge_bench/`.

## Repair measure (registered, see PREREG.md; numbers independently recomputed from the raw jsonl)
12 feasible false successes of the original agent, replayed up to the recorded answer. For each, K=2 continuations
per arm with at most 15 new steps, on the same server at the same time, scored by the official evaluator. 9 episodes
have a valid replay in all 4 branches (3 excluded: f5c13cdd, vlc/386dbd0e, vlc/aa4b5023).

| 9 episodes × 2 branches | no guard | guard (Claude Sonnet, passive) |
|---|---|---|
| Repaired (official score 1) | 2/18 | **5/18** |
| Answered "done", still wrong | 15 | 6 |
| No answer within 15 steps | 1 | 8 |
| Mean new steps | 1.4 | 8.6 |

- Paired difference per episode (mean over K, guard − no guard): **+16.7 pts, 95 % bootstrap CI [0, +44]**.
  2 episodes are better with the guard and 0 are worse; the sign test gives p = 0.5. **The effect cannot be told
  apart from zero.** With all 12 episodes: +12.5 pts [0, +33].
- The guard refused in 12 branches (6 episodes), 16 refusals in all. 3 of these branches ended repaired, 25 %
  (Wilson 95 % CI 9–53 %), from 2 episodes:
  - **calc/1de60575, 2/2 against 0/2 without the guard.** The verifier saw that the pivot table was on a tab named
    "Pivot Table_Sheet1_1", not "Sheet2". The agent renamed it in 5 steps and the second check passed (demo:
    `~/osw/feci_demo/calc_1de60575/`).
  - writer/0b17a146, 1/2: scored 1 at the step limit without answering again.
- impress/8979838c succeeds in all 4 branches as soon as the agent answers. Its recorded false success does not
  reproduce under replay, so it accounts for both no-guard repairs and 2 of the 5 guard repairs. Only 3 repairs are
  specific to the guard.
- Costs and failures:
  - 7 refused branches reached the 15-step limit without answering again. A refusal itself counts as a step, as
    registered.
  - 2 branches (impress/550ce7e7) were let through by the cap while still wrong; the difference there is invisible on
    screen.
  - On 2 episodes (impress/7dbc52a6, multi_apps/716a6079) the guard accepted wrong answers (COMPLETE) in all 4
    branches.
- What is measured is a refusal **plus coaching**: the feedback contains Claude's suggested next action, for example
  the menu path. It is not refusal alone.
- Headline: on 9 replay-valid episodes, the guard repaired 3 of its 12 refused branches (2 episodes), while the
  no-guard arm repaired nothing beyond a flaky task. The paired gain, +17 pts [0, +44], cannot be told apart from
  zero, and most refusals ended without an answer within 15 steps.
Raw data: `~/osw/feci_repair/{nog,guard}/branches.jsonl`; analysis: `analyze_repair.py` -> `repair/results.json`.

## Rescue harness, real 1-task run (run_holo_guard_rescue.py, 09:20 UTC, orbit VM)
impress/550ce7e7, with Holo-3.1-4B as the agent, Claude Sonnet as the Guard (CLI) and Holo4-27B on Modal as the
rescue model. Journal: `smoke/impress_550ce7e7_rescue_guard.md`.
- Step 11: Holo-3.1 answers "done". The Guard refuses: "the strike-through ends after 'Budget Request', the 's.' is
  not struck".
- Steps 12-15: Holo4-27B takes over with the history and the feedback. It selects the line (Home, Shift+End), applies
  strike-through and saves, using 5 rescue calls.
- Step 16: the Guard checks again: COMPLETE.
- The official score is 0, as in the guard-only run. The remaining difference in the .pptx is not visible on screen.
The plumbing works end to end: refusal, escalation, rescue, re-check and scoring. No conclusion about efficacy can be
drawn from one task.

## Guard v2, sprint S1 (offline, judge_bench corpus; v2/PROTOCOL.md, independently recomputed)
A stronger judge with history (Claude Opus + the 2 screens before the answer + the action list) detects significantly
more false successes: **+13.8 pts [+2.9, +30]**. Its false rejections are higher, but not significantly: **+4.3 pts
[−5, +15]**. The variant was selected on dev, and the held-out half was used once, as a single confirmation.
Held-out: v2 69 % (20/29) detection, 12.9 % (15/116) false rejection; v1 55 % (16/29), 8.6 % (10/116). The target
(>= 80 % / <= 10 %) was not met. Decision (ares): no online v2 arm; the v2 relay is stopped.
