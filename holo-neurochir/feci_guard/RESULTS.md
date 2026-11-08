# Feci Guard — results (final, 2026-11-08)

## In four lines
1. **A stronger judge is a real verifier; the agent judging itself is not.** On the same 268 episodes, Claude Sonnet
   (Feci Guard v1, final screen only) detects 68 % of false successes for 10 % false rejections (gap +58 pts
   [+41, +74]). Holo-3.1-4B judging itself: 53 % / 48 % (+5 [−13, +23]).
2. **Adding history to an even stronger judge helps.** Claude Opus with the 2 screens before the answer and the
   action list detects significantly more than v1 (+13.8 pts [+2.9, +30]), and its extra false rejections are not
   significant (+4.3 [−5, +15]). This was selected on dev and confirmed once on the held-out half. It does not reach
   the 80 % / 10 % target.
3. **Refusal with precise feedback sometimes repairs; on its own it does not prove a gain.** Replaying 9 feasible false
   successes: 5/18 branches repaired with the guard, 2/18 without, paired +17 pts [0, +44]. This cannot be told apart
   from zero, and only 3 repairs are specific to the guard. The clearest case: calc/1de60575, 2/2 against 0/2.
4. **The limit of a screen-only verifier.** Some false successes differ only inside the saved file (impress/550ce7e7:
   the guard fixed what was visible and the evaluator still scored 0). Of the original's 29 false successes on the
   test split, 15 are visible on the last screen and 4 only in the file or internal state (osw-analysis,
   `../report/S2_DIAG.md`).

Not run (cancelled by ares): the 60-item blind packet (replaced by judge_bench), the 45-task online run (too small: the
minimum detectable effect is about 17 pts), the 30-step repair sensitivity, and an online v2 arm.

## 1. Judge bench: three judges on the same 268 episodes (final screen only)
Source: `../judge_bench/` (verif-study corpus: 66 false successes, 202 true successes, 90 tasks). Wilson 95 % CI;
CI of the gap from a task-level bootstrap.

| | Holo-3.1-4B | Holo4-27B | Claude Sonnet (Feci Guard v1) |
|---|---|---|---|
| False successes detected | 53 % (35/66) [41–65] | 47 % (31/66) [35–59] | **68 % (45/66) [56–78]** |
| True successes wrongly rejected | 48 % (97/202) [41–55] | 31 % (63/202) [25–38] | **10 % (21/202) [7–15]** |
| Gap | +5 pts [−13, +23] | +16 pts [−3, +33] | **+58 pts [+41, +74]** |

Caveat: the Holo judges used verif-study's V1 prompt, while Claude used the Feci Guard prompt, so the Claude advantage
mixes the model and the prompt.

## 2. Guard v2, sprint S1 (offline; protocol `v2/PROTOCOL.md`, independently recomputed)
Split by task hash, committed before any test (`v2/SPLIT.json`): dev has 37 false and 86 true successes; held-out has
29 and 116. The variants were run on dev; one was selected by the rule written beforehand (highest detection with dev
false rejection <= 10 %), then run once on the held-out half.

| Dev | detection | false rejection |
|---|---|---|
| v1 (Sonnet, final screen) | 29/37 | 11/86 |
| a: + history (2 previous screens + actions) | 28/37 | 7/86 |
| b: Opus | 29/37 | 8/86 |
| c: strict "file evidence" prompt | 35/37 | 33/86 |
| **ab: Opus + history (selected)** | **31/37** | **8/86** |

Held-out, one run: v2 (ab) detects 69 % (20/29) [51–83], false rejection 12.9 % (15/116) [8–20]; v1 detects 55 %
(16/29), false rejection 8.6 % (10/116). Paired by task: detection **+13.8 pts [+2.9, +30]**, false rejection
**+4.3 [−5, +15]**. Caveat: ab was built after the dev results of a, b and c were seen, so the held-out run is a
single confirmation, not a pre-registered test. Median latency is 11 s, against 6 s for v1. Decision (ares): no
online v2 arm.

## 3. Repair measure (registered in PREREG.md; independently recomputed from the raw jsonl)
12 feasible false successes of the original agent (diag, diag2 and val runs, never test) were replayed up to the
recorded answer. Each got K=2 continuations per arm with at most 15 new steps, on the same server at the same time,
scored by the official evaluator. 9 episodes have a valid replay in all 4 branches (3 excluded: multi_apps/f5c13cdd,
vlc/386dbd0e, vlc/aa4b5023).

| 9 episodes × 2 branches | no guard | guard (Claude Sonnet, passive) |
|---|---|---|
| Repaired (official score 1) | 2/18 | **5/18** |
| Answered "done", still wrong | 15 | 6 |
| No answer within 15 steps | 1 | 8 |
| Mean new steps | 1.4 | 8.6 |

- Paired difference per episode (guard − no guard): **+16.7 pts [0, +44]**. 2 episodes are better and 0 worse
  (sign test p = 0.5). With all 12 episodes: +12.5 [0, +33]. **The effect cannot be told apart from zero.**
- The guard refused 12 branches (16 refusals). 3 of them ended repaired, 25 % [9–53], from 2 episodes:
  - **calc/1de60575, 2/2 against 0/2.** The tab was named "Pivot Table_Sheet1_1", not "Sheet2". The agent renamed it
    in 5 steps and the second check passed. Demo: `~/osw/feci_demo/calc_1de60575/`.
  - writer/0b17a146, 1/2: scored 1 at the step limit without answering again.
- impress/8979838c succeeds in all 4 branches as soon as the agent answers (its recorded false success does not
  reproduce under replay). So only 3 repairs are specific to the guard.
- Costs:
  - 7 refused branches reached the 15-step limit without answering (a refusal counts as a step).
  - 2 branches were let through at the refusal cap while still wrong.
  - On 2 episodes the guard accepted wrong answers in all 4 branches.
- What is measured is refusal **plus coaching**: the feedback carries Claude's suggested next action.
- Protocol notes (PREREG.md, corrections section): the section was written before launch but committed after about
  6 branches had finished, and the exclusion rule depends only on the replay prefix.

Raw data: `~/osw/feci_repair/{nog,guard}/branches.jsonl`. Analysis: `analyze_repair.py` -> `repair/results.json`.

## 4. End-to-end runs on orbit VMs (one task each; they show the harness works, not that it helps)
- **Guard** (`smoke/impress_550ce7e7_guard.md`):
  - Step 29: the guard refused, with correct evidence: "the strike-through stops at 'Requ'".
  - The agent fixed it, and the second check passed.
  - Official score 0: the remaining difference is inside the .pptx and not visible on screen.
- **Guard + rescue** (`smoke/impress_550ce7e7_rescue_guard.md`):
  - Step 11: the guard refused.
  - Holo4-27B (Modal) took over with the history and the feedback, using 5 calls. The second check passed.
  - Official score 0, for the same reason.

## 5. Verifier hand tests
On vlc/386dbd0e (false success, a global hotkey setting), the passive mode answers COMPLETE because the setting is not
visible (cannot_tell). The active mode answers NEED_CHECK and asks to open Tools > Preferences > Hotkeys. Latency is
6.5–10.6 s, about $0.04 per check.
