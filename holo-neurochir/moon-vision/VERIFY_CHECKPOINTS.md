# Moon-vision independent verification verdict

Source evidence:

- JSON: `/workspace/astra/moon-vision/VERIFY_CHECKPOINTS.json`
- Log: `/workspace/astra/moon-vision/independent_verify.log`
- Verifier: `/workspace/astra/moon-vision/independent_verify.py`

RAN: **YES**. The independent verifier completed against both generated CUA checkpoints.

PASSED: **YES**. The JSON status is `PASS`; both checkpoints passed with exit status 0:

| checkpoint | beta | tensor coverage | changed elements | update L2 | BF16 changed elements | BF16 update L2 |
|---|---:|---:|---:|---:|---:|---:|
| `/dev/shm/moon-vision/cua_b050` | 0.5 | 297 visual + 427 nonvisual / 724 total | 169,449,071 | 0.7584099583777293 | 169,449,071 | 0.7584099583777293 |
| `/dev/shm/moon-vision/cua_b100` | 1.0 | 297 visual + 427 nonvisual / 724 total | 221,128,354 | 1.2808340288524802 | 221,128,354 | 1.2808340288524802 |

CORRECT: **YES for the checked artifact contract**. The verifier independently reopened the source and output safetensors, recomputed all 297 visual formulas, checked raw-byte identity for all 427 nonvisual tensors, validated Holo config/index equality, validated output file and sidecar SHA256 values, checked source provenance, and checked finite values and dtype/shape preservation.

NOT RUN / LIMITS:

- The Holo extrapolation checkpoint `holo_g025` has not been independently verified yet.
- No serving runtime or baseline comparison was run by this verifier.
- Cohort and scoring remain outside scope.
