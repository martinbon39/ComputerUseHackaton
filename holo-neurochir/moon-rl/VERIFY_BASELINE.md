# Independent baseline A verification

Reviewer: independent read-only checker. No model/API/GPU call was made.

## Verdict

- **RAN:** direct parse of the frozen manifest, all 220 GUI records, the JSON schema, both pilot/full receipts, the three text controls, `analyze.py`, and `analysis_A.json`; independent recomputation of keys, schema validation, classifications, tool counts, and strata aggregates.
- **PASSED:** baseline A is complete and internally consistent. The four-request pilot is retained, followed by 216 new requests. All expected 55 tasks x 4 seeds are present exactly once.
- **CORRECT:** the recorded A aggregates and analysis definitions match the raw data. Candidate deltas use paired task-level differences and a 100,000-replicate PCG64 task bootstrap. The registered numeric cutoffs are implemented with the intended inclusive comparisons.
- **NOT RUN:** candidate comparisons, checkpoint construction/integrity, online OS interaction, and semantic correctness of GUI actions.

## Baseline evidence

Raw file: `/tmp/moon-rl/runs/A/generations.jsonl`; SHA-256 `20099f21c10eefc725ca6a1304b5408c47105fa77b83d9c2936c3612c7f0ab71`.

The file contains 220 unique `(task_id, seed)` keys and exactly equals the Cartesian product of 55 frozen task IDs and seeds 17000-17003. Every record matches its complete frozen row and payload digest, has `arm=A`, and has `model=power_A`. Receipts identify vLLM 0.23.0, the sole model `power_A`, and root `/workspace/hf/hub/models--Hcompany--Holo-3.1-4B/snapshots/8c88265a5a159bfd1492db9243733dd2e6e04a6e`. The frozen SHA in both stages is `9bf07af1f630ffbee0f628347270dff9c3abe068aa9fb76c9c8c747e47585839`.

Independent schema validation passes for all 220 records. Stored `schema_valid`, `invalid`, `answer`, and `valid_nonanswer` flags agree with recomputation. There are zero transport errors and zero truncations.

| Stratum | n | answer | valid non-answer | exact recorded tool |
|---|---:|---:|---:|---:|
| fs+ | 76 | 56 (73.6842%) | 20 (26.3158%) | 56 |
| true finish (`fs-`) | 80 | 75 (93.7500%) | 5 (6.2500%) | 75 |
| healthy | 64 | 4 (6.2500%) | 60 (93.7500%) | 59 (92.1875%) |

The three T0 text controls are present, untruncated, error-free, and coherent/correct: `391`; `La réunion commence à neuf heures.`; and a one-sentence explanation that water freezes below 0 C as molecules form a rigid structure.

## Analysis audit

`analyze.py` validates completeness, frozen rows, payload digests, arm/model identity, and paired seeds before analysis. For each stratum and metric it averages the four draws within each task, computes candidate-minus-A per task, then resamples those paired task differences. This is the registered task-clustered paired bootstrap. It uses 100,000 PCG64 draws with seed 20261108 and percentile 95% intervals.

The gates are implemented as registered: schema-valid rate `>= 0.95`; healthy `valid_nonanswer` delta `>= -0.02`; fs+ answer delta `<= -0.15`. Baseline self-comparison in `analysis_A.json` correctly gives zero deltas and degenerate zero intervals; the fs+ signal gate is correctly false for A versus itself. With 64 healthy generations, the -2 point cutoff permits at most one additional non-answer failure relative to A (59/64 = 92.1875%, delta -1.5625 points); two additional failures yield -3.125 points and fail.

The healthy gate is a structural preservation check only. `valid_nonanswer` establishes a schema-valid non-answer action, not that its tool arguments are sensible, that it matches the demonstrated action, or that it advances the live task. Exact tool type and argument differences remain diagnostics, and successful OS interaction was not tested here.
