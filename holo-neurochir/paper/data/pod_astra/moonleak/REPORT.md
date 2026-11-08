# moon-leak — note/thought → tool-choice channel

Status: attribution complete; first weights-only candidate under generation screening. No candidate admitted and no online gain claimed.

## Question and scope
Can a weights-only reduction of attention heads that read the model's own note/thought reduce false completion more than genuine completion? The source model is Hcompany/Holo-3.1-4B, exact revision8c88265a5a159bfd1492db9243733dd2e6e04a6e. No gradient, LoRA, runtime hook, changed prompt, or changed harness is part of any candidate; hooks are used only for diagnosis.

The inspiration [Who Verifies the Agent's Success Claim?](https://arxiv.org/abs/2610.29609) tests self-report leakage in downstream completion judges. Moving that idea into the agent's own tool-choice circuit is an unproven extension. Broad's donor-JSON swap changed answer margins by −15.75/−21.5 logits on2 false-finish contexts, but had no matched true-finish intervention and changed prefix lengths by+15/−25 tokens. It motivates the test; it does not establish selective circuitry.

## Frozen data and baseline
The astra-power cohort manifest SHA256 is2faee8f1af5a1243b8c8bacbf0369e4e035ab9dc336307c9f6678c0d134c24d0. Its55 task-disjoint contexts comprise19 feasible false finishes (score0),20 true finishes (score1),16 healthy actions. All have strict evaluator feasibility. Heads are selected on this cohort, so its screening is exploratory, not independent validation. Neither the45 reserve nor split_test has been opened by moon-leak.

Frozen messages come directly from power payloads with SHA checks. Recorded suffixes were extracted from39 local trajectories after each whole traj hash matched the frozen source_hashes. The extracted bundle SHA256 is93b32dbd65a93a671b423464fa788783b2f0f9d3c440b00c68a7d7126d430d57. Independent review verified exact step equality for all39 rows. No screenshots were regenerated.

Original A is the completed astra-power run, exact55×4 paired rows/seeds17000–17003, ended07:11:06UTC, vLLM0.23.0. It has220/220 valid JSON and zero errors/truncations.

| Stratum | A metric | Count | Rate |
|---|---|---:|---:|
| Feasible false finish | answer |55/76|72.37%|
| True finish | answer |75/80|93.75%|
| Healthy action | valid nonanswer |59/64|92.19%|

## Attribution design and validity
For every head in full-attention layers3,7,11,15,19,23,27,31 (zero-based;16 heads each), ablate the final query's links to tokens overlapping JSON note/thought values and renormalize attention over other keys. The task, screens, external reasoning, and other heads remain fixed. Measure answer minus maximum other legal-tool first-token logit. This teacher-forced margin is a diagnostic, never the admission outcome.

Cache copies isolate all mutable KV, DeltaNet recurrent and convolution states. Pilot verified exact repeated hidden states and tool-logit vectors. Numerical confounds found before selection were fixed: correct cached multimodal positions, deterministic explicit final-token attention for all8 attention layers, and matched zero-mask controls. Prefill remains SDPA. Legal-tool logits are FP32 projections of BF16 final hidden states and existing BF16 lm_head rows; they differ from BF16-rounded broad logs. Full-versus-cache margin error is recorded per context; all must stay≤0.75. All zero-mask controls must be exact zero. Model parameter versions must remain unchanged.

Each of24 DeltaNet layers is also patched at its final mixer output with the corresponding output from the same-length context whose strictly interior JSON note/thought value tokens are replaced by spaces. Boundary-crossing tokens remain; neutralization is not complete lexical erasure. This removes both note and thought, while preserving external reasoning and positions. Layer-output replacement tests a carrier of the counterfactual change, not a clean attribution to that layer's recurrent mechanism.

Engineering failures and pilots are preserved but excluded from ranking. Five contexts completed before one missing original_pod_path stopped the first full process; the canonical recorded-step bundle fixes provenance for all39, and resumption skips only complete contexts. Full attribution budget6435 forward calls, hard process total6500; inclusive fidelity-debugging cap8500. All runs use fleet slots and2 CPU threads.

## Candidate and screening protocol
Two families of4 heads are frozen. Selective rank (mean false-finish margin drop minus mean true-finish drop): L11h2,L7h4,L3h3,L15h4. Literal raw-channel rank (largest mean false-finish margin drop): L7h13,L11h2,L7h8,L15h5. For both, scale o_proj columns256h:256(h+1) by0.5 or0. The raw family replaces the original optional2/6-head sweep following independent review, before any candidate generations were inspected; the candidate cap decreases from6 to4. The original unused2/6 specs are retained for audit. The selection rule and its amendment are exploratory. Random controls match each family's head counts per layer, seed261029609; use the best numerically passing dose, or zero if neither passes, at most one control dose per family. No further search after these4 candidates.

A head-column edit suppresses all uses of that head at every position; it cannot selectively remove only note/thought edges. Therefore causal diagnosis does not imply a selective weight edit. Wv/Wk variants are optional and not in the primary sweep; GQA shares each KV head across4 query heads, and normalization complicates K scaling.

Every tested checkpoint gets a full independent CPU tensor audit before serving: exact declared formula, all other columns/tensors bitwise identical, identical tokenizer/config/index metadata, complete HF shards. GPU serving is only own port8030, vLLM0.23.0, memory fraction0.15, KV6GiB, maxlen32768, maxseq32, qwen3 reasoning parser. Original power A used the same vLLM/model/schema but resource caps0.20/KV8GiB; this resource-setting difference is disclosed rather than described as identical serving configuration.

Per arm:220 GUI draws, T0.8/top_p0.9/top_k20/max3072, reasoning enabled/medium, exact JSON schema and seeds; plus3 fixed plain-text T0 controls. No retries. Gates: JSON≥95%, healthy proxy loss≤2pp, healthy text, fs+ answer reduction≥15pp or independently verified better actions; channel hypothesis additionally requires fs+ loss greater than true-finish loss. Healthy proxy means valid nonanswer, not demonstrated downstream task success. Paired bootstrap intervals resample tasks, not individual seeds. No online admission from incomplete arms.

## Results and decision
Attribution is complete:6357 raw records,6435 forward calls, all39 contexts complete, all312 zero-mask controls exactly zero, maximum full-versus-cache margin difference0.198738. Independent recomputation matches every supplied aggregate exactly.

| Diagnostic | Mean fs+ margin loss | Mean true-finish margin loss | Difference fs+−true |
|---|---:|---:|---:|
| All note/thought interior tokens neutralized |7.5485|8.1850|−0.6365|
| Best selective single head, L11h2 |0.04359|−0.00739|+0.05098|
| Best raw-strength single head, L7h13 |0.04798|0.01811|+0.02986|
| Best selective DeltaNet output patch, L17 |0.08205|−0.10039|+0.18243|

Neutralization difference task-bootstrap95% interval is[−2.1332,+0.7996] logits. This does not establish equivalence or absence of an internal discriminator. Selection-biased descriptive intervals for selected heads are in independent_attribution_stats.json, not treated as confirmatory significance. The very small head effects should be interpreted alongside the measured replay sensitivity. Narrow final-query attention-link masking cannot rule out earlier-token, multi-head, recurrent-state, or residual routes.

Generation screening pending. No checkpoint recommended yet.

## Evidence
PROTOCOL.md; VERIFY_ATTRIBUTION.md; attribution_pilot_attempt*.log/jsonl; attribution.jsonl; baseline_A/; spec_*.json; build_*.json; verify_*.json; runs/; screen_*.json. Decisions and any cleanup are appended in LOG.md. Ares owns all online confirmation.
