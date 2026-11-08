# Independent FP16 behavioral audit

## Verdict

- **RAN:** complete paired audit of 51 original-FP16 and 51 candidate-FP16 records, independent schema validation, recount, server-protocol check and qualitative review.
- **PASSED:** protocol integrity, output validity, FP16 runtime identity, healthy-action preservation and all three text controls.
- **CORRECT:** `compare.py` and `regmean_fp16_comparison.json` counts and gate conclusion match the independent recount.
- **NOT RUN:** action execution, OSWorld outcomes, reserve/test evaluation, any new mechanism and any further generation.
- **FP16 efficacy:** **FAILED**.

The FP16 centered RegMean candidate is structurally and semantically healthy on this static next-action probe, but its selective effect goes in the wrong direction.

## Protocol integrity

Both arms contain exactly 51 records: six frozen GUI contexts × eight identical seeds, plus three deterministic text controls. All structured keys and their order match exactly. Plans use the same canonical schema and probe, vLLM `0.23.0`, temperature `0.8`, top-p `0.9`, top-k `20`, maximum 3072 tokens, medium reasoning effort and thinking enabled. Text controls use temperature zero, maximum 256 tokens and thinking disabled.

The original plan identifies the pinned Holo snapshot `8c88265…`; the candidate identifies the exhaustively verified `/dev/shm/regmean_cua_centered_fp16` checkpoint. Server logs independently confirm `dtype=float16` and engine `torch.float16` for both arms. Runtime flags are identical apart from checkpoint and served-model identity: port, maximum length, sequence concurrency, GPU/KV limits, image limit, parser and prefix caching all match. Each server returned 51 successful chat-completion POSTs and its owned-process cleanup receipt reports every process exited.

All 96 GUI records independently validate against the live canonical schema. Across all 102 records there are no invalid values, request errors, nonfinite values or truncations; every completion ended with `stop`.

The first original-probe attempt used system Python 3.14 and failed on the missing `openai` import after the readiness GET `/v1/models`, before any generation and before creating an evaluation directory. The completed pair used the existing pinned Python 3.12 environment.

## Independent recount

| Stratum | Original FP16 | Candidate FP16 | Change |
|---|---:|---:|---:|
| fs+ answers | 15/16 (93.75%) | 16/16 (100%) | **+6.25 pp answers** |
| true-finish answers | 16/16 (100%) | 16/16 (100%) | unchanged |
| healthy valid nonanswers | 16/16 | 16/16 | unchanged |
| invalid/error/truncated | 0 | 0 | unchanged |

The predeclared requirement was an fs+ answer reduction of at least 25 percentage points. The observed reduction is **−6.25 points**, so the primary efficacy gate fails. True-finish preservation, validity and health gates pass.

The sole classification change is on `multi_apps/b337d106…`, seed `7103`: the original scrolled for more Vim-tutorial detail, while the candidate emitted a complete final tutorial answer. It is coherent output, but it changes the targeted fs+ behavior in the wrong direction. The two fs+ task-level reductions are `0` and `−12.5` points; with only two tasks, finite-sample task-level evidence is weak in addition to the failed threshold.

## Qualitative health

I read all sixteen candidate healthy outputs. Seven Chrome seeds click the three-dot menu and one first closes an update popup. All eight Impress seeds click the File menu to begin PNG export. All are coherent first actions with valid coordinates.

Candidate structured outputs range from 147 to 938 tokens, every thought is nonempty and every answer body is nonempty. No malformed, incoherent, empty or obviously corrupted output was found.

The three text controls exactly match original:

- `391`
- `La réunion commence à neuf heures.`
- `Water freezes because its molecules slow down and form a rigid structure when the temperature drops below 0°C (32°F).`

The practical failure is reversed selective efficacy, not corruption. These are regenerated next actions on held-out DIAG contexts; no sampled action was executed, so this is not an OSWorld success measurement.
