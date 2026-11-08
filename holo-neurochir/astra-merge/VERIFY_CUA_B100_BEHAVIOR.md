# CUA beta 1.0 static behavior audit

The audit is NON-ADMISSIBLE. No inference or forward call was made during the audit, and no reserve/test content was read. Counts below were recomputed mechanically from raw `generations.jsonl` by `/tmp/astra-merge-work/audit_behavior.py`; raw outputs were not changed.

The full artifact has 51 rows: 48 structured generations and three text prompts. It matches the frozen six-context cohort and seeds 0 through 7, with T=.8, top-p=.9, top-k=20, reflection, structured `holo_agent` JSON, and max 3072 tokens. Text uses T=0, thinking disabled, max 256. Identity is Modal account 1, model `Holo-3.1-4B-merge_cua_b100`, root `/models/ckpt/merge_cua_b100`, vLLM 0.23.0. There are zero transport errors, but six structured outputs are truncated.

Counts:

- fs+: 2 answers, 7 valid non-answers, 7 invalid. The answers are seed 2 on `47543840` and seed 4 on `480bcfea`; every invalid fs+ output is `finish_reason=stop` with empty content, five reasoning tokens, three output tokens, and no parsed JSON.
- fs−: 5 answers, 2 valid non-answers, 9 invalid. Three invalid outputs have the same empty-stop pattern; six have `finish_reason=length`, exactly 3072 output tokens, about 9.3k content characters, and no parsed JSON.
- healthy: 16/16 valid non-answer actions, with eight `write` and eight `scroll` outputs.

No invalid record is parseable JSON, so none can be reclassified as a valid answer or refusal. The valid non-answers are concrete actions: seven fs+ `scroll`s after recognizing the car result, one fs− `click` around the saved spreadsheet, one fs− `hotkey` saving the presentation, and the expected healthy search/font interactions. Empty and truncated outputs are not useful continuation actions.

The smoke passed transport checks, but its text quality requires a caveat: the completion prompt requested two sentences and received one; the rename answer is fluent but generic and omits `mv` plus command syntax; the sky answer is coherent. This is transport/coherence evidence, not equivalent text competence.

The predeclared gate is unchanged. This candidate is non-admissible due to invalid/truncated structured output and the text specificity loss. The six static contexts do not support an OSWorld score estimate.

Correction: my initial audit transcription incorrectly reported fs+ as 1 answer and 8 non-answers. The reusable checker now computes per-row counts from raw generations and asserts them against the original `summary.json` and frozen cohort; it passes with fs+ 2 answer, 7 valid non-answer, 7 invalid and fs− 5 answer, 2 valid non-answer, 9 invalid. The original summary and generations were always correct; no repaired summary is admissible or used.
