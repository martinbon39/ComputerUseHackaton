# Independent artifact verification: CUA beta 0.25

**Verdict: PASS.**

- All 724 indexed and serialized tensors were checked for exact key placement, Holo shape/dtype, and finitude.
- All 426 language tensors exactly match the independently recomputed arithmetic formula `Holo + 0.25 * (CUA - Qwen)` after conversion to Holo's target dtype.
- All 298 vision/head/policy-preserved tensors are bitwise tensor-equal to Holo.
- 325 language tensors physically differ from Holo; the remaining formula results round back to Holo in the target dtype. Manifest changed/retained lists exactly match physical equality.
- Both shards, all manifest sizes/hashes, and all 11 byte-identical Holo auxiliary files pass.
- Local-only loading passes as `Qwen3_5Config` and `Qwen3VLProcessor`.
- Full model allocation was **NOT RUN**.

Durable evidence: `/workspace/astra/astra-merge/VERIFY_CUA_B025.json`.

Reusable independent checker: `/workspace/astra/astra-merge/verify_candidate.py`, SHA-256 `bcedf391754d6cd8041c621c24384e17fce98866c8e6c6c1dd9213bc1a4ae84e`. It reads merge provenance and parameters from the candidate manifest, but independently implements arithmetic verification and imports no maker functions. It currently rejects non-arithmetic methods explicitly.
