# Independent artifact verification: CUA mid-layers beta 0.50

**Verdict: PASS.**

- Manifest range is exactly half-open `[12,24)`; observed selected layers are exactly 12 through 23.
- All 724 tensors match Holo's index/shard map, shapes, and dtypes and are finite.
- All 159 selected tensor keys exactly equal independently recomputed `Holo + 0.5 * (CUA - Qwen)` after target-dtype conversion.
- All 565 keys outside the selection—including layers 0–11 and 24–31, embeddings, final norm, vision, and `lm_head.weight`—are bitwise tensor-equal to Holo.
- 126 selected tensors physically changed. Another 33 selected formula results round back to Holo in the target dtype. The manifest's 126 changed and 598 retained keys exactly match observed physical equality.
- Physically changed tensors by layer: 12:11, 13:11, 14:11, 15:9, 16:11, 17:11, 18:11, 19:9, 20:11, 21:11, 22:11, 23:9.
- Manifest actual update L2 norm: `1.3865373135738688`; changed elements: `780857461`.
- Both shards, manifest hashes/sizes, all 11 byte-identical Holo auxiliary files, and local-only `Qwen3_5Config` / `Qwen3VLProcessor` loading pass.
- Full model allocation was **NOT RUN**; no GPU was initialized.

Authoritative JSON: `/root/astra_merge_evidence/VERIFY_CUA_MID_B050.json`.

Checker: `/workspace/astra/astra-merge/verify_candidate_v2.py`, SHA-256 `cf2784fbda577d13bb9b87c66c5c7a1407447c5a4909aad2050f5db5226f103e`.
