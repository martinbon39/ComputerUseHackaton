# Independent healthy preservation review: A versus V10

**Verdict: UNCERTAIN — no semantic loss above 2 percentage points is demonstrated, but the available screenshots do not certify that bound.**

Most choices are preserved. The terminal/verification changes in the contacts and United contexts balance exactly within their respective frozen states. Only two Speedtest pairs remain unresolved. If both lose a useful next action, the loss is 2/64 = **3.125 pp**; if at most one does, the loss is at most **1.5625 pp**. The missing evidence is the effect of the specific Speedtest clicks, not the count of nonanswer outputs.

## Coverage and integrity

- Reviewed **all 64 pairs**, contexts **39–54**, seeds **17000–17003**, in `/tmp/moon-vision/HEALTHY_DIFF_V10.json`.
- Comparison SHA-256: `4a86876b67edf785c32687485a5a1e9b6bd9878db95fef322d1ecb1054142f36`.
- Independently matched all 64 unique candidate task/seed records to the healthy rows of `/tmp/moon-vision/runs/V10/generations.jsonl`, including payload hash, step, and all stored candidate output fields. Assertions passed.
- Directly inspected latest frozen screenshots for every context with changed executable coordinates or action transitions: **39, 40, 41, 44, 45, 46, 49, 50, 51, 53, 54**. Used metadata-designated latest files, including `046/image_01.png` and `050/image_00.png`. Relevant histories and the contacts save screenshots had also been examined in this checker session and remain the same frozen packets.
- No inference, GPU activity, heldout/reserve inspection, UI replay, or changes to other artifacts. Other-group output content was not reviewed while filtering the raw journal.
- **40 pairs have identical executable choices** after discarding descriptive wording and answer prose. **16 further coordinate variations hit the same visible controls.** Eight pairs remain: two Speedtest changes, four reciprocal contacts transitions, and two reciprocal United transitions.

Identical actions may share a defect; this is a preservation comparison, not a claim that all 56 preserved choices are correct. Likewise, **59/64 valid nonanswers is not 59/64 correct actions**.

## The two unresolved Speedtest pairs

Task: measure the connection and save the results to `~/Test/Speed/results.txt`, one metric per line. The current screenshot visibly shows ping **4 ms**, download **935.69 Mbps**, and upload **574.93 Mbps**. No results file has yet been created in the supplied history. Earlier history also mentions additional latency measurements, so asking for more detail is not inherently irrelevant.

| Context / seed | A → V10 | Evidence and judgment |
|---|---|---|
| **45 / 17003** | `Ctrl+Alt+T` → click `(350,925)` | A opens a terminal, directly preparing to create the directory/file. V10 clicks about pixel **672,999**, in the results-row region to the right of the ping value, hoping to open detailed results. There is no distinct visible control at that point; the share/action icons are much farther right. It might activate a row-level handler or do nothing. **Plausible loss of useful progress; not a proven miss.** A working details link could be a legitimate preparatory action. |
| **45 / 17000** | Click `(245,925)` → click `(210,925)` | A targets about **470,999**, inside the date text; V10 targets about **403,999**, at the left edge of the date-text area, between its calendar icon and first visible digit. Both intend the same date/time result entry. This is more plausibly equivalent than a move to another column, but the screenshot does not expose the clickable hitbox. **Unresolved target equivalence**, not an automatic regression and not an assumed successful click. |

The other two Speedtest seeds retain the exact terminal shortcut. No observed outcome establishes that either changed click opens details. A location in the same visual table row does not, on its own, prove equal interaction behavior.

## Balanced verification losses and gains

### Context 51: exported contacts

- Seeds **17000, 17001:** A answers; V10 clicks Files `(17,555)` to start verifying the Desktop files.
- Seeds **17002, 17003:** A clicks that same Files target; V10 answers.

The launcher click is grounded. Additional file verification is useful, but completion is also supported: the earlier save screenshot visibly lists Desktop `contacts.csv`, the next screenshot sets Desktop `contacts` with Excel `.xlsx` format, the recorded action clicks Save, and the latest screenshot shows **contacts.xlsx** with data and no open save dialog.

Thus these terminal choices are not automatically incorrect, nor are the extra checks automatically needed repairs. More importantly, **both arms have exactly two answers and two identical Files clicks on this same state**. Their executable-action multisets were checked programmatically and are equal. Under consistent next-action scoring, the two gained checks and two lost checks cancel; counting only the losses would bias the comparison.

### Context 54: United baggage calculator

- Seed **17001:** A waits 3 seconds; V10 answers.
- Seed **17003:** A answers; V10 waits the same 3 seconds.

The screenshot shows the calculator URL/title but still displays the prior baggage-information page and its “Calculate bag fees” button, with Chrome's stop-loading icon. Waiting is grounded and allows verification of the requested interface. Declaring readiness is less well supported at this instant.

This is one lost and one gained continuation check. **Each arm has three answers and one identical 3-second wait on the same state**, again verified programmatically. These changes cancel under consistent action-level scoring. They do not establish completed calculator loading in either arm.

## Complete context disposition

| Context | Assessment across all four seeds |
|---|---|
| 39 | Same CSV-export OK action; `(617,650)`→`(616,648)` remains inside the button. |
| 40 | All four coordinate changes stay within the orange bookmark Done button, x 831–833 / y 274–276. |
| 41 | Two identical Scale clicks and two small y changes that remain inside GIMP's Scale button. |
| 42 | Four identical Rename Sheet OK clicks. |
| 43 | Four identical extension-folder Select clicks. |
| 44 | Two identical PDF Save clicks; two coordinate changes still hit the green Save button. |
| 45 | Two identical terminal shortcuts; two unresolved changes described above. |
| 46 | Two identical Slide Pane clicks; y 320→323 and x 114→115 remain on the Slide Pane menu row. |
| 47 | Four identical 3-second waits. |
| 48 | Four identical `Ctrl+Enter` actions. |
| 49 | Two identical Delete data clicks; y 733→737 and 737→738 remain inside the same blue button. Any overly broad cleanup is shared by both arms. |
| 50 | Two identical system-menu clicks; the other two still hit the top-right speaker/system-indicator area. |
| 51 | Two answer→Files and two Files→answer transitions; action multiset preserved exactly. |
| 52 | Four identical Enter key actions. |
| 53 | Three identical Save clicks; x 806→805 still hits the green Save button. |
| 54 | Two preserved answers plus one wait→answer and one answer→wait; action multiset preserved exactly. |

## Conservative conclusion

The grounded differences establish **no net loss among the interpretable changes**. The remaining two possible losses are both in context 45. A conservative sensitivity range is therefore **0–2 additional lost useful actions (0–3.125 pp)**. This is an ambiguity range, not a measured accuracy estimate or confidence interval; either click could also turn out to be harmless or useful.

A strict **PASS** would require resolving at least one of those possible losses in V10's favor or establishing equivalent targeting. A **FAIL** would require establishing that both lose useful progress. Neither is justified solely by the available screenshots. **UNCERTAIN** is therefore the appropriate preservation verdict; no regression above the permitted 2 pp has been demonstrated.

This conclusion applies only to single-next-action preservation on this frozen cohort. No after-action screenshots, UI hitbox metadata, downstream task outcomes, or generalization evidence are available. No additional acceptance threshold has been introduced.

**RAN:** complete paired review, raw-output integrity checks, coordinate grounding, and action-multiset checks. **PASSED:** integrity/coverage and the documented target-equivalence checks. **CORRECT:** no absolute or end-to-end success-rate claim. **NOT RUN:** UI execution, inference, heldout evaluation, or other admission gates.
