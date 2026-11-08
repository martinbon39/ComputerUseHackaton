# Independent E025 raw-results verification

Static recomputation only; no server, GPU, heldout/reserve data, screenshot interpretation, or semantic judgment.

Created [HEALTHY_DIFF_E025.json](/tmp/moon-vision/HEALTHY_DIFF_E025.json) with 16 healthy contexts × 4 seeds, raw A/E025 response fields, and audit packet references. Existing `FS_DIFF_E025.json` was preserved. The reusable checker remains [extract_diff.py](/tmp/moon-vision/extract_diff.py).

All A and E025 arms contain exactly 220 unique task/seed pairs with seeds `17000–17003`. Every row matches the frozen row and every payload SHA-256 matches the frozen payload. Both arms have zero schema-invalid rows, transport errors, and truncations. Recomputed group counts match `SUMMARY.json`; the same count comparison was also true for V05 and V10.

| Arm | Group | Rows | Answer | Valid nonanswer | Invalid | Errors | Truncated |
|---|---|---:|---:|---:|---:|---:|---:|
| A | fs+ | 76 | 55 | 21 | 0 | 0 | 0 |
| A | fs- | 80 | 75 | 5 | 0 | 0 | 0 |
| A | healthy | 64 | 5 | 59 | 0 | 0 | 0 |
| A | all | 220 | 135 | 85 | 0 | 0 | 0 |
| E025 | fs+ | 76 | 57 | 19 | 0 | 0 | 0 |
| E025 | fs- | 80 | 76 | 4 | 0 | 0 | 0 |
| E025 | healthy | 64 | 4 | 60 | 0 | 0 | 0 |
| E025 | all | 220 | 137 | 83 | 0 | 0 | 0 |

Independent task bootstrap used 20,000 PCG64 replicates with seed `20261108`, paired four-seed task means, and the analyzer metrics (`answer` for fs+/fs-, `valid_nonanswer` for healthy). Results match `SUMMARY.json` for all three candidate arms:

| Arm | Group | Delta pp | 95% bootstrap interval | Tasks |
|---|---|---:|---:|---:|
| V05 | fs+ | 2.631578947368421 | [-2.631578947368421, 7.894736842105263] | 19 |
| V05 | fs- | 0.0 | [0.0, 0.0] | 20 |
| V05 | healthy | -1.5625 | [-4.6875, 0.0] | 16 |
| V10 | fs+ | -1.3157894736842104 | [-5.263157894736842, 2.631578947368421] | 19 |
| V10 | fs- | -2.5 | [-7.5, 0.0] | 20 |
| V10 | healthy | 0.0 | [0.0, 0.0] | 16 |
| E025 | fs+ | 2.631578947368421 | [-2.631578947368421, 7.894736842105263] | 19 |
| E025 | fs- | 1.25 | [0.0, 3.75] | 20 |
| E025 | healthy | 1.5625 | [0.0, 4.6875] | 16 |

The nine candidate text controls (three per V05, V10, and E025) are present, each has `finish_reason=stop`, `error=null`, and `truncated=false`. Their exact contents are: `45`; `La tasse bleue est sur la table.`; and `Apple, banana, orange.` for the arithmetic, translation, and fruit prompts respectively.

This file records integrity and numerical agreement only; it makes no semantic or quality judgment.
