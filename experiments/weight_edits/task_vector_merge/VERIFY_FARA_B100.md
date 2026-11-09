# Independent artifact verification: Fara beta 1.00

**Verdict: PASS.**

- Manifest provenance: arithmetic merge, beta `1.0`, donor `/root/astra_merge_fara` against the declared Qwen reference and Holo target.
- All 724 serialized tensors match Holo's index, shard placement, shapes, and dtypes and are finite.
- All 426 language tensors exactly equal independently recomputed `Holo + 1.0 * (Fara - Qwen)` after conversion to Holo's target dtype.
- All 298 vision/head/policy-preserved tensors are bitwise tensor-equal to Holo.
- 405 language tensors physically differ from Holo; manifest changed/retained sets exactly match observed physical equality.
- Both shards, manifest sizes and SHA-256 hashes, and all 11 expected byte-identical Holo auxiliary files pass.
- Local-only loading passes as `Qwen3_5Config` and `Qwen3VLProcessor`.
- Full model allocation was **NOT RUN**; no GPU was initialized.

Authoritative JSON: `/root/astra_merge_evidence/VERIFY_FARA_B100.json`.

## Independent verifier

Checker: `/workspace/astra/astra-merge/verify_candidate.py`
SHA-256/version: `115e24029fc1302a1d823e70d1e64ce32571f3317550827f1ca98f06c349d4cd`

Invocation, with environment and CPU affinity:

```sh
export OMP_NUM_THREADS=2 MKL_NUM_THREADS=2 OPENBLAS_NUM_THREADS=2
taskset -c 40,41 /workspace/venv/bin/python \
  /workspace/astra/astra-merge/verify_candidate.py \
  /dev/shm/merge_fara_b100 \
  /root/astra_merge_evidence/VERIFY_FARA_B100.json
```
