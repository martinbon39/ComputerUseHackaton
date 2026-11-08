# Independent checkpoint audit

RAN: yes. PASSED: True. CORRECT: CHECKPOINT IDENTITY AND DOSE PASS; D REALIZED NORM MATCHED WITHIN 0.1 PERCENT PER TENSOR.

Finished 2026-11-08T07:04:42.121907+00:00; CPU affinity [40, 41], torch threads 2, no GPU.

## Identity and dose

- A: Hcompany/Holo-3.1-4B revision 8c88265a5a159bfd1492db9243733dd2e6e04a6e; both shard hashes matched their HF LFS content addresses.
- B: all 13 files matched the restored manifest and historical CHECKPOINTS.json; arithmetic CUA beta 0.5, full layer scope.
- C/D: all 15 files each matched manifests, and manifests match historical orbit archives. Dose 1.0, shared factors hash, 24 edited tensors. D includes its archived per-tensor norm calibration. The actual BF16 weights matched the exact requested formulas; all 700 other tensors equal A.
- All four: identical configuration, tokenizer, chat template, processor files and 724 tensor shapes/dtypes.

## Random control norms

Requested global L2: C=7.338905332, D=7.33950849.
Maximum per-tensor unscaled-factor relative mismatch from stored FP32 factors: 1.55e-09.
Realized BF16 global L2: C=7.345827105, D=7.346396873; D/C=1.000077563.
Realized per-tensor D/C range: [0.9999572265, 1.000296318].

D matches C in realized BF16 norm within the historical 0.1 percent per-tensor contract. The exact archived control_scale is included in the independently checked BF16 formula. It shares C's conditioning/right factors and randomizes the left factors. Full per-tensor values, SHA256 hashes and check results are in VERIFY_CHECKPOINTS.json.

## Limitations and NOT RUN

- Unscaled factors match in norm before BF16 rounding. D additionally applies archived per-tensor control_scale to match realized norms within the historical 0.1 percent tolerance; the measured residual mismatch is reported.
- The random control retains each learned right/conditioning factor and replaces/scales the left factor. It is not isotropic random noise over all model parameters.
- B formula was previously independently verified; this audit recomputes every file hash and matches that exact attested checkpoint, but does not recompute its donor arithmetic.
- Checkpoint files are audited; this does not identify GPU-resident weights, check server request settings, or establish behavioral efficacy.
- C/D manifests exactly match the historical copies archived on orbit. Cloud-account credentials were not inspected.
- NOT RUN: GPU inference; live server model identity; new B donor formula computation; behavior and cohort/statistical audit.
