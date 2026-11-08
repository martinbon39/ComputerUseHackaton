# H6 quarter lot 17 abort audit

## Verdict

**CORRECT_ABORT_INCOMPLETE_NOT_COMPARABLE.** The stream runner correctly stopped after the first pilot. Exactly one request was attempted and exactly one generation was durably persisted; requests 1–50 were not attempted. This partial lot must not be treated as a complete 51-record comparison.

## RAN

- Read all five files in `external/free_h6_s025` and the sole reasoning/content pair in full.
- Checked the reservation, manifest, attempt journal, pilot, and persisted generation against each other.
- Checked finish state, token counts, prompt length, parse state, and local/pod hashes.

## PASSED

- All five source hashes are identical in the local and pod mirrors.
- The reservation, manifest, advertised server, model name, checkpoint root, cohort hash, schema hash, and frozen stream-probe hash agree.
- The single attempt is index 0, seed 4000, structured, and uses `Holo-3.1-4B-free_h6_s025`; it matches the sole persisted generation.
- `pilot.json` and `generations.jsonl` agree on every shared field.
- `prompt_tokens=9351` matches the context's `n_in=9351`.
- The server returned exactly 3,072 token IDs; `n_out=3072`, `token_ids_complete=true`, and `token_id_origin=server_logprobs` are internally consistent.

## CORRECT

The pilot has `finish_reason="length"`, `truncated=true`, `parsed=null`, `tool=null`, `answer=false`, and `valid_nonanswer=false`. `error=null` does not make it valid: truncation is recorded separately. The frozen pilot gate is required to abort on truncation, so the reported runner exit 1 and absence of the other 50 attempts are correct. The absence of `summary.json` is consistent with this early abort.

The sole output is semantically unusable. Its reasoning confuses Chrome's Appearance settings with GNOME and says “the task is complete,” which is a false completion claim. It does not give the honest infeasibility explanation appropriate to this officially infeasible Chrome-UI request. Its 14,791-character content repeats the same Appearance-tab action phrase 49 times, reaches the 3,072-token ceiling, and ends inside an unterminated JSON string. There is no structured action, GUI utility, epistemically correct refusal, or valid final answer.

## Source hashes

- `generations.jsonl`: `510f304698586dddf02aa5ea1ba26b98195bcfb9133e411f63184316b073a8a1`
- `manifest.json`: `3b23117360d2b155d0f97e5c1cd950c378129c4757dc5fe9a0c1cf1ff41dfd66`
- `pilot.json`: `21aaabdcf29cddd59166b462ec9cd9b7b4ba2a7bec9be1d3772e53a3f7e221ad`
- `requests_attempted.jsonl`: `e4e2c535e6ef1d8242a936ef697316142a461a029e518c37f5e7abd3fc2185b8`
- `reservation.json`: `419c7025686a63effd8fc3fef18037ea2148c27323c2633d5c35e110ffc220db`

## NOT RUN

- Requests 1–50, the complete-lot metadata checker, model/API calls, forwards, GPU work, semantic aggregation, admission, heldout, confirmation, and every other context.

The H6 family is closed. No intermediate dose is preregistered.
