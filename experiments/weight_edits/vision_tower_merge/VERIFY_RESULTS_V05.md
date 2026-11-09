# Independent V05 raw-results verification

Static recomputation only; no server, GPU, heldout/reserve data, screenshot interpretation, or semantic judgment.

The reusable extractor is `/tmp/moon-vision/extract_diff.py` (not in the repository). It reads only `FROZEN.json`, `schema.json`, frozen payloads, baseline A, and the requested candidate arm. It asserts exactly 220 rows, 220 unique task/seed pairs, the four frozen seeds, frozen row equality, payload SHA equality, and independent JSON-schema validity. It emits the requested group packet with audit-packet/history/image references and raw response fields.

For A and V05, all 220 pairs are present and exact. All 220 payload hashes match their frozen payload bytes. Both arms have zero schema-invalid rows, zero transport errors, and zero truncations.

Recomputed group counts:

| Arm | Group | Rows | Answer | Valid nonanswer | Invalid | Errors | Truncated |
|---|---|---:|---:|---:|---:|---:|---:|
| A | fs+ | 76 | 55 | 21 | 0 | 0 | 0 |
| A | fs- | 80 | 75 | 5 | 0 | 0 | 0 |
| A | healthy | 64 | 5 | 59 | 0 | 0 | 0 |
| A | all | 220 | 135 | 85 | 0 | 0 | 0 |
| V05 | fs+ | 76 | 57 | 19 | 0 | 0 | 0 |
| V05 | fs- | 80 | 75 | 5 | 0 | 0 | 0 |
| V05 | healthy | 64 | 6 | 58 | 0 | 0 | 0 |
| V05 | all | 220 | 138 | 82 | 0 | 0 | 0 |

These recomputed counts match the corresponding baseline and V05 entries in `SUMMARY.json` exactly. The healthy packet artifact is `/tmp/moon-vision/HEALTHY_DIFF_V05.json` (not in the repository), containing 16 contexts × 4 seeds, raw A/V05 tool calls, note/thought/reasoning fields, and packet references. No outcome interpretation is included.
