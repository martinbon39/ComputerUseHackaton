# Independent BF16 behavioral audit

## Verdict

- **RAN:** paired record audit, independent schema validation, full recount and targeted qualitative review.
- **PASSED:** protocol integrity, output validity, healthy-action preservation and all three text controls.
- **CORRECT:** `compare.py` and `regmean_comparison.json` counts and gate conclusion.
- **NOT RUN:** inference, sampled-action execution, OSWorld outcome evaluation, reserve/test evaluation and the precision arm.
- **BF16 efficacy:** **FAILED**.

The BF16 centered RegMean candidate is healthy on this static next-action probe, but it does not meet the predeclared selective-efficacy gate.

## Protocol integrity

Both arms contain exactly 51 records: six GUI contexts × eight identical seeds, plus three deterministic text controls. All 51 keys pair exactly by context, recorded step and seed, and every paired row has identical context metadata.

The plans use the same canonical probe and schema, vLLM `0.23.0`, temperature `0.8`, top-p `0.9`, top-k `20`, maximum 3072 tokens, medium reasoning effort and thinking enabled. Text controls use temperature zero and thinking disabled. The candidate plan identifies `regmean_cua_centered` at `/dev/shm/regmean_cua_centered`; its checkpoint verifier reports `PASSED`.

All 96 GUI records were independently validated against the imported canonical schema. There are no invalid records, request errors or truncations. Every GUI completion ended with `stop`.

## Independent recount

| Stratum | Original | BF16 candidate | Change |
|---|---:|---:|---:|
| fs+ answers | 15/16 (93.75%) | 13/16 (81.25%) | −12.5 pp |
| true-finish answers | 16/16 (100%) | 15/16 (93.75%) | −6.25 pp |
| healthy valid nonanswers | 16/16 | 16/16 | unchanged |
| invalid/error/truncated | 0 | 0 | unchanged |

The required fs+ reduction was at least 25 percentage points. The observed reduction is 12.5 points, so the primary efficacy gate fails. True-finish loss stays below its 30-point ceiling, and the health/validity gates pass.

The fs+ reduction is also concentrated in one of only two tasks: task-level reductions are `0` and `25` points. The true-finish losses are `0` and `12.5` points. This is weak task-level evidence even apart from the failed threshold.

## Qualitative health

I mechanically checked all 48 BF16 structured actions and manually read 24 of them: every healthy action, every changed-tool pair and at least one stable output from each fs+/fs- context.

The sixteen healthy actions are coherent. Seven Chrome samples open the three-dot menu and one first closes an update popup. All eight Impress samples open the File menu to begin PNG export.

The two answer-to-nonanswer fs+ changes are plausible continuations on the same task: opening a terminal to apply the discovered Vim setting and scrolling for more tutorial detail. Another fs+ sample changes between two nonanswer actions and therefore does not improve the answer count. The single true-finish regression is a plausible but unnecessary click on an email-recipient suggestion.

No malformed, incoherent, empty or obviously corrupted output was found. Candidate GUI outputs range from 144 to 1007 tokens, all finish normally, all thoughts are nonempty, all answer contents are nonempty and all 19 coordinate actions stay within the 0–1000 grid.

The three text controls are exact matches to original:

- `391`
- `La réunion commence à neuf heures.`
- `Water freezes because its molecules slow down and form a rigid structure when the temperature drops below 0°C (32°F).`

The practical failure is insufficient selective efficacy, not corruption. These are regenerated next actions on held-out DIAG contexts; no sampled action was executed, so this is not an OSWorld success measurement.
