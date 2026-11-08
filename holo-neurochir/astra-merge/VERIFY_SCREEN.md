# Screen wrapper verification (read-only)

Date: 2026-11-08. No inference, network call, or file mutation outside this report was performed.

## Verdict

PASS with one semantic caveat: `/tmp/astra-merge-work/screen.py` uses the frozen `astra_cohort_probe.py`, `probe_answer_rate.py`, and `cohort.json` hashes before running. Full mode invokes `astra_cohort_probe.py` with the exact cohort, results root, explicit Modal URL, resolved model ID, `ASTRA_MERGE_AUTH`, `--k 8`, and checkpoint label. The cohort contains only the six DIAG contexts already validated by `load_task/check_traj`; no production prompt or harness file is changed.

Identity mode lists `/v1/models`, requires exactly one model whose root ends with `/<checkpoint-name>`, asserts the selected model ID, and prints only model/root identity. The Modal key is read from `/home/orbit/.holo_modal_key` into an environment variable and is not placed in argv or printed. The wrapper itself sets Python thread caps and `torch.set_num_threads(2)`.

Smoke mode makes three text calls with `temperature=0`, thinking disabled, `max_tokens=256`, then one healthy structured call through `astra_cohort_probe.call` with T=.8, top-p=.9, top-k=20, reflection enabled, structured JSON schema, and max_tokens=3072. It checks transport/non-empty text and `valid_nonanswer` for the healthy row. The caveat is that `valid_nonanswer` checks schema/tool class only; semantic health still requires manual review of the returned action/screenshot context.

Full mode uses seeds 0..7 and six rows (48 structured generations plus 3 text calls = 51 rows). It writes outputs under a checkpoint-specific temporary directory; an existing directory causes a deliberate `exist_ok=False` failure, preventing accidental mixing/reruns.

## Existing original-pod artifact (independent read)

`/tmp/astra-merge-work/original_pod/generations.jsonl` contains 51 rows, matching `probe_freeze.json`: 48 structured rows and 3 text rows; 0 errors and 0 truncated. All rows identify `http://127.0.0.1:8000/v1`, model `Holo-3.1-4B`, vLLM `0.23.0`.

Structured counts are 16 fs+ (`answer` 16/16), 16 fs− (`answer` 16/16), and 16 healthy (`write` 8, `scroll` 8, `answer` 0). The three text rows all have non-empty content and `finish_reason=stop` (output lengths 49, 161, and 38 tokens). The summary records the exact settings: T=.8, top-p=.9, top-k=20, reflection/structured schema, max_tokens=3072; text T=0, thinking off, max_tokens=256.

## Blockers

No execution blocker found. Manual semantic health review remains required after any actual smoke/full run; this audit intentionally did not call inference.
