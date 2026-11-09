# Fresh CPU verification: early prefix capacity probe

Date: 2026-11-07 UTC. Scope: static/CPU audit of `prefix_probe_early.py`, `prefix_probe_early01.job.json`, and `run_prefix_probe_early.sh` against the already-audited late probe and immutable `experiment.py`, `generation.py`, baseline, and screen grid. No model generation or GPU use.

## Verification status

- **RAN:** full code/job/launcher diff; SHA and callback binding checks; Python and shell syntax checks; baseline hash/grid/count/sampling/seed recomputation; offline tokenizer test of the exact phrase; guards, labels, input isolation, and early-stop review.
- **PASSED:** intended early-placement change, exact phrase-only injection, tokenizer round-trip, screen grid and seeds, schema/sampling path, original-input hashes, absence of weight edits, capacity-only labels, lock/budget/deadline/memory inheritance, and hard failure for an incomplete panel.
- **CORRECT:** the reviewed files implement a bounded, input-modified capacity diagnostic at the start of thinking. A favorable result could show capacity under a generic instruction, but is not evidence of weight-edit efficacy.
- **NOT RUN:** `prefix_probe_early01`; there is no JSONL, incomplete marker, or budget entry for this job at audit time.

No blocking code defect was found.

## Exact change and placement

The complete diff against the final late probe changes only names/interpretation, adds the asserted `placement="thinking_start"`, and replaces:

`baseline reasoning + "\n" + PHRASE + "\n"`

with exactly:

`PHRASE + "\n"`.

The original screen input is reconstructed with `enable_thinking=True`, so appending those IDs continues the already-open thinking stream. The injected string does not replay baseline reasoning and does not close `</think>`. The baseline reasoning is read only to validate the matched frozen record and record its SHA-256 with role `matched_reference_only_not_replayed`; it is never included in `extra`.

Independent offline tokenization found 31 IDs:

`[13784, 13, 353, 1189, 599, 34811, 449, 16693, 1852, 364, 2316, 13, 6558, 728, 9150, 1754, 10897, 7472, 440, 279, 9155, 5721, 13, 3437, 15808, 369, 1990, 632, 3923, 30, 198]`.

Decoding with special tokens preserved exactly reproduces the phrase plus newline. The `</think>` ID is 248069 and is absent. Runtime assertions repeat all three facts and require `new_n_in == old_n_in + len(prefix_ids)` before generation.

## Grid, sampling, and output semantics

The frozen baseline SHA-256 is `0709b9fefbd4d8a0eef2936029c1c96be3b47cd960458b9d07069e905b823e87`, matching the job and `baseline_frozen.json`. Recalculation found exactly 24 unique `(row_index, sample)` cells over six screen rows and four samples. Every stored row equals its current frozen screen row, every seed is `4000 + sample`, and every sampling dictionary equals the frozen sampling configuration. Counts remain:

| Label | n | Answers | Valid nonanswers |
|---|---:|---:|---:|
| fs+ | 8 | 8 | 0 |
| fs- | 8 | 8 | 0 |
| healthy | 8 | 0 | 8 |

The callback compiles each unchanged row schema and calls the immutable generation helper with the same production sampling and seeds. The job and callback both bind `max_new_tokens=3072`. Output parsing and labels remain those of `generation.generate`: strict `Step` JSON after `</think>`, then `tool`, `answer`, `valid_nonanswer`, `error`, and `truncated`.

The early-stop bounds are unchanged: at most 4 fs+ answers, at least 8 fs- answers, at least 8 healthy valid nonanswers, and at most 2 invalid/truncated outputs. A mathematically unreachable bound durably writes `.incomplete.json` and then raises, causing the outer lot status to be failed rather than complete. A valid complete result requires all 24 cells.

## Isolation and guards

For every screen row, the callback clones original `input_ids` and hashes every tensor before any sample. It verifies the clone before generation and all tensor hashes afterward. `exp.extend` returns a distinct dictionary with appended token-aligned tensors, so prefixes do not accumulate across samples. No code path calls `apply_spec`, touches model weights, or loads a delta. Prospective records say `input_modified=true`, `weights_modified=false`, `diagnostic_only=true`, and `prefix_source="generic_phrase_only; no_baseline_reasoning_replay"`.

The callback loops only over `manifest["screen"]`. The immutable outer runner reads heldout task IDs solely for split-disjointness assertions; this probe opens no heldout example path or content. The launcher inherits `launch.lock` and shared `gpu_slot.sh`; the runner additionally uses `own_gpu.lock`, STOP/deadline guards, the 40-lot budget, 13 GB allocator limit, GPU-process monitoring, forward guards, and durable per-record writes.

## Evidence limits

Cache use is still implicit in the immutable generation call. The probe asserts and records that both text config and generation config have `use_cache=True`, so ordinary Transformers generation selects incremental cache use, but this probe does not independently record forward shapes `[prefill, 1, 1, ...]`. This is the same accurately bounded limitation as the late probe.

The baseline remains a matched reference used for hashes, grid, counts, and thresholds. Since no baseline reasoning is replayed, the late probe's decoded-text versus original-token-ID caveat does not affect the injected phrase. It also means the early diagnostic asks a different causal question: whether the generic instruction at thinking entry changes behavior, not whether an intervention at the original pre-conclusion state does.

## Identities

- `prefix_probe_early.py`: `48549746fbca9845818a2c10e8e69a9b08417fc75bfa44b8fb47e2dadba63a56` (exactly matches job `implementation_sha256`)
- `prefix_probe_early01.job.json`: `8cad2526f5a3c47575ed6b1ef2722d91d2519655f5ed1305a60d941594399828`
- `run_prefix_probe_early.sh`: `6bf2dffd91535bcfa38186ed6d830c6d55925d98b639683f6a38c645a148aae0`
- immutable `experiment.py`: `b02d7b4899f8c4e89fbbae5668b8cf246f16d30c919bde50598889f2a0b65fe7`
- immutable `generation.py`: `56febaa3719dfbe6b380b6c0adb25b8ea351b9c0bcbf0968feec52458fd435c0`

The diagnostic is correctly prepared and unrun. It should remain described as the second and last capacity probe, run only under the stated contingency, and never enter the weight-candidate success count.

## Addendum — 2026-11-08 cache assertion correction

The execution-readiness verdict above is superseded in one material respect. The early callback repeats the same invalid assertion as the late callback: `model.generation_config.use_cache is True`. Lot 11 established on the same loaded snapshot that this raw field is `None`; Transformers resolves the effective value later inside `generate()`. Therefore `prefix_probe_early01` would fail before generation if launched, and the prior statements “no blocking code defect” and “CORRECT” do not apply to that file's execution readiness. All non-cache static checks remain valid, and this early diagnostic itself was never run.

The original report before this addendum had SHA-256 `7eb2a70ac8e638ea35903c0c013c5dd7a1e1eabf095f6a9167438ee3104497b5`. Root cause, installed-source evidence, and the independently reviewed fail-closed replacement are in `CACHE_CONFIG_FAILURE_AUDIT.md` (initial SHA-256 `44317c1ab665b8e44c4d33007b357486b10f993cbb6619cd15286a48dbef79b7`). Replacement real-model cache evidence remains **NOT RUN**.
