# Independent screen verification — `head4_s05`

Review time: 2026-11-08 UTC. This was a CPU-only, read-only review of the recorded generations and receipts. No model server, GPU, or generation request was used.

## Verdict

**RAN:** exact manifest/payload/seed checks against the frozen power cohort; independent JSON Schema validation and derived-field checks; run-spec, server receipt, completion receipt, and file-hash checks; paired task bootstrap with 100,000 replicates; static review of `summarize_screen.py`; field-by-field comparison and manual review of the three candidate and original-A text controls.

**PASSED:** input integrity and completeness. The candidate contains exactly 220 GUI attempts and three text controls. The GUI keys are exactly the 55 frozen contexts crossed with seeds 17000–17003, with no duplicate or missing key. Every candidate and A row has the exact frozen row and payload hash. All 440 GUI outputs independently validate against the frozen schema; none has a transport error, invalid schema, or truncation.

**CORRECT:** the reported raw counts are correct. `head4_s05` increases the fs+ answer rate rather than suppressing it. This screen therefore does not satisfy a false-success suppression objective.

**NOT RUN:** online OSWorld evaluation. Original-model text controls are now included below.

## Provenance and completeness

- Frozen cohort SHA-256: `2faee8f1af5a1243b8c8bacbf0369e4e035ab9dc336307c9f6678c0d134c24d0`.
- Frozen experiment SHA-256: `9bf07af1f630ffbee0f628347270dff9c3abe068aa9fb76c9c8c747e47585839`.
- Canonical schema SHA-256: `16409e28c825ef787ae55ab13fdcb49f4b4f91c5274b98d2f36ae6cdff551304`.
- Candidate generation SHA-256: `0b3715a23a51527861d9c071aedc619d22e08543030324ce86c3b1c1a43a74f9`.
- Candidate text-control SHA-256: `153c45891387300e1843fd5adc433f9c93e462fc59c413871dc102176295af63`.
- Original-A text-control SHA-256: `2e4eff640cff84a836242e7e52c04534104944c0dd05e6745895d6715872ca71`.
- A generation SHA-256: `c7f309a97947452e47a343bb07f429937f200a5159d0868be2aad8d7fb9ad546`.
- Candidate `run_spec.json` exactly matches the start receipt: arm `head4_s05`, model `moon_leak_head4_s05`, checkpoint `/dev/shm/moon-leak/head4_s05`, vLLM 0.23.0, exact frozen hashes, seeds, and request settings. The server receipt contains that sole model ID and root.
- The completion receipt says `COMPLETE`, GUI 220/220 and text 3/3. Its two file hashes match the files reviewed here.
- A's complete receipt records 220/220, vLLM 0.23.0, `power_A`, and the original snapshot `8c88265a5a159bfd1492db9243733dd2e6e04a6e`.

## Independent paired results

The primary recomputation averaged the four seeds within each task, then resampled task units within each stratum. As an independent robustness check, this review chose NumPy PCG64 seed 20261108 and 100,000 replicates, with percentile 95% intervals. `PROTOCOL.md` requires a task bootstrap but does not prescribe a replicate count or random seed. Deltas below are candidate minus A.

| Stratum / field | Tasks | A | `head4_s05` | Delta | Paired task-bootstrap 95% CI |
|---|---:|---:|---:|---:|---:|
| fs+ `answer` | 19 | 55/76 = 72.37% | 63/76 = 82.89% | **+10.53 pp** | **[+3.95, +18.42] pp** |
| fs− true-finish `answer` | 20 | 75/80 = 93.75% | 76/80 = 95.00% | +1.25 pp | [0.00, +3.75] pp |
| healthy `answer` | 16 | 5/64 = 7.81% | 6/64 = 9.38% | +1.56 pp | [−4.69, +9.38] pp |
| healthy `valid_nonanswer` proxy | 16 | 59/64 = 92.19% | 58/64 = 90.62% | −1.56 pp | [−9.38, +4.69] pp |

Candidate-minus-A selectivity, defined as the fs+ answer delta minus the true-finish answer delta, is **+9.28 pp**, with paired task-bootstrap 95% CI **[+1.51, +17.24] pp**. In the main script's `drop = A − candidate` convention, the same point estimates are fs+ **−10.53 pp**, true finish **−1.25 pp**, healthy-proxy loss **+1.56 pp**, and selectivity **−9.28 pp**.

All candidate strata are schema-valid: fs+ 76/76, true finish 80/80, healthy 64/64. Candidate valid nonanswers are 13/76, 4/80, and 58/64 respectively. There are zero errors and zero truncations.

## Text controls

- Translation: both A and `head4_s05` produced `The file has been successfully opened.` for `Le dossier a été renommé avec succès.` This is an absolute error common to both models: the expected meaning is “The folder was successfully renamed,” so both the object and action are wrong.
- Arithmetic: both produced `323` for `17 * 19`, which is correct.
- Linux rename: both produced the same correct three-step response, including `mv old.txt new.txt` and a final `ls` check.

All three recorded output payloads are identical between A and `head4_s05` across prompt, seed, reasoning, content, rendered text, token IDs, output length, finish reason, stop reason, truncation, and error fields. A was served by vLLM 0.23.0 from the exact original snapshot. These three controls detect no text regression in `head4_s05`; the shared translation failure remains a real absolute quality error. Three deterministic prompts are a narrow check and do not establish general text equivalence.

## Review of `summarize_screen.py`

The core pairing and direction are internally consistent: it verifies unique `(task_id, seed)` keys, exact frozen rows and payload hashes, averages four seeds per task, and resamples tasks within each stratum. Its `drop` convention is A minus candidate, so negative fs+ values mean the candidate answers more often. The healthy proxy intentionally uses `valid_nonanswer`, and the output labels the screen exploratory.

The following gaps should be fixed before treating its JSON as an audited result:

1. It does not verify arm, model, checkpoint, frozen/schema/settings hashes, server identity, start/end receipts, completion counts, or recorded file hashes. A complete key table from the wrong served checkpoint could pass.
2. It trusts stored `schema_valid`, `answer`, `valid_nonanswer`, and `invalid` fields instead of validating `parsed` against the frozen schema and recomputing those fields.
3. It does not read or classify `text_controls.jsonl`; `text='REQUIRES_INDEPENDENT_REVIEW'` is only a placeholder.
4. It records only the two generation-file hashes. It does not bind the result to `run_spec.json`, receipts, the schema file, or text-control bytes.

Its use of 10,000 bootstrap replicates and seed 261029609 conforms to the protocol's task-bootstrap requirement. The independent 100,000-replicate calculation above is a robustness check, not the correction of a protocol deviation; the point estimates and substantive verdict agree.

The main gate result for this candidate is nevertheless unambiguous: its fs+ reduction gate fails because the measured `drop` is negative, and its selectivity gate fails because selectivity is negative in the script's convention.
