# Moon-vision builder review

Scope: read-only review of `/workspace/astra/moon-vision/build_vision.py` and the Holo, Qwen, and CUA headers/configs/indexes. Cohort and scoring are excluded.

## Result

The builder logic passes the requested current-input checks:

- Holo is `/workspace/hf/hub/models--Hcompany--Holo-3.1-4B/snapshots/8c88265a5a159bfd1492db9243733dd2e6e04a6e`; Qwen is `/root/expo/base`; CUA is `/dev/shm/astra_merge_cua` (`build_vision.py:14-16`).
- Holo's index has 724 tensors: 297 `model.visual.*`, 6 of them `model.visual.merger.*`, and 427 nonvisual tensors.
- `vision_delta.json` records CUA−Qwen L2 `1.2800996175035877` and `221992483` nonzero elements. The active branch therefore uses CUA with coefficients 0.5 and 1.0 (`build_vision.py:129-143`).
- The selected formula is `cast_H_dtype(H.float32 + beta * (CUA.float32 - Qwen.float32))` (`build_vision.py:92,104`). The visual prefix includes merger tensors.
- Output config and index are compared exactly with Holo, all output tensors are checked for shape/dtype and finiteness, selected tensor bytes are compared with the formula, and nonvisual tensor bytes are compared with Holo (`build_vision.py:93-108`).
- Source mutation checking hashes the Holo/Qwen/CUA model shards, config, and index before and after construction (`build_vision.py:51-52,134-146`).

## Findings

### MEDIUM: builder verification is not independent

The output checks are performed by the builder itself and use the same `Weights` access and formula implementation that creates the output (`build_vision.py:98-108`). A fresh verifier must independently reopen both checkpoints and recompute all 297 formulas plus raw-byte equality for all 427 nonvisual tensors. That verifier is uploaded as `/workspace/astra/moon-vision/independent_verify.py`; it must run only after both CUA checkpoints finish.

### LOW: copied sidecars are outside source provenance

The provenance map covers only indexed safetensors, `config.json`, and `model.safetensors.index.json` (`build_vision.py:51-52`). The build copies other Holo sidecars (`build_vision.py:85-87`) but does not compare those source files before and after construction. The independent verifier compares every output sidecar against the current Holo source.

### LOW: BF16 serving requires an explicit loader decision

Metadata inspection found all 724 Holo tensors stored as BF16, while Holo's top-level and vision config advertise `dtype: float32`. The builder preserves the Holo tensor dtype and config. A serving loader that trusts config dtype can upcast the model to FP32; serving should explicitly select BF16 when that is required for memory and runtime behavior. The verifier reports changed elements and L2 after casting original/output vision tensors to BF16.

### INFO: inactive zero-delta fallback

If CUA−Qwen becomes exactly zero, the builder switches to Holo direction with coefficients 0.25 and 0.5 (`build_vision.py:129-139`). The current measured CUA delta is nonzero, so this fallback is inactive. If the contract is strictly CUA-only, fail closed instead of taking this branch.
