# Fresh CPU verification: `prefix_probe.py`

Date: 2026-11-07 UTC. Scope: final static/CPU audit of `prefix_probe.py`, `prefix_probe01.job.json`, `run_prefix_probe.sh`, immutable `experiment.py`/`generation.py`/`run_lot.sh`, frozen baseline, and offline tokenizer behavior. No model generation or GPU use.

## Verification status

- **RAN:** static control-flow review, SHA verification, full 24-record baseline/grid audit, offline tokenization of all 24 constructed prefixes, and CPU config inspection.
- **PASSED:** final callback/job binding; immutable helper identities; baseline hash/grid/counts/sampling/seeds; schema path; exact textual prefix construction; no terminator in injected IDs; all-original-tensor immutability checks; cache-config assertions; screen-only loop; diagnostic labels; weight non-modification; incomplete-panel failure propagation; lock/budget/guard/memory inheritance.
- **CORRECT:** the final code implements a bounded **input-modified capacity diagnostic**. A favorable result would show behavior under an injected instruction and must not be reported as weight-edit success.
- **NOT RUN:** the actual `prefix_probe01` GPU diagnostic. At final audit time there is no `prefix_probe01.jsonl`, incomplete marker, status file, output directory, or budget entry.

No blocking defect remains in the reviewed code.

## Remaining evidence limits

1. **Cache activation is still implicit at the model call.** The callback now fails unless both `holo.model.config.text_config.use_cache` and `holo.model.generation_config.use_cache` are exactly `True`, and records both flags. The immutable `generation.generate` helper does not pass `use_cache=True` explicitly or record incremental forward shapes. Under Transformers generation semantics these true configs select cache use, matching the frozen baseline, but the result will not independently attest `[prefill, 1, 1, ...]` forward lengths as the separate fidelity diagnostic does.
2. **Original generated token IDs are unavailable.** The frozen baseline stores decoded text rather than sampled token IDs. The probe therefore re-tokenizes the exact decoded pre-`</think>` reasoning. It now asserts exact tokenizer text round-trip and records `prefix_replay="exact_text_retokenized; baseline_generated_ids_unavailable"`. This proves exact text-prefix injection, not token-for-token replay of the original generation.

These limits are accurately labeled in every prospective record and do not create weight-efficacy evidence.

## Final identities and helper immutability

- `prefix_probe.py` SHA-256: `bf7a0c9465bd012479ff78d641a1e425c4a69ed7d194463982e3bba1f9022bde`;
- job `implementation_sha256`: same value;
- `prefix_probe01.job.json` SHA-256: `d48f42d89fb16bfc1be64fc26883443a545ff2ce91e76280a8aabbceff882fd2`;
- `experiment.py` SHA-256: `b02d7b4899f8c4e89fbbae5668b8cf246f16d30c919bde50598889f2a0b65fe7`;
- `generation.py` SHA-256: `56febaa3719dfbe6b380b6c0adb25b8ea351b9c0bcbf0968feec52458fd435c0`;
- `baseline_screen.jsonl` SHA-256: `0709b9fefbd4d8a0eef2936029c1c96be3b47cd960458b9d07069e905b823e87`.

The baseline SHA matches `baseline_frozen.json` and the job. The callback now asserts the immutable experiment SHA directly at line 185. Neither `experiment.py` nor `generation.py` changed while the audit gaps were closed.

## Baseline and grid

`load_reference` requires exactly 24 unique records covering every `(row_index 0..5, sample 0..3)` pair. It checks each baseline row against `manifest["screen"][row_index]`, seed `4000+sample`, frozen sampling, valid nontruncated text, and exact frozen counts:

| Label | n | Answers | Valid nonanswers |
|---|---:|---:|---:|
| fs+ | 8 | 8 | 0 |
| fs- | 8 | 8 | 0 |
| healthy | 8 | 0 | 8 |

Frozen sampling is temperature 0.8, top-p 0.9, top-k 20, `max_new_tokens=3072`, with sampling enabled. Derived bounds are max 4 fs+ answers, min 8 fs- answers, min 8 healthy valid nonanswers, and max 2 invalid/truncated outputs. The early-stop arithmetic treats unobserved protected outputs optimistically and stops only after a requirement becomes mathematically unreachable.

## Prefix boundary and IDs

For each baseline record, the appended text is exactly:

`baseline_text_before_first_</think> + "\n" + frozen_phrase + "\n"`.

It is encoded with `add_special_tokens=False` and appended to the unchanged original prompt. The callback asserts:

- the reasoning text contains no `</think>`;
- the encoded prefix is nonempty and contains no `</think>` token ID;
- decoding `prefix_ids` with special tokens preserved exactly reproduces `prefix_text`;
- `new_n_in == old_n_in + len(prefix_ids)`.

Independent offline tokenization of all 24 records found token ID 248069 for `</think>`, prefix lengths 62–265 IDs (4,030 total), 24/24 exact decode round-trips, zero terminator IDs, and 24 distinct prefix-text hashes.

The generated continuation begins at `new_n_in`; the injected prefix does not close reasoning. `ThinkingGrammar` remains in reasoning mode until the new continuation emits `</think>`, then applies the original JSON schema. Each record contains exact prefix IDs, old/new boundaries, replay caveat, prefix/reasoning/baseline/row hashes, source hashes, and cache flags.

## Sampling, schema, seeds, and output labels

The probe compiles each screen row’s unchanged system JSON schema using the same xgrammar path as the immutable runner. It calls the same `generation.generate` helper with the frozen sampling dictionary and seed `4000+sample`. That helper strictly validates post-`</think>` JSON as a `Step` and reports `tool`, `answer`, `valid_nonanswer`, `error`, `n_out`, and `truncated` under the same EOS handling as baseline.

The job’s `max_new_tokens=3072` is asserted, and exact sampling equality makes it effective. The callback also requires both text and generation cache configs to be true before any output.

## Input and weight isolation

For each screen row, `exp.inputs_for` reconstructs the original prompt once. The final callback computes SHA-256 for every tensor in the original input dictionary before any sample. After each generation it recomputes the complete tensor-digest mapping and requires exact equality. It separately retains the original `input_ids` clone and asserts equality before and after generation. `exp.extend` creates a new dictionary and new token-aligned tensors, so samples are not cumulatively prefixed.

The callback never calls `apply_spec`, accesses model parameters, registers a weight-edit hook, or loads a delta. Job, output, and marker fields state `input_modified=true`, `weights_modified=false`, and `diagnostic_only=true`, with an explicit capacity-only interpretation.

The loop uses only `manifest["screen"]`. `experiment.main` reads heldout task IDs solely for universal disjointness assertions; no heldout example path or content is opened or generated.

## Locks, budget, memory, and termination

`run_prefix_probe.sh` uses `launch.lock`, then shared `gpu_slot.sh`. `experiment.main` additionally acquires nonblocking `own_gpu.lock`, checks STOP/deadline, enforces the 40-lot cap, appends exactly one attested lot, limits allocator use to 13 GB, monitors process GPU memory, and guards every model forward. The callback calls `exp.guard()` before each generation and frees cached allocations after every durable JSONL append.

A complete panel is exactly 24 records and a successful outer lot status. If a frozen bound becomes unreachable, the callback durably writes `.incomplete.json` with `panel_complete=false`, counts, bounds, reason, and diagnostic labels, then raises `RuntimeError`. `experiment.main` consequently records the lot outcome as failed. The prior ambiguity between an incomplete panel and generic `outcome="complete"` is resolved.

This audit establishes final code/provenance correctness for a diagnostic. Behavioral usefulness is **NOT RUN** and cannot support any claim about edited weights.

## Addendum — 2026-11-08 cache assertion correction

The execution-readiness verdict above is superseded in one material respect. Lot 11 loaded the model but failed before any forward because `model.generation_config.use_cache` is `None`, while the original callback asserts identity with `True`. The snapshot omits this field; Transformers resolves it to the global runtime default `True` only inside `generate()`. Thus the original `prefix_probe01` is not runnable as audited, and the prior statements “no blocking defect remains” and “CORRECT” do not apply to that file's execution readiness. All non-cache static checks remain valid.

The original report before this addendum had SHA-256 `d7c5da49b7017278b9e2a9109046771b31793612fcaa90f193598211cec3b065`. Root cause, installed-source evidence, and the independently reviewed fail-closed replacement are in `CACHE_CONFIG_FAILURE_AUDIT.md` (initial SHA-256 `44317c1ab665b8e44c4d33007b357486b10f993cbb6619cd15286a48dbef79b7`). Replacement real-model cache evidence remains **NOT RUN**.
