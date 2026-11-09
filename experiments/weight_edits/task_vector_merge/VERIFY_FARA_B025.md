# Independent artifact verification: Fara beta 0.25

**Verdict: PASS.**

- Manifest provenance: arithmetic merge, beta `0.25`, donor `/root/astra_merge_fara` against the declared Qwen reference and Holo target.
- All 724 serialized tensors match Holo's index, shard placement, shapes, and dtypes and are finite.
- All 426 language tensors exactly equal independently recomputed `Holo + 0.25 * (Fara - Qwen)` after conversion to Holo's target dtype.
- All 298 vision/head/policy-preserved tensors are bitwise tensor-equal to Holo.
- 364 language tensors physically differ from Holo; manifest changed/retained sets exactly match observed physical equality.
- Both shards, manifest sizes and SHA-256 hashes, and all 11 expected byte-identical Holo auxiliary files pass.
- Local-only loading passes as `Qwen3_5Config` and `Qwen3VLProcessor`.
- Full model allocation was **NOT RUN**; no GPU was initialized.

Authoritative JSON: `/root/astra_merge_evidence/VERIFY_FARA_B025.json`.

Checker: `/workspace/astra/astra-merge/verify_candidate.py`, SHA-256 `115e24029fc1302a1d823e70d1e64ce32571f3317550827f1ca98f06c349d4cd`.
