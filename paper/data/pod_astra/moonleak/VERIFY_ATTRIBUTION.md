# Independent verification — moon-leak attribution

Reviewed 2026-11-08 UTC, read-only with respect to the remote experiment. The reviewer did not launch GPU work or modify the remote run.

## Verdict

**RAN:** fresh-context static review of `attribution.py` and `PROTOCOL.md`; inspection of the installed Transformers 5.22.2 Qwen3.5 attention, GQA, cache, and DeltaNet implementations; read-only audit of the completed two-context pilot.

Reviewed source hashes:

- `attribution.py`: `69844786ac4effbbb85e9faae2f73e18e5b410c32ee39cbf316afb196429ebb2`
- `PROTOCOL.md`: `bd1e7e9db01cc6f72bf764072ae586a575d3e67b6deac0320cadbfad0fe08337`
- `attribution_pilot.jsonl`: `05850d61e930e5feba186bc18eaf54e5b31624ee52cf869542edaa0927db9279`
- `recorded_steps.json`: `93b32dbd65a93a671b423464fa788783b2f0f9d3c440b00c68a7d7126d430d57`

**PASSED:** the corrected pilot completed 332 model forwards and emitted complete records for one `fs+` and one `fs-` context. Each context has exactly 1 baseline, 8 matched mask controls, 128 head interventions, 1 neutral-prefix result, 24 DeltaNet patches, and 1 completion record. Repeated cached legal-tool vectors and final normalized hidden states were bitwise identical in both contexts (`hidden_max_abs_diff=0`). All 16 zero-mask controls reproduced their cached baseline exactly. Parameter-version invariance passed at process exit, so no model weight was mutated.

Cached versus full replay legal-tool margin errors were 0.01035 and 0.02805 logits, below the fixed 0.75 assertion. The maximum difference over the complete BF16-rounded vocabulary logit vector was 0.5 in both contexts and is retained in the records.

**CORRECT for the stated diagnostic:**

- The scored query is the final serialized-prefix token immediately before the tool-name value. The score is `answer` first-token logit minus the maximum of the nine GUI-tool first-token logits.
- At every one-token full-attention decode, 4 KV heads are repeated in Qwen GQA order to 16 query heads. QK scores and softmax are computed in FP32. A selected query head receives `-inf` only at absolute token positions overlapping serialized `note`/`thought` values, then attention is renormalized. Prefill remains on the original SDPA path.
- The explicit one-token attention path is shared by baseline, zero-mask control, and intervention. This removes the earlier GQA/backend confound; exact zero-mask equality in the pilot verifies the no-op control.
- Cached decode omits the full attention mask only after asserting a single unpadded context. With one current query and a cache containing only past tokens, attending over all cached keys plus the current key is causally correct.
- Multimodal RoPE deltas are saved after original prefill, restored before branches, and asserted equal after the same-length neutral prefill.
- DeltaNet has no per-token KV memory to mask. The implementation instead patches one `linear_attn` module output at the final query with the corresponding output from a same-length neutralized-prefix branch. Cache copies isolate the in-place convolution and recurrent-state updates.

No blocking correctness issue remains for the 39-context attribution run, provided the existing exact repeatability, zero-mask equality, cache immutability, RoPE equality, forward-cap, and parameter-version assertions remain enabled.

## Provenance and resume amendment

The first full run completed five contexts and stopped while preparing the sixth because some frozen rows have no `original_pod_path` on the GPU pod. It stopped before that context's first model forward and left no partial context records.

The repaired input path uses one immutable `recorded_steps.json` bundle instead of probing alternate filesystem paths. Independent verification found:

- The bundle has exactly the 39 frozen finish-context IDs: 19 `fs+` and 20 `fs-`, with no missing or extra entry.
- For every entry, `task_id`, zero-based `t`, and `traj_sha256` equal the corresponding frozen row.
- Each source `row.task_dir/traj.jsonl` was independently hashed and matched both the frozen `source_hashes["traj.jsonl"]` and bundled digest. The bundled step is exactly the parsed source trajectory element at index `t`; `step_num == t + 1`; both `tool_name` fields are `answer`.
- Runtime code pins the complete bundle hash before loading the model, then rechecks the per-row task ID, step index, and trajectory digest before building the recorded suffix. The frozen payload remains separately content-hash checked.
- The retained full-run file has 815 records covering exactly five complete contexts and no partial context. Each has the expected 1 baseline, 8 mask controls, 128 heads, 1 neutral result, 24 DeltaNet patches, and 1 completion record. Completion counters are 165, 330, 495, 660, and 825.
- A non-pilot context executes exactly 165 guarded forwards. Restoring `COUNT = 165 * len(done)` therefore resumes at 825 and preserves the original 6500-forward cap; completing the remaining 34 contexts ends at 6435.

**PASSED:** the provenance repair preserves the exact recorded step content and experiment accounting while removing the unavailable-path dependency. It does not change model inputs for the five retained contexts or any attribution intervention.

## Known limits

- This is teacher-forced attribution at the tool-name token. It is not a generated action rate, calibrated probability, verified task outcome, or proof that an `o_proj` edit will be selective.
- The power cohort is used for attribution and selection. It is not independent confirmation.
- Legal-tool logits are deterministic FP32 reprojections of the model's BF16 final normalized hidden state and existing BF16 LM-head rows. They intentionally differ from the BF16-rounded logits in earlier broad logs.
- Full replay and cached replay are close on the legal-tool margin but not bitwise equivalent over the vocabulary. Head effects are compared within the exact repeated cached path, not against full replay.
- Neutralization preserves token count and JSON validity by replacing strictly interior value tokens with space tokens. Tokens crossing each value boundary are retained; the pilot excluded two such boundary tokens per context, which can preserve first or last lexical material.
- The head mask removes links to serialized `note`/`thought` value tokens only. It does not remove recorded reasoning, JSON field delimiters, or information already carried in the final query/residual stream.
- A DeltaNet output patch replaces the entire module output at one layer and final position. It is an activation-patching diagnostic, not an exact deletion of note/thought contributions from the recurrent state.
- The corrected deterministic repeatability check covers the two pilot contexts. The full run should be rejected if any retained invariant fails or any context is partial.
- Scaling selected `o_proj` columns changes those heads at every generated position and for every source token. The attribution intervention is narrower, so generation and preservation screening remain necessary.
- The earlier broad anchoring swap showed large changes only on two construction false-success contexts. It did not test true-finish or healthy selectivity, and donor-prefix length changed the final position. It cannot serve as evidence that prefix effects are selective.
