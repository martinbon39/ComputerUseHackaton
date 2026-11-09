# Independent artifact verification: Fara beta 0.50

**Artifact verdict: PASS. Evidence-publication status: blocked by `/workspace` quota.**

The unchanged reusable checker completed every substantive assertion before failing on its final JSON write:

- All 724 indexed and serialized tensors match the Holo key/shard layout, shape, and dtype and are finite.
- All 426 language tensors exactly match independently recomputed `Holo + 0.5 * (Fara - Qwen)` after target-dtype conversion.
- All 298 vision/head/policy-preserved tensors are bitwise tensor-equal to Holo.
- The manifest reports 381 physically changed and 343 retained tensors; its sets exactly matched independently observed physical equality during the completed assertion pass.
- Both shards, manifest sizes/hashes, all 11 Holo auxiliary files, and local-only config/processor loading passed.
- Full model allocation was **NOT RUN**.

The final write to `/workspace/astra/astra-merge/VERIFY_FARA_B050.json.tmp` failed with `OSError: [Errno 122] Disk quota exceeded`. The volume reports 814 TB free, so this is a user/directory quota rather than filesystem capacity. The zero-byte temporary file remains. No checkpoint/runtime concern was found; only durable evidence publication is affected.

Checker: `/workspace/astra/astra-merge/verify_candidate.py`, SHA-256 `115e24029fc1302a1d823e70d1e64ce32571f3317550827f1ca98f06c349d4cd`.
