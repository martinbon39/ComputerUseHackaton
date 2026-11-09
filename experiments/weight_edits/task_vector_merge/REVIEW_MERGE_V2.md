# Independent review: scoped merge v2

**Verdict: READY; no blocking defect found in the v1→v2 scope change.**

Reviewed `/tmp/astra-merge-work/merge_v2.py`, SHA-256 `26ac7cef74c822a0a1f72e84042b8df4ef01d923c29f84677b1789906165824b`, against frozen v1.

The diff is limited to:

- adding `--layer-range START STOP`;
- validating a nonempty half-open range within `num_hidden_layers`;
- selecting only keys under `model.language_model.layers.<n>.` whose parsed layer number lies in that range;
- recording `layer_range` and scoped-language wording in the manifest.

For `[12,24)`, layers 12 through 23 are selected. Embeddings, final norm, unselected language layers, vision, and `lm_head.weight` take the unchanged-Holo branch. Existing arithmetic/TIES/DARE formulas and serialization paths are unchanged. Parsing index `k.split(".")[3]` is correct for the gated prefix `model.language_model.layers.`. The CLI boundary check rejects empty, negative, reversed, and out-of-model ranges.

## Independent verifier v2

Installed `/workspace/astra/astra-merge/verify_candidate_v2.py`, SHA-256 `cf2784fbda577d13bb9b87c66c5c7a1407447c5a4909aad2050f5db5226f103e`.

It independently:

- requires a two-integer manifest `layer_range` and revalidates it against Holo's layer count;
- parses layer numbers from checkpoint keys and requires the observed selected layer set to equal every layer in the half-open interval;
- recomputes the declared formula only for selected keys;
- requires every other key, including all unselected language tensors, embeddings, final norm, vision, and head, to be bitwise Holo;
- reports dynamic `selected_formula_verified` and `preserved_policy_verified` counts rather than the full-language 426/298 constants;
- retains exhaustive index/shard, shape/dtype/finiteness, hash, auxiliary-file, config, and processor checks.

Frozen v1 checker remains unchanged at `/workspace/astra/astra-merge/verify_candidate.py`, SHA-256 `115e24029fc1302a1d823e70d1e64ce32571f3317550827f1ca98f06c349d4cd`.

Only syntax compilation and source-hash checks were run. No checkpoint, build, model allocation, or GPU operation was performed.
