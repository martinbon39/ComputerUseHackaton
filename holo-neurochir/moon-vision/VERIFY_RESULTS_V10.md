# Independent V10 raw-results verification

Static recomputation only; no server, GPU, heldout/reserve data, screenshot interpretation, or semantic judgment.

The reusable extractor is [extract_diff.py](/tmp/moon-vision/extract_diff.py). It independently checks exactly 220 rows per arm, 220 unique task/seed pairs, seeds `17000–17003`, frozen row identity, payload SHA-256 identity, and JSON-schema validity. It emitted [HEALTHY_DIFF_V10.json](/tmp/moon-vision/HEALTHY_DIFF_V10.json), containing all 16 healthy contexts × 4 seeds with raw A/V10 response fields and audit packet references. Existing [FS_DIFF_V10.json](/tmp/moon-vision/FS_DIFF_V10.json) was left untouched.

All A and V10 source pairs are complete: 220/220 each. Every payload hash matches the frozen payload. Both arms have zero schema-invalid rows, zero transport errors, and zero truncations.

Recomputed group counts, matching `SUMMARY.json` exactly:

| Arm | Group | Rows | Answer | Valid nonanswer | Invalid | Errors | Truncated |
|---|---|---:|---:|---:|---:|---:|---:|
| A | fs+ | 76 | 55 | 21 | 0 | 0 | 0 |
| A | fs- | 80 | 75 | 5 | 0 | 0 | 0 |
| A | healthy | 64 | 5 | 59 | 0 | 0 | 0 |
| A | all | 220 | 135 | 85 | 0 | 0 | 0 |
| V10 | fs+ | 76 | 54 | 22 | 0 | 0 | 0 |
| V10 | fs- | 80 | 73 | 7 | 0 | 0 | 0 |
| V10 | healthy | 64 | 5 | 59 | 0 | 0 | 0 |
| V10 | all | 220 | 132 | 88 | 0 | 0 | 0 |

Independent task-bootstrap recomputation used 20,000 PCG64 replicates with seed `20261108`, paired four-seed task means, and the same analyzer metric (`answer` for fs+/fs-, `valid_nonanswer` for healthy). Endpoints match `SUMMARY.json`:

| Group | Delta pp | 95% bootstrap interval | Tasks |
|---|---:|---:|---:|
| fs+ | -1.3157894736842104 | [-5.263157894736842, 2.631578947368421] | 19 |
| fs- | -2.5 | [-7.5, 0.0] | 20 |
| healthy | 0.0 | [0.0, 0.0] | 16 |

This file records integrity and numerical agreement only; it makes no semantic or quality judgment.
