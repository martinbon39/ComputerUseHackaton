# Independent review: `merge.py`

Scope: static, read-only review of `/tmp/astra-merge-work/merge.py`. No real checkpoint/output artifact has been inspected yet, so this is **not** a blanket success verdict.

## Must fix

1. **Validate `--density` before either sparse algorithm** (`merge.py:113-126`, CLI definition at `merge.py:156`).
   - DARE is unbiased only for `0 < density <= 1`. At `density > 1`, every element is retained and then divided by `density`, shrinking the update incorrectly. At `density == 0`, it divides by zero; negative density is also invalid.
   - TIES sends invalid counts to `topk` for densities above 1, while zero/negative density is silently coerced to one retained element by `max(1, ...)` rather than rejected.
   - Required gate: reject unless `0 < density <= 1` for TIES/DARE (and ideally document whether density is ignored for arithmetic).

2. **If “top 20% density” means strict whole-model task-vector density, TIES currently does not meet it** (`merge.py:112-116`).
   - Pruning is independently `ceil(0.2 * numel)` for every tensor and retains at least one element per tensor. The aggregate retained count is therefore `sum(ceil(.2*n_i))`, which can exceed 20%, substantially so for many small tensors.
   - This implementation does correctly perform per-tensor top-magnitude trimming, sign election from the trimmed donor vectors (`merge.py:117`), and mean aggregation of sign-aligned retained values (`merge.py:118-124`). If per-tensor density is the intended contract, record that explicitly and this item is not a blocker.

## Verified statically

- **Task arithmetic:** arithmetic computes each task vector as `donor - reference` and applies `Holo + beta * mean(task vectors)` (`merge.py:108-129`). This matches the manifest formula.
- **DARE formula:** for a valid probability, independent Bernoulli retention followed by division by density is the standard unbiased rescaling, then donors are averaged (`merge.py:125-126`). RNG is seeded once and deterministic for a fixed tensor/donor traversal (`merge.py:99`).
- **Compatibility gates:** every Holo key except explicit `lm_head.weight` must exist in reference/donor, unexpected non-`mtp.*` keys are rejected, common shapes are checked, text architecture fields are compared, and vision configs must match (`merge.py:44-60`).
- **Holo vision and head preservation:** only keys beginning `model.language_model.` are edited (`merge.py:104-107`). `model.visual.*` and top-level `lm_head.weight` are written from Holo unchanged. The explicit head exclusion in compatibility is consistent with this policy.
- **HF layout construction:** all Holo non-safetensors regular files, including the existing shard index/config/tokenizer files, are copied; each indexed Holo shard is regenerated with the same Holo key partition (`merge.py:90-94`, `100-139`). This is structurally plausible but still needs artifact-level verification against actual files, index, shapes, and loadability.
- No training, gradients, harness changes, or prompt changes appear in this script.

## Required artifact check when ready

On the pod, verify independently that: every index-referenced shard exists; index keys exactly equal serialized tensor keys; all output shapes/dtypes match Holo; vision tensors and `lm_head.weight` are bitwise tensor-equal to Holo; at least intended language tensors changed; all expected HF auxiliary files exist; `AutoConfig`, processor/tokenizer, and the appropriate model class load from the output without fetching replacements. Also inspect the build/report manifests and hashes. Until then, runtime correctness and complete HF output remain **NOT RUN**.

## Follow-up after revision

- Density validation was added at `merge.py:164-165`; the first must-fix item is resolved.
- The declared TIES protocol is per-tensor top-20%, so the global-density caveat is informational rather than a blocker.
- Config alias check confirmed on the pod with Transformers 5.22.2, without loading weights. Raw Holo `vision_config.model_type=qwen3_5_vision` and raw Qwen `model_type=qwen3_5` both instantiate as `Qwen3_5VisionConfig` and normalize to `model_type=qwen3_5_vision`. All architectural fields normalize identically. The remaining normalized `dtype` difference (`float32` versus `None`) is load metadata, not vision architecture; preserving Holo's config and tensors makes excluding it from donor compatibility reasonable.
