# Quantitative verification — literal phase

**Verdict: RAN / PASSED / CORRECT**

Audit indépendant en lecture seule, exécuté sur le pod avec taskset -c 40,41 et OMP_NUM_THREADS=2 MKL_NUM_THREADS=2 OPENBLAS_NUM_THREADS=2. Aucun GPU, aucune génération relancée, aucune donnée reserve/test ni screenshot examinée.

## Frozen identities

- Manifest v3 SHA256: cdef6ea3b55406a1bd7574b3840a632ffa72c5ee39f4efbe5756b9a1b577d2f7
- Axes SHA256: eff834646fa65134a545094c67745dbcb560b63b82f170a047d86f7dde9c1a44
- Reference SHA256: 1a6fe189702201c5768f60a23676c2c6fd5ca404793446fd01b855fe26f52c79
- Current steer.py SHA256: c2c2d2817c7fd27dddfe47e0fc4f4f93f774b800d53fa03554752a166999310e
- Archived baseline no-op steer.nn_hooks.py SHA256: 7d65651fa4f734c2d69624e4d83e46338c2af5672ec073a8f869823bfb39c076

Every completed job records the same manifest, axes, reference, scope=boundary, scaled=false, and n_outputs=59 (56 GUI + 3 text). The baseline deliberately records the archived no-op runner; gate/add/random use the current bound-forward runner.

## Completed arms

| arm | mode / strength | rows | unique keys x seeds | fs+ answer | fs- answer | trunc/error | final boundary / target / changed | realized delta norm |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| baseline_v1 | baseline / -0.5 | 56 | 7 x 8 | 15/16 | 12/16 | 0 | 0 / 0 / 0 | 0 |
| gate_v1 | gate / -0.5 | 56 | 7 x 8 | 15/16 | 12/16 | 0 | 56 / 560 / 42 | 10.671612 |
| add_m05 | add / -0.5 | 56 | 7 x 8 | 15/16 | 12/16 | 0 | 56 / 560 / 560 | 396.249493 |
| add_m1 | add / -1.0 | 56 | 7 x 8 | 15/16 | 12/16 | 0 | 56 / 560 / 560 | 792.070703 |
| add_m2 | add / -2.0 | 56 | 7 x 8 | 15/16 | 12/16 | 0 | 56 / 560 / 560 | 1583.961545 |
| random_m2 | random / -2.0 | 56 | 7 x 8 | 15/16 | 12/16 | 0 | 56 / 560 / 560 | 1583.941818 |
| scaled_m05 | add / -0.5, scaled | 56 | 7 x 8 | 15/16 | 11/16 | 0 | 56 / 560 / 560 | 9838.777501 |

For every completed arm, all 56 GUI records have the expected frozen row metadata, exact actual_n_in == expected_n_in, a valid answer/non-answer boolean, no error, and no truncation. All 56 token streams contain END token 248069 and terminate in <|im_end|> token 248046. The three text prompts and text schemas are identical across arms and all text records are complete.

The GUI decision map (row_key, seed) -> (answer, valid_nonanswer, truncated, error) is identical across baseline_v1, gate_v1, add_m05, add_m1, add_m2, and random_m2; this was checked per pair, not only from aggregate counts. Intervention outputs can still change action/tool text: the comparison files report changed action cases and explicitly limit interpretation to screening metrics.

random_m2 matches add_m2 on all pair decisions, frozen metadata, seeds, schemas, prompts, and generation settings. Its requested delta norm is exactly the same (1583.919163); realized BF16 norm is 1583.941818 versus 1583.961545 for add_m2 (difference 0.019727, approximately 0.00125%). Both have 560 targeted and 560 actually changed rows.

## Output and provenance hashes

| arm | JSONL SHA256 | runner SHA256 | exit | done |
|---|---|---|---:|---|
| baseline_v1 | 7b43249f35a1dd47566cc65846bbbacaa094d3e4752d13e8b9fcd2585469580b | 7d65651fa4f734c2d69624e4d83e46338c2af5672ec073a8f869823bfb39c076 | 0 | complete |
| gate_v1 | e3ec4bca8e2ac811f5423e787da3471e61a9de6a7c62f350150d633131d907e5 | c2c2d2817c7fd27dddfe47e0fc4f4f93f774b800d53fa03554752a166999310e | 0 | complete |
| add_m05 | 9fd2a8ce0f4d3712d66cf6cf159e8e633bbdb15d3d5e8f4f74fcabe1c2da516d | c2c2d2817c7fd27dddfe47e0fc4f4f93f774b800d53fa03554752a166999310e | 0 | complete |
| add_m1 | a64611a8d3746e62b65b6a1f72a9845c343bb30e233f476da8c03cd6c60bdde4 | c2c2d2817c7fd27dddfe47e0fc4f4f93f774b800d53fa03554752a166999310e | 0 | complete |
| add_m2 | 710cd8e90f2d680f269bf5548979d5f33b5b7454d453358add52b0dc910b5d29 | c2c2d2817c7fd27dddfe47e0fc4f4f93f774b800d53fa03554752a166999310e | 0 | complete |
| random_m2 | a7e4da0228ce14c13fcbc306065eec50cacfb496ddbe7b9bcb5290064dd409f6 | c2c2d2817c7fd27dddfe47e0fc4f4f93f774b800d53fa03554752a166999310e | 0 | complete |
| scaled_m05 | d21042347d23cf3b77973988dca22cb1c799e9a6b78c4e459c45deb85fe90b6a | c2c2d2817c7fd27dddfe47e0fc4f4f93f774b800d53fa03554752a166999310e | 0 | complete |

Failed attempts remain excluded and are distinguishable: baseline and gate each have exit=1 and no completion marker. They are not merged with baseline_v1 or gate_v1.

## Run accounting and pending

There were 10 launcher starts in this literal phase. Seven completed successfully: baseline_v1, gate_v1, add_m05, add_m1, add_m2, random_m2, and scaled_m05. The failed baseline attempt generated 0 GUI/text outputs. The failed gate attempt generated 8 partial GUI outputs and 0 text outputs, with no completion marker; those 8 are excluded from arm comparisons. The random_scaled_m05 startup attempt generated 0 GUI/text outputs and no completion/comparison marker.

scaled_m05 is complete and included in the verdict below. random_scaled_m05 is NOT RUN as an arm: its launcher exited 143 during startup after the stop-first-healthy-collapse rule was triggered by the three corrupted text controls discovered in scaled_m05. It has no output or done file.

Screenshot-grounded semantic efficacy, online task success, and label quality are NOT RUN by this audit.

## scaled_m05 audit addendum

scaled_m05 uses mode=add, strength=-0.5, scope=boundary, scaled=true, and the same manifest/axes/reference identities as the other completed arms. It has 56 GUI + 3 text outputs, 7 frozen row keys x 8 seeds, exact paired metadata and input lengths, matching top-level/text schemas, no truncation/errors, and valid END/im_end token boundaries. Counts are fs+ 15/16 and fs- 11/16.

Compared with add_m05, all pair keys, seeds, metadata, schemas, prompts, and generation settings match. The decision map has exactly one flip: row key results_diag2:libreoffice_calc/0cecd4f3-74de-457b-ba94-29ad6b5dafb6:16 at seed 4103, where add_m05 is answer=true and scaled_m05 is answer=false/valid_nonanswer=true. This is a real screening decision change, with no truncation or error. The final runtime counters are boundary_rows=56, target_rows=560, changed_rows=560; requested delta norm=9838.914322 and realized BF16 delta norm=9838.777501.

scaled_m05 JSONL SHA256: d21042347d23cf3b77973988dca22cb1c799e9a6b78c4e459c45deb85fe90b6a. Its runner SHA256 is c2c2d2817c7fd27dddfe47e0fc4f4f93f774b800d53fa03554752a166999310e.

Cumulative generated-output accounting is 392 GUI + 21 text outputs across the seven completed arms. The incomplete gate attempt adds 8 GUI outputs. Thus 400 GUI outputs and 421 total retained outputs are present. No output was generated by the failed baseline or random_scaled_m05 startup attempts.


## Final RESULT/REPORT documentary cross-check

This final read-only check compared RESULT.json and REPORT.md with the audited JSONL, done, comparison, and job files.

- Accounting agrees exactly: 10 starts, 7 completed arms, 392 completed GUI + 21 completed text outputs, 8 GUI outputs from the incomplete gate attempt, and 421 retained outputs total.
- Every completed-arm output hash in RESULT.json matches its audited JSONL. Text hashes also match the audited text JSONL files.
- The report rates match the paired audit: all literal arms and random_m2 are fs+ 15/16 and fs- 12/16; scaled_m05 is fs+ 15/16 and fs- 11/16, with exactly one answer flip versus baseline at the audited pair.
- RESULT/REPORT runtime norms are the aggregate done-file scope including 56 GUI plus 3 text probes (59 rows / 590 targeted rows). The earlier quantitative table in this file reports GUI-context event scope only (56 rows / 560 targeted rows). The two scopes are consistent, not contradictory. Aggregate realized norms are gate 15.563233, add_m05 417.473252, add_m1 834.498196, add_m2 1668.812672, random_m2 1668.801343, and scaled_m05 10365.836428.
- RESULT explicitly has candidate=false, checkpoint_compiled=false, uploaded=false, online_osworld_tested=false, and weight_edits=false. REPORT likewise states no admitted candidate and no compilation, upload, or online OSWorld result. Its NOT RUN claims are consistent with the audit.
- random_scaled_m05 is recorded as exit 143, zero outputs, no done marker, and no behavioral result. It is correctly excluded from completed-arm rates.

Documentary verdict: RAN / PASSED / CORRECT. This check did not run GPU, compilation, upload, OSWorld, screenshot review, or any new data/test read; those remain NOT RUN here.
