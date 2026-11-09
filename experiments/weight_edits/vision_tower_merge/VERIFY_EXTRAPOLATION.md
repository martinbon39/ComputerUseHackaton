# Moon-vision E025 independent verification verdict

Evidence:

- Verifier log: `/workspace/astra/moon-vision/independent_verify_extrapolation.log`
- Verifier JSON: `/workspace/astra/moon-vision/VERIFY_EXTRAPOLATION.json`
- Checkpoint: `/dev/shm/moon-vision/holo_g025`

RAN: **YES**. `independent_verify_extrapolation.py` completed with exit status 0 under the requested CPU environment, `taskset -c 40,41`, and 600-second timeout.

PASSED: **YES**. The JSON status is `PASS`.

CORRECT: **YES for the E025 artifact contract**. The independent verifier checked:

- 724 total tensors: 297 selected visual tensors and 427 nonvisual tensors.
- Every selected tensor against `cast_H_dtype(H.float32 + 0.25 * (Holo.float32 - Qwen.float32))`, including all merger tensors.
- Raw byte identity for all 427 nonvisual tensors against Holo.
- Exact Holo `config.json` and `model.safetensors.index.json` equality.
- Tensor shape, dtype, and finite-value checks for sources and output.
- Output manifest file sizes and SHA256 values, all copied Holo sidecars, and the three-source `source_provenance.json` hashes.

Measured output:

| checkpoint | beta | changed elements | update L2 | BF16 serving changed elements | BF16 serving update L2 |
|---|---:|---:|---:|---:|---:|
| `/dev/shm/moon-vision/holo_g025` | 0.25 | 228,976,750 | 5.028068901394733 | 228,976,750 | 5.028068901394733 |

The independent norm agrees with the builder’s reported `5.028068901394734` within floating-point accumulation precision. Holo, output, and all selected vision tensors are BF16 in storage, so the actual BF16 serving metrics are identical to the stored output metrics.

NOT RUN / LIMITS:

- No serving runtime or baseline comparison was run.
- Cohort and scoring remain outside scope.
