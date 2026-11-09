# Independent artifact verification: CUA mid-layers beta 0.25

**Verdict: PASS.**

- Manifest range is exactly `[12,24)` and observed selected layers are exactly 12 through 23.
- All 724 tensors match Holo's index/shard map, shapes, and dtypes and are finite.
- All 159 selected keys exactly equal independently recomputed `Holo + 0.25 * (CUA - Qwen)` after target-dtype conversion.
- All 565 keys outside the selection—including unselected language layers, embeddings, final norm, vision, and head—are bitwise tensor-equal to Holo.
- 125 selected tensors physically changed; 34 selected formula results round back to Holo. Manifest changed/retained sets exactly match the observed 125/599 physical split.
- Changed tensors by layer: 12:11, 13:11, 14:11, 15:9, 16:11, 17:11, 18:11, 19:9, 20:11, 21:11, 22:10, 23:9.
- Actual update L2 norm: `0.6138762129425228`; changed elements: `486244378`.
- Both shards, manifest hashes/sizes, all 11 byte-identical Holo auxiliaries, and local-only `Qwen3_5Config` / `Qwen3VLProcessor` loading pass.
- Full model allocation was **NOT RUN**; no GPU was initialized.

Authoritative JSON: `/root/astra_merge_evidence/VERIFY_CUA_MID_B025.json`.

Checker: `/workspace/astra/astra-merge/verify_candidate_v2.py`, SHA-256 `cf2784fbda577d13bb9b87c66c5c7a1407447c5a4909aad2050f5db5226f103e`.

## Final boundary/design review

No issue found in the scoped v2 diff. Maker and checker both use the same half-open boundary semantics, while the checker independently parses keys and reconstructs the expected layer set. The maker's optional range preserves the existing whole-language route; it does not add a silent recovery path. The apparent duplicated boundary logic across maker and checker is intentional independent verification and should not be factored into a shared abstraction. No defensive fallback or second selection path was added inside the scoped implementation.
