# Replay verification

Independent read-only verification of the proof-anchor preflight and four-forward pilot.

## Verdict

PASS for the checked replay invariants. `PREFLIGHT.json` contains 39 unique contexts and four variants per context. One context has a null note; its null value is retained while thought is substituted. Every context has equal total token count across variants, distinct variant input hashes, ordered residual positions, and finite tool logits in the pilot.

The four pilot forwards for `power_000` (`a`, `b`, `c`, `d`) have input hashes and total token counts matching their corresponding preflight variants.

## Checks

- Source/payload identity checks are implemented in `load_source()` and passed in the recorded preflight: source hashes, payload SHA256, historical `assistant_json()` and `tool_output()` strings, and decoded image pixel equality.
- `make_variants()` preserves contextual token lengths for note, thought, and reasoning substitutions. The earlier review concern about `length_matched()` was incorrect: its target is `measure(original)`, so condition d measures original and candidate in the same full-suffix domain.
- `prepare()` records zero-based positions for final prompt, final reasoning/delimiter token, and the token immediately before the first note value token (or `null`).
- `tool_tokens()` checks prefix identity and records first-token IDs; the reported margin is the answer first-token logit minus the maximum other-tool first-token logit.
- Capture uses `use_cache=False`, `logits_to_keep=1`, and no generation path.

## Scope and limits

This verifies replay/provenance and teacher-forced first-token scoring. It does not verify generated behavior, causal effects, or the residual tensors from the full 156-forward run.

