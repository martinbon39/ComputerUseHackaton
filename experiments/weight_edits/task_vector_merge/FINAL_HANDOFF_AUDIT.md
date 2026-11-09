# Final handoff audit

Result: PASS

This was an artifact-only audit. Model weights, reserve content, and inference processes were not touched. No source artifacts were changed.

- `CHECKPOINTS.json` contains exactly 9 entries.
- All 9 entries have `weight_verification: PASS`; each checkpoint name, beta, half-open scope, and recorded file hashes match its corresponding `*_build.json`.
- Static statuses are exactly: 3 `HEALTHY`, 1 `REJECTED`, 3 `NOT_RUN_SCOPE_AMENDMENT`, and 2 `QUEUED`.
- The three healthy entries (`merge_cua_b025`, `merge_cua_b050`, `merge_fara_b050`) each have an independent behavior-audit JSON with a passing static audit.
- `merge_cua_b100` is not claimed as a gain: the frozen static results show 16 invalid GUI outputs, including 6 truncated outputs. Its rejection is preserved.
- Both scoped middle-block audits confirm 159 selected/formula-verified tensors and 565 preserved outside-scope tensors.
- `REPORT.md` explicitly says no OSWorld gain is established and distinguishes queued runtime screens from measured health; it does not claim runtime health for queued candidates.
- The v1/v2 split is frozen, and the scope amendment is explicit: the original full-language grid is closed; only the two CUA layer-12–23 candidates are scoped/queued. No TIES/DARE completion is implied.
- The final tokenizer audit reports all four source mappings aligned in both directions with zero conflicts: `fara_tokenizer_alignment_final.json`.

The owned `/tmp/astra-merge-work` scan found only generic credential-related words (`token`, `credential`, `password`, `bearer`, or key terminology) in these filenames; these are documentation or code terms, not credential values:

`README.md`, `REPORT.md`, `VERIFY_SCREEN.md`, `VERIFY_UPLOAD.md`, `literature.json`, `screen.py`, `tokenizer_alignment.json`.

Strict scans over all owned text found zero email addresses, AWS-style access IDs, `hf_` tokens, private-key headers, or bearer credential values. No unresolved secret flag remains.
