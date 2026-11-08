# Final capture verification

## Verdict

RAN / PASSED / CORRECT for the frozen replay and capture artifacts. NOT RUN: model rerun, refit, generation, or statistical analysis.

## Checks performed

- `capture_receipt_156.json` exists: 156 completed and 156 started forwards.
- `forwards.jsonl` has 156 rows, forward numbers 1 through 156, with 156 unique `(context_id, condition)` pairs and no missing pair among 39 contexts × `a/b/c/d`.
- Every forward's `input_ids_sha256` and `total_tokens` match the corresponding immutable `PREFLIGHT.json` variant.
- The 39 original-condition capture files exist and each residual array has shape `(6, 3, 2560)`, with finite values.
- Every capture stores layers `[8, 12, 16, 20, 24, 28]` and positions equal to its preflight metadata.
- Every capture SHA256 equals the `capture_sha256` recorded in its original-condition forward row.
- Receipt identifies the exact Holo-3.1-4B snapshot, BF16, CUDA device, and zero-based layer convention.

## Limits

This is an artifact/provenance check after completion. It does not rerun the model, validate generated behavior, refit probes, or judge the scientific/statistical conclusions.

