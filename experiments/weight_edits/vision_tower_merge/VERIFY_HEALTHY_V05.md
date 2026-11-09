# Independent healthy preservation review: A versus V05

**Verdict: UNCERTAIN.** The frozen evidence does not demonstrate a semantic loss greater than 2 percentage points, but it also does not establish preservation within that limit. The structural change from 59 to 58 valid nonanswers is not a correctness measurement.

On 64 samples, one lost useful action is 1.5625 pp; two are 3.125 pp. The unresolved choices below can cross that boundary, so a confident PASS or FAIL would require assumptions about interaction behavior or how optional verification is scored.

## Coverage

- Examined all 64 A/V05 pairs for the 16 healthy contexts **39–54**, seeds **17000–17003**, in `/tmp/moon-vision/HEALTHY_DIFF_V05.json`.
- Input SHA-256: `c6716633f10fe6369fdb738068e84fad400a5f3ec9bcc95c3f61a365f305d843`.
- Read the healthy task statements and relevant histories. Inspected latest screenshots for every context containing changed coordinates or substantive action transitions: **40, 41, 44, 45, 46, 49, 50, 51, 53, 54**. For context 51, also inspected `image_00.png` and `image_01.png` to check the export/save evidence. Used `packet.json`'s `last_image`, including `046/image_01.png` and `050/image_00.png`.
- No inference, rollouts, servers, weight changes, heldout/reserve data, or other groups' paired actions/screenshots were used in this subtask.
- Ignoring descriptive wording and answer prose, **44/64 executable choices are identical**. Of the 20 remaining pairs, **15 are visually equivalent control hits**. The five non-equivalent or uncertain pairs are detailed below.

## Meaningful changes and uncertainties

### Context 45 — write Speedtest results to a file

The task requires saving network metrics to `~/Test/Speed/results.txt`. The latest screenshot displays the results table with ping 4 ms, download 935.69 Mbps, and upload 574.93 Mbps. No results file has yet been created in the supplied history.

**Seed 17003: A opens a terminal (`Ctrl+Alt+T`); V05 clicks `(450,920)`.** A takes a direct, useful step toward creating the directory and file. V05 clicks approximately pixel **864,994**, within the results-row region between the download and upload values, hoping to obtain details or a copy option. The screenshot shows no distinct control at that point; the visible share/action icons are much farther right. The click might activate a row-level handler, or might do nothing. Its effect is unavailable. This is a **plausible useful-action loss, not a proven failure**. A legitimate information-gathering action is also possible; history previously showed additional latency values, so further detail is not intrinsically pointless.

**Seed 17000: A clicks `(245,925)`; V05 clicks `(400,925)`.** A targets approximately pixel **470,999**, the date/time area; V05 targets **768,999**, the download-cell area. Both lie in the same visible result row, but the screenshot cannot establish whether the entire row, only particular cells, or neither point is clickable. **Do not automatically score these as equivalent merely because both descriptions say “result entry”; do not score V05 as a miss without interaction evidence.** This pair is unresolved.

Seeds 17001 and 17002 retain the identical terminal-opening shortcut.

### Context 51 — export contacts.csv and convert to contacts.xlsx

**Seed 17003: A opens Files `(17,555)`; V05 answers that the export/conversion is complete.** A's coordinates hit the Files launcher and begin a final existence check. V05 omits that additional verification.

There is unusually strong prior completion evidence: `051/image_00.png` visibly lists `contacts.csv` on Desktop; `image_01.png` shows the Desktop save destination, name `contacts`, and Excel 2007–365 `.xlsx` format; the last recorded action clicks Save; `image_02.png` shows the closed dialog and title **contacts.xlsx** with contact data present. Therefore V05's terminal decision is **defensible as completion**, not automatically an incorrect answer. The lost opportunity to verify both files together can be considered a process regression, but **a task-correctness loss is not established**. Count this separately from a mandatory save or an unfinished export.

The other three seeds preserve their executable choices: two answers and one Files click.

### Context 54 — open United's baggage fee calculator

**Seed 17001: A waits 3 seconds; V05 answers. Seed 17003: A answers; V05 waits 3 seconds.** The screenshot shows the calculator URL/title, while the body still displays the preceding checked-baggage information and “Calculate bag fees” button; Chrome's stop-loading icon is visible. Waiting is grounded and gives the new calculator interface time to render. An answer asserting that the calculator is ready goes beyond the visible interface.

These are a **loss and corresponding gain in continuation/verification**, on the exact same frozen screen, with the exact same 3-second wait. They cancel in an aggregate useful-next-action comparison under consistent scoring. One must not count only V05's adverse transition. The other two seeds remain answers. This does not prove that either arm has actually loaded the calculator.

## Complete context disposition

| Context | All four seeds: executable preservation assessment |
|---|---|
| 39 | Same CSV-export OK clicks. Descriptive wording only. |
| 40 | Bookmark Done clicks remain within the same visible orange button, including x 831–833 / y 274–276 variations. |
| 41 | Scale clicks remain inside the same GIMP Scale button, including x 585→590 and y 673–676 variations. Both arms inherit the same pending size/aspect settings. |
| 42 | Identical Rename Sheet OK clicks. |
| 43 | Identical extension-folder Select clicks. |
| 44 | PDF Save clicks remain within the same green Save button; 2-unit changes do not alter the target. |
| 45 | Two identical terminal shortcuts; the two uncertain row-click changes are detailed above. |
| 46 | Slide Pane clicks remain on that menu row. x 114→111 preserves the hit. |
| 47 | Identical 3-second waits after requesting the monthly weather view. |
| 48 | Identical `Ctrl+Enter` page-break actions. |
| 49 | Delete data clicks remain inside the same blue button at x 616 / y 733–738. Any concern about the breadth of the selected cleanup is shared, not a V05 difference. |
| 50 | Speaker/system-menu clicks remain in the same top-right system indicator area, x 964–965 / y 10–12. |
| 51 | Three equivalent choices; one omission of additional file verification, with completion already supported by prior save evidence. |
| 52 | Identical Enter key to confirm the font field. |
| 53 | Save clicks remain inside the same green button; x 805→806 preserves the hit. |
| 54 | Two equivalent answers; one wait→answer and one answer→wait on the same loading state. |

## Conservative interpretation

**Established net differential loss: zero from the clearly interpretable changes**, because the United continuation loss/gain cancels and the other grounded control changes preserve the hit. This is not a claim that either arm is correct on all other samples: identical actions can share a defect.

The two Speedtest pairs have unknown interaction effects, and the contacts pair loses optional verification while retaining strong completion evidence. A sensitivity analysis that counts zero through three of these as losses spans **0–4.6875 pp**; this is an ambiguity range, **not a measured accuracy estimate or statistical interval**. Even treating the date-cell/download-cell pair as equivalent leaves the remaining two judgments capable of straddling the 2 pp gate.

The defensible conclusion is **UNCERTAIN, with no demonstrated >2 pp semantic regression**. Do not promote the valid-nonanswer rate to ground truth. A strict preservation admission would need either observed effects for the Speedtest clicks and an explicit treatment of completed-task answers, or a correctness assessment that resolves those cases consistently across both arms.

**RAN:** all-pair semantic comparison and the screenshot/history grounding above. **PASSED:** coverage and target-equivalence checks only. **CORRECT:** no end-to-end accuracy claim. **NOT RUN:** UI replay, resulting screenshots, task completion evaluation, inference, or other cohort evaluation.
