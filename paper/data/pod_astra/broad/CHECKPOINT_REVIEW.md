# Checkpoint review

`verify_checkpoint.py` is the independent CPU checker for `build_checkpoint.py`.
It sets PyTorch/OpenMP/BLAS to two threads and processes one safetensors shard at a
time. It checks the full 724 tensor index, source/target tensor keys, shapes, dtypes,
finite values, and exact equality of every unedited tensor. Each of the 24 edited
writers in layers 12--23 is checked against the builder's exact expression
`(source.float() + dose * (left @ right)).to(source.dtype)`.

The factor checks require both `learned` and `random` arms, the exact 24 writer names,
float32 factors with `[2560, rank] @ [rank, 9216]` MLP shapes or
`[2560, rank] @ [rank, 4096]` mixer shapes, finite values, matching right factors, and
matched random/learned ideal factor norms. For a random checkpoint, each recorded
`control_scale` must be finite and in `[0.5, 2.0]`; the verifier independently rebuilds
the learned same-dose BF16 perturbation, requires the recorded target norm to match it,
checks the scaled random BF16 formula exactly, and requires the realized norm gap to be
below `1e-3`. A learned checkpoint may omit the control fields (or use scale `1` with a
null target). Pack metadata must identify the cohort manifest; the checkpoint manifest
must retain the same provenance, factor hash, arm, dose, and per-writer edit statistics.

The cohort check reads metadata only. It compares the 45 reserve IDs with
`/workspace/osw_shared/confirm_tasks.json` and its frozen SHA256, checks reserve
exclusion, and verifies construction/preservation are disjoint from the six-task
development panel. It does not open task episodes, screenshots, or the test split.

The file-set check requires the checkpoint to contain exactly the source files plus
`broad_manifest.json`; every non-safetensors source file is byte-identical, including
`config.json` and `model.safetensors.index.json`. This covers tie/config preservation
without loading or changing model configuration.

## First checkpoint

The verifier ran on the pod against `/dev/shm/broad_residual_p100`, using
`/dev/shm/astra-broad/factors_residual.pt`, the canonical source revision
`8c88265a5a159bfd1492db9243733dd2e6e04a6e`, and two CPU threads. The verdict is
`PASSED`; the machine-readable result is `/workspace/astra/astra-broad/checkpoint_verify.json`.

Observed result:

- 724 tensors and 5,174,964,736 elements compared across both safetensors shards.
- 24 edited tensors, 408,944,640 edited elements.
- 354,868,124 BF16 elements changed at dose 1.0, learned arm.
- Reserve count 45; construction 4 rows; preservation 4 rows; development 6 rows.

The implementation is at
[`verify_checkpoint.py`](./verify_checkpoint.py). The source construction formula and
manifest fields it checks are in
[`build_checkpoint.py`](./build_checkpoint.py:44) and the factor provenance is written
by [`derive.py`](./derive.py:55).
