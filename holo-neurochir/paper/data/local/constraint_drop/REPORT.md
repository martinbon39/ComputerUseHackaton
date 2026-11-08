# constraint_drop: does Holo-3.1-4B name an unmet requirement just before it answers?
2026-11-08, CPU only. Protocol pre-registered and committed before any annotation (`PROTOCOL.md`, commits b88886d and 42a99b0).
Scripts: `annotate.py` (blind annotation), `analyze.py` (pre-registered stats), `post_hoc.py` (NOT pre-registered).
Numbers: `RESULT.json`. Raw labels: `annotations.jsonl`.

## In short
- **H1 is not supported.** The agent names an unmet requirement in its last 3 steps in **9/56 false successes (16.1 %
  [8.7, 27.8])** and in **10/133 true successes (7.5 % [4.1, 13.3])**. The difference is +8.6 pts [−0.8, +20.8]
  (Newcombe), one-sided Fisher p = 0.068. The bootstrap by task gives [−3.4, +22.0]. Neither arm alone is significant
  (modal p = 0.25, pod p = 0.12).
- **"Dropping a known constraint" is rare.** Of the 19 "yes", 14 are statements that the task cannot be done. Only 5
  name a step still to do: 3 in FS and 2 in TS (the 2 TS are "the document needs to be saved", followed by the save).
  The pattern the reviewer described ("the dates must still be corrected", then answer) shows up clearly in **2 or 3 of
  the 56 false successes**: `multi_apps/e8172110` ("the script couldn't fully automate"), `libreoffice_calc/7a4e4bc8`
  ("no separate First Name column exists"), and maybe `multi_apps/c7c1e4c3` ("need to save").
- **5 of the 9 FS "yes" are a harness scoring artefact, not a false "done".** On 5 infeasible tasks the agent answers that
  the task cannot be done ("GIMP cannot convert PNG to SVG", "Bluetooth cannot be switched on", "unable to find an
  option…"). The regex in `run_holo.py:67` (`infeasible|cannot be (completed|done)|not possible`) misses that wording.
  The harness then sends DONE instead of FAIL, so the episode scores 0. These are all 5 FS on infeasible tasks in the two
  arms: `gimp/62f7fd55` (pod), `os/b3d4a89c` (both arms), `chrome/ae78f875` (both arms). The same text phrased
  differently scores 1 on modal (`gimp/62f7fd55`).
- **On feasible tasks only (post hoc):** 4/51 FS (7.8 %) against 2/124 TS (1.6 %), +6.2 pts [−0.03, +17.0], p = 0.061.
  Not significant either.
- **A free self-check guard is much weaker than the external Guard.** If we block the "done" whenever label = yes, it
  catches 9/56 = 16 % [9, 28] of FS, wrongly rejects 10/133 = 7.5 % [4, 13] of TS, and has a precision of 9/19 = 47 %.
  The external Guard catches 68 % and wrongly rejects 10 %. That Guard figure comes from 268 other final screens, so the
  comparison is indicative, not paired. In the pre-registered sensitivity subset (answers the harness does not read as
  "infeasible"), it rejects only 2/124 TS (1.6 %) at the same 16 % recall. But 5 of its 9 catches are the regex misses
  above: fixing the regex would remove them, and blocking them does not repair anything.

## Data
Two arms of the original Holo-3.1-4B on the 120-task test split: modal (`~/osw/results_test_gh_orig_modal_test`) and pod
(`~/osw/results_test_gh_orig`). Included: last step is `answer`, score 0 (FS) or 1 (TS). There are 56 FS (27 modal, 29
pod) and 133 TS (65, 68). 9 partial scores are excluded, and nothing else is. The annotator saw the instruction plus
`note` and `thought` of the last 3 steps. It did not see the score, the arm, the task id, the answer text or `reasoning`.
The prompt is English (the PROTOCOL gives it in French). The constant is `annotate.py:PROMPT`.

## Results (pre-registered)
| subset | FS yes / n | TS yes / n | FS − TS [95 % CI] | Fisher p (FS > TS) |
|---|---|---|---|---|
| **all (primary)** | 9/56 = 16.1 % [8.7, 27.8] | 10/133 = 7.5 % [4.1, 13.3] | +8.6 [−0.8, +20.8] | 0.068 |
| modal | 5/27 = 18.5 % | 7/65 = 10.8 % | +7.7 [−6.5, +26.7] | 0.25 |
| pod | 4/29 = 13.8 % | 3/68 = 4.4 % | +9.4 [−2.0, +26.4] | 0.12 |
| answer not read as infeasible by the harness | 9/56 = 16.1 % | 2/124 = 1.6 % | +14.5 [+6.0, +26.3] | 0.0005 |

The last row is significant, but it is **not** evidence for H1. The subset removes exactly the 9 TS where the agent
correctly answers "infeasible". Those hold 8 of the 10 TS "yes", and the filter depends on the answer text, which
determines the score on infeasible tasks. Most of the FS "yes" that remain are the 5 regex misses.
Pre-registered decision: H1 needs p < 0.05 and a CI lower bound > 0 on the primary row. That fails.

## Checks
- **Quotes:** 17/19 "yes" quotes are verbatim substrings of the text the annotator saw. The 2 others contain an elision ("…").
- **Re-annotation of 20 random rows by an independent Sonnet subagent, blind:** with the exact protocol question, it
  agrees on **20/20**. In a first run, my brief added an example that is not in the protocol ("needs to be saved" counts
  as yes). Agreement then fell to **10/20**. All 10 disagreements were still-to-do steps (save, press Enter, nudge), and
  the agent usually performs them within the same 3 steps before answering. So the label depends on whether such
  in-progress steps count. Under that broad reading the sample gives yes on 5/5 FS and 8/15 TS. That is too small
  to test, and a guard would reject about half of the true successes. Deciding whether this broader construct
  discriminates would take a new pre-registered run on all 189 episodes, which was not done. Details:
  `audit_results.json`, `audit_key.json`.
- **Statistics recomputed by a second independent subagent from the raw jsonl, with its own code:** every count, rate,
  Wilson and Newcombe CI and Fisher p matches to 4 decimals.

## Limits
- One annotator model (Sonnet) and one prompt.
- A 3-step window: a requirement stated earlier and then forgotten is not seen.
- The same task appears in both arms, so the episodes are not independent. The bootstrap by task gives the same verdict.
- The text signal is the agent's own `note` and `thought`. An agent that drops a constraint silently is invisible here by
  construction. That is the case for most FS: 47/56 have no "yes".

## Sentence for the paper
"When Holo-3.1-4B ends with `answer`, it seldom writes in its last three steps that a requirement is still unmet: 9/56
false successes (16 %) against 10/133 true successes (8 %), one-sided Fisher p = 0.07, difference +8.6 pts [−0.8, +20.8].
Most of these mentions say that the task cannot be done, and 5 of the 9 in false successes are correct infeasibility
answers that our harness scored as 'done'. Knowingly dropping a stated constraint therefore explains few false successes
(2–3 of 56). A free rule that blocks the 'done' on this signal would catch 16 % of false successes, against 68 % for the
external verifier."
