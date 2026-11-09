# Independent artifact verification: CUA beta 1.00

**Verdict: PASS.**

- Manifest provenance: arithmetic merge, beta `1.0`, Holo reference target, Qwen reference, donor `/dev/shm/astra_merge_cua`.
- All 724 indexed and serialized tensors match Holo's key/shard layout, shapes, and dtypes and are finite.
- All 426 language tensors exactly match independently recomputed `Holo + 1.0 * (CUA - Qwen)` after conversion to Holo's target dtype.
- All 298 vision/head/policy-preserved tensors are bitwise tensor-equal to Holo.
- 364 language tensors physically differ from Holo; manifest changed/retained sets exactly match physical equality.
- Both shards, manifest file sizes and SHA-256 hashes, and all 11 expected byte-identical Holo auxiliary files pass.
- Local-only metadata loading passes as `Qwen3_5Config` and `Qwen3VLProcessor`.
- Full model allocation was **NOT RUN**; no GPU was initialized.

Authoritative JSON: `/root/astra_merge_evidence/VERIFY_CUA_B100.json`.

Checker: `/workspace/astra/astra-merge/verify_candidate.py`, SHA-256 `115e24029fc1302a1d823e70d1e64ce32571f3317550827f1ca98f06c349d4cd`.
