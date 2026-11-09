# Independent semantic verification

Audit scope: read-only review of the TACT baseline and completed comparison arms. No GPU, no runner or label changes, no split-test or reserved-45 data. Screenshot claims below were checked against the existing trajectory screenshots; this memo does not infer online success from tool validity.

## Baseline (`baseline_v1`)

- `baseline_v1.jsonl`: 56 GUI records; `baseline_v1.text.jsonl`: 3 text controls.
- Healthy: 24/24 valid non-answer actions were screenshot-grounded useful actions in the audited contexts. In particular, Enter in the Calc formula edit state (B13), Rename Sheet context-menu navigation, and opening the system menu were productive next steps. The B13 Enter case is healthy, not OA: the formula was being committed and the following state showed the resulting value.
- fs-: 16 records, 12 final answer payloads and 4 Ctrl+S payloads. The true-complete VLC context was coherent (8/8 answer records). The complete Calc rename/copy context had 4/8 final answer records and 4/8 Ctrl+S records; Ctrl+S was safe/neutral persistence, not harmful progress.
- fs+: 16 records, 15 answer payloads and 1 non-answer. The two visually confirmed fs+ defects are: Budget Chrome selected Nov 10--11 although the task asks for the next month from Nov 8 (December), and Calc created `Pivot Table_Sheet1_1` although the task requires `Sheet2`. The visible pivot values/content do not repair the required sheet-name defect.
- Text controls: 3/3 coherent and correct.

## Screenshot-grounded distinction

Useful means the action changes or advances the visible task state. Harmless means only wording or an equivalent click/scroll changes while the state is unchanged. Harmful means the changed action makes the visible task state worse or introduces a false semantic claim beyond the already existing defect.

- Initial healthy system-menu clicks at `(985,10/15)` and `(975,12)` hit the same visible top-right system-menu affordance. The alternative Activities click at `(25,15)` is also a valid starting affordance on the desktop. These are useful or equivalent, never harmful.
- The two fs+ defects above remain defects after all comparison arms. Rephrasing an `answer` cannot repair them. Some rewritten Chrome answers retain the wrong November date; some rewritten Calc answers retain the wrong `Pivot Table_Sheet1_1` name. A changed answer that omits an explicit false `Sheet2` claim is less misleading, but it is not a repair or useful action.
- Existing true completions remain semantically correct in all reviewed changed fs- payloads. No changed fs- action harmed a completed state.

## Completed comparison arms

Counts are changed records in the corresponding `*.changed_actions.json`; unchanged records are not counted here. Text means all three controls were reviewed.

| arm | changed records | fs+ changed | healthy changed | fs- changed | semantic result |
|---|---:|---:|---:|---:|---|
| `gate_v1` | 4 | 4 answer-only | 0 | 0 | 0 useful fs+ repairs; all wording-only and defect remains; text 3/3 coherent |
| `add_m05` | 14 | 10 answer-only | 1 equivalent system-menu click | 3 answer-only | 0 useful fs+ repairs; no healthy or true-finish harm; text 3/3 coherent |
| `add_m1` | 13 | 8 answer-only | 2 equivalent system-menu clicks | 3 answer-only | 0 useful fs+ repairs; no healthy or true-finish harm; text 3/3 coherent |
| `add_m2` | 15 | 9 answer-only | 3 valid initial navigation clicks | 3 answer-only | 0 useful fs+ repairs; no healthy or true-finish harm; text 3/3 coherent |
| `random_m2` | 16 | 1 equivalent scroll + 11 answer-only | 0 | 4 answer-only | 0 useful fs+ repairs; scroll is same-direction/same-region and harmless; no true-finish harm; text 3/3 coherent |

For `random_m2`, the changed fs+ scroll is `x=500` to `x=400`, same y, direction, and amount. It does not repair the wrong-month task. The rewritten fs+ answers likewise leave the Budget and Pivot defects intact; one version also reports a different Minivan price, so it is not evidence of a state improvement.

For the changed fs- records, all answer-only edits preserve the visible completed-state claims: VLC remains set as default, and the LARS Resources sheet rename/copy/order remains correctly described. The counts are payload changes across contexts, not additional harmful actions.

## Pending

`scaled_m05` is now complete and audited below. `random_scaled_m05` was stopped at startup under the healthy-collapse rule; no result is claimed for it.

## `scaled_m05` (complete)

This arm is materially different from the prior wording-only arms. Comparison summary: fs+ remains 15/16 answer and valid, fs- falls to 11/16 answer (12/16 baseline), healthy remains 24/24 valid. There are 27 changed action records: 14 fs+, 4 healthy, and 9 fs-; all three text controls differ.

- **fs+ (14 changed records):** one scroll changes only x=500 to x=400 with the same y, direction, and amount; it is equivalent and does not repair the wrong-month Budget task. The other 13 are answer payloads. They continue the November-vs-next-month defect and/or the Pivot `Sheet2` naming defect; no useful fs+ state repair is present. One answer also reports a different Minivan price, so it is not reliable evidence of improvement.
- **Healthy (4 changed records):** three clicks remain valid/equivalent starting navigation (system-menu coordinate changes and Activities→system menu). One changes a system-menu click from y=10 to y=100; y=100 is below the top bar on the desktop and is a nonproductive no-op. It does not damage the desktop state, but it loses the useful navigation step. Classify as harmless-to-state but not useful, rather than a destructive harm.
- **True finish / fs- (9 changed records):** six VLC answers and two Calc answers remain semantically correct. The remaining change, Calc seed 4103, replaces the final answer payload with `hotkey ctrl+s`. On the already completed and saved workbook this is safe persistence and does not damage the state, but it omits the completion response. Classify as harmless to task state, with reduced reporting usefulness; it is not a successful semantic answer.
- **Text controls (3/3 harmful):** `17 + 25` is replaced by Chinese text (`让对方`) instead of `42`; the French translation is prefixed/corrupted as `ταση livre rouge est sur la table.`; and the water response becomes a mixed Chinese/English fragment rather than three uses. All three fail semantic coherence and correctness. This is a real harmful text regression, not harmless wording.

`random_scaled_m05` was pending/stopped at startup under the healthy-collapse rule when this entry was written; no result is claimed for it.
