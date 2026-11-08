# Astra preamble — closed, no admitted checkpoint

The learned dose 2.0 fails both behavioral gates: **0/8** done notes begin with the exact preamble and choose verification (required ≥6/8); **14/16** healthy generated texts and **11/16** exact tool calls differ from the paired original (allowed ≤1/16). The matched random control also has 0/8 preambles. All three text controls remain correct in all arms.

Ares requested closure in message 6456. Dose 1.0 was cancelled during CPU construction, before a complete manifest, independent checkpoint verification, or any generation. Its random checkpoint was not built. No candidate was sent for online evaluation. All owned experiment processes and the tunnel stopped; **41,492,037,065 bytes** of temporary checkpoint files were removed by **05:47:52 UTC**, before the **06:30 UTC** deadline. Captures, factors and evidence remain in `/workspace/astra/astra-preamble`.

## Frozen controls and results

Each completed arm generated 27 responses: eight done contexts (four true, four false), sixteen healthy contexts and three text controls. There were **81/81 complete responses**, **72/72 valid GUI JSON objects**, and no errors or truncations.

| Measurement | Original | Learned dose 2.0 | Random dose 2.0 | Required for learned arm |
|---|---:|---:|---:|---|
| Exact preamble at done-note start | 0/8 | 0/8 | 0/8 | ≥6/8, with verification |
| Exact preamble plus real verification | 0/8 | 0/8 | 0/8 | ≥6/8 |
| Generic “Before” start | 0/8 | 7/8 | 0/8 | Diagnostic only |
| Done-context answer action | 7/8 | 7/8 | 8/8 | Diagnostic only |
| Healthy full-text differences | — | 14/16 | 14/16 | ≤1/16 |
| Healthy exact tool-call differences | — | 11/16 | 11/16 | ≤1/16 |
| Text controls semantically correct | 3/3 | 3/3 | 3/3 | 3/3 |
| GUI JSON valid | 24/24 | 24/24 | 24/24 | All |

The learned arm changes opening style but never installs `Before declaring completion, I verify the result on screen:`. The exact phrase appears nowhere in its eight done notes. Three notes express prospective verification; two still emit `answer`. The remaining click minimizes a Files window to inspect the screen, and that action already occurs in the original. There are no additional verification actions.

The random update matches realized Frobenius norm per writer within maximum relative error 2.427e-5. Its seeded signed row permutations reproduce exactly under independent checking. It does not meet the efficacy gate. The random-control and text checks are complete; efficacy and preservation fail.

## Scope and frozen data

Weights-only experiment on Hcompany/Holo-3.1-4B, revision `8c88265a5a159bfd1492db9243733dd2e6e04a6e`. No gradients, optimizer, LoRA, serving prompt or harness changes. Only the 24 designated layer 12–23 writers were edited: twelve `down_proj`, nine `linear_attn.out_proj`, and three `self_attn.o_proj` at layers 15, 19 and 23. Inputs were captured from `args[0]`.

The allowlist `/home/orbit/projects/holo-osworld-runner/tasks/diag_extra.json` was loaded before episode reads. Exclusions: `chrome/480bcfea-d68f-4aaa-a0a9-2589ef319381` and `libreoffice_writer/bb8ccc78-479f-4a2f-a71e-d565e439436b`. No reserve or split_test episode content was read. Only original DIAG and DIAG2 were used; extra_gh was not used because available labels did not match its source paths.

Construction: 48 conclusions, balanced 24 false/24 true; protection: 100 healthy contexts. Evaluation: eight task groups disjoint from the 57 construction/protection tasks. Construction and protection share 23 tasks by design. Source episodes stayed read-only; selected prefixes were copied to the owned pod directory and checked by checksum.

Manifest SHA256: `43eae282c73f74b03485bfa9f18b1fc3dd8b8a498e500c0b82faffbb14fbfbf7`.

## Authorized recipe correction

Teacher-forcing future preamble tokens cannot change an activation at the same preceding prefix. The original same-site source/target capture would therefore give a zero residual. Independent audit identified this; ares explicitly authorized a replacement in message 6440.

The replacement sets each next-token target by closed-form norm-preserving geometry of the final residual under Qwen3.5 RMSNorm and the output head. A bounded active-set calculation, at most eight active-set iterations, requires global vocabulary margin ≥2. The displacement is divided across 24 writers. Transport through intervening nonlinear layers is a heuristic, not an exact equivalence. All eleven preamble-token positions use causal teacher-forced prefixes; free-running generation is decisive.

Each writer has 528 construction keys (48 contexts ×11 tokens) and 100 protection keys. The exact dual ridge fit uses λ=10 on the sum of protected outer products and ε=0.001 times mean squared construction-key norm. Solve precision is float64; stored factors are float32. Doses 1.0 and 2.0 were registered before behavioral generation. The four-context pilot favored dose 2.0 for first-token wins, so it was evaluated first. No dose or threshold was added after evaluation.

## Independent numerical and checkpoint checks

The scientific auditor confirmed exact cohort IDs, writer scope, all 528 token targets (minimum margin 2.000543), and maximum norm-preservation relative error 2.793e-7. Independent float64 recomputation of layer-12 MLP and layer-23 attention fits reproduced stored right factors within 2.535e-8 relative error. Independent normal-equation residuals were below 3.78e-14; stored float32 factors had residuals up to 3.684e-6. These are construction checks, not behavioral success.

Across all 24 writers, reported fit errors range 0.0090–0.0291; maximum protected output Frobenius norm is 0.00432 versus target norm 4.496. Factors SHA256: `48f11f38adce96fa8603e758b07369cfcdae420c188733bf4e79c23e4883cc08`.

Fresh checkpoint verification passed for original, learned dose 2.0 and random dose 2.0: 724 tensors each. In edited checkpoints, 700 untouched tensors retain source dtype and bitwise values, and exactly 24 edited writers use FP16. Config, tokenizer and other source assets are byte-identical. An initial builder rejected global BF16-to-FP16 storage conversion because it changed 169,556 tiny lm_head entries; the corrected builder preserves unedited storage exactly. No tolerance was weakened. All arms served with identical `--dtype float16`, matching runtime precision.

The three complete HF checkpoints and the incomplete dose-1 checkpoint were removed under ares's closure instruction. Complete manifests and verification evidence remain; there is no admitted checkpoint.

## Runtime, accounting and stop

Validation used unchanged canonical `astra_cohort_probe.call`, vLLM 0.23.0, temperature 0.8, top_p 0.9, top_k 20, thinking enabled, exact step JSON schema, max_tokens 3072 and fixed GUI seed 7100. The three canonical text prompts used temperature 0 with thinking disabled. Each arm used a fresh sequential server through `gpu_slot.sh`; version and model root were checked before requests. No online evaluation was run.

Capture used **158/160 forwards**: two failed one-forward instrumentation attempts, then one completed 156-forward integrated run. A diagnostic norm readout had re-entered the sequence capture hook; direct norm readout and a hook shape assertion fixed that. An inference-tensor mutation outside inference mode caused the second failure; the complete runner now executes inside inference mode. Both logs remain; the cumulative counter persisted across restarts. Behavioral generation used **81 requests**. Dose-1 behavior and its random arm are **NOT RUN**, cancelled on ares's explicit stop.

Verification status: numerical/checkpoint integrity **RAN / PASSED**; generation/schema checks **RAN / PASSED**; learned behavior **RAN / NOT CORRECT against frozen gates**; online evaluation **NOT RUN**. Independent semantic reviews are separate from the maker's measurements.

Only owned PIDs were stopped. The unrelated production GPU process 193632 remains running; local tunnel ports 18025–18027 are closed. Checkpoint cleanup freed approximately 38.64 GiB. No more experiments are scheduled and no CANDIDAT signal was sent.

Git pull was blocked by pre-existing shared changes; fetch showed HEAD and origin/main at 0/0 divergence. No unrelated files were restored, stashed or staged. Ares owns fleet Git archival.

## Interpretation limits

This rejects the tested implementation and dose against the frozen gates. It does not disprove the general preamble idea, because the complete preamble was never installed. Generic “Before” wording without verification is insufficient.

Exact healthy text or coordinate differences are not all harmful regressions. Independent reading found mostly wording, coordinate or wait variants and two material route changes in the learned arm. Both edited arms share the same aggregate healthy-difference counts. One original baseline at the same request seed does not measure residual vLLM/GPU nondeterminism; these differences cannot all be causally assigned to weights. Semantic judgments use generated outputs, without live action execution or a screenshot-based outcome claim.

## Evidence

- `PROTOCOL.md`, `manifest.json`, `pilot.json`, `forward_count.json`, `solve.json`.
- `SCIENTIFIC_AUDIT.json` and `.md`: independent target/factor audit.
- `astra_preamble_*.manifest.json` and `.verified.json`: tensor and provenance checks.
- `astra_preamble_*.generations.jsonl`, `.requests.json`, `.server.log`, `.summary.json`: paired outputs and metadata.
- `SEMANTIC_LEARNED_D20.json` and `.md`, `SEMANTIC_RANDOM_D20.json` and `.md`: independent semantic reviews.
- `validation_events.jsonl`, `*.stopped.json`, `CLEANUP.json`: execution and cleanup evidence.
- `captures.pt` and `factors.pt`: retained on the pod, sufficient to reconstruct the rejected edit from the frozen source revision.
