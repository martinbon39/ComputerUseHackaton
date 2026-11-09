# Independent artifact verification: CUA beta 0.50

**Verdict: PASS** for serialized artifact correctness and HF metadata loading.

Artifact: `/dev/shm/merge_cua_b050`
Build report: `/workspace/astra/astra-merge/cua_b050_build.json`
Machine-readable evidence: `/workspace/astra/astra-merge/VERIFY_CUA_B050.json`

Verified independently, CPU-only with two pinned cores:

- The output index exactly equals Holo's 724-key weight map; all index-referenced shards exist, no extra shards exist, and serialized keys/shard assignments exactly match the index.
- All 724 tensors have Holo's shape and dtype and contain only finite values.
- All 426 `model.language_model.*` tensors exactly equal, after target-dtype conversion, `Holo.float() + 0.5 * (CUA.float() - Qwen.float())`.
- All 298 policy-preserved tensors, including vision and `lm_head.weight`, are bitwise tensor-equal to Holo.
- 338 language tensors physically differ from Holo. Another 88 satisfy the exact formula but round back to the original value in the target dtype. The build manifest's changed/retained lists exactly describe this physical equality split.
- Both output safetensor shards and all 11 expected auxiliary files are present. Manifest file sizes and SHA-256 hashes pass. Auxiliary files are byte-identical to Holo.
- Local-only metadata loading passes: `AutoConfig` -> `Qwen3_5Config`; `AutoProcessor` -> `Qwen3VLProcessor`.

Full CPU model allocation was intentionally **NOT RUN**. Runtime model-load/inference proof belongs to the separately launched vLLM service.
