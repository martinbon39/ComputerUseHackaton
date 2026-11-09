# Independent artifact verification: dual arithmetic mean beta 0.50

**Verdict: PASS.**

- Manifest provenance and donor order: CUA (`/dev/shm/astra_merge_cua`), then Fara (`/root/astra_merge_fara`); arithmetic beta `0.5` against the declared Qwen reference and Holo target.
- All 724 serialized tensors match Holo's exact index/shard map, shapes, and dtypes and are finite.
- All 426 language tensors exactly equal independently recomputed `Holo + 0.5 * mean(CUA - Qwen, Fara - Qwen)` after conversion to Holo's target dtype.
- All 298 vision/head/policy-preserved tensors are bitwise tensor-equal to Holo.
- 364 language tensors physically differ from Holo; manifest changed/retained sets exactly match observed physical equality.
- Both shards, manifest sizes and SHA-256 hashes, and all 11 expected byte-identical Holo auxiliary files pass.
- Local-only loading passes as `Qwen3_5Config` and `Qwen3VLProcessor`.
- Full model allocation was **NOT RUN**; no GPU was initialized.

Authoritative JSON: `/root/astra_merge_evidence/VERIFY_DUAL_MEAN_B050.json`.

Checker: `/workspace/astra/astra-merge/verify_candidate.py`, SHA-256 `115e24029fc1302a1d823e70d1e64ce32571f3317550827f1ca98f06c349d4cd`.
