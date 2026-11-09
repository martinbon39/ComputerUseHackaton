# Results of the weight-edit track (summary of 8 November 2026)

> Written before the paper's external review. Where it differs from the paper, the paper is authoritative: in
> particular the paper reads the merge and AlphaEdit effects as moving the stopping decision without being shown to
> target false successes (paper §6).

Source: paper (arXiv / NeurIPS versions) and our research journal (not included in this kit). Offline numbers = sampled generations on frozen contexts (16 samples per stratum unless noted), small n: read them as direction, not as statistics.

## 1. Primary verdict (rule fixed before reading the results)
Merge (CUA-Lite, β=0.5) vs the original **served by the same backend (Modal)**, OSWorld, paired by task, bootstrap 95 % over tasks.

| Set | n | merge (sum of scores) | original (sum of scores) | Δ points | CI95 | wins / losses |
|---|---|---|---|---|---|---|
| reserve + test (primary) | 165 | 92.5 | 89.3 | **+1.9** | [−4.3 ; +8.0] | 18 / 14 |
| test only | 120 | 70.5 | 70.3 | +0.2 | [−6.5 ; +7.5] | 11 / 10 |
| reserve only | 45 | 22.0 | 19.0 | +6.6 | [−6.7 ; +22.1] | 7 / 4 |

**Verdict: no detectable gain** (lower bound < 0). "reserve" is the split named `confirm` in the CSV. The Modal-vs-Modal reference was chosen as primary by a rule fixed after the first pod-served runs had been seen; against the pod-served original the merge is −1.3 pt on the test (n=120, CI [−8.9 ; +6.4], 12 wins / 13 losses; printed by `verify_results.py`). Reproduce with `verify_results.py`. Noise reference: the same original served by two backends differs by +1.5 pt (test, CI [−4.5 ; +7.6]) and +4.4 pt (reserve), the same order as the observed effects. Minimum detectable effect on the 45-task reserve: about 17 points (80 % power).

## 2. Causal lever: learned edit vs random edit of the same norm
24 writer matrices of layers 12–23, closed-form AlphaEdit-style edit, 100 % dose, contexts of the false-success cohort (generation, 16 samples/stratum).

| Arm | false success, `answer` (fs+) | true finish, `answer` (fs−) | healthy steps (no `answer`) | invalid |
|---|---|---|---|---|
| original | 15/16 | 15/16 | 16/16 | 0 |
| learned edit | **8/16** | **3/16** | 16/16 | 0 |
| random edit, same norm | 16/16 | 16/16 | 16/16 | 0 |

Reading: the effect comes from the learned direction, not from perturbing the block (causal). It is **not a selective repair**: true finishes drop faster than false successes, at 50 % dose too (12/16 and 9/16). The whole fs+ drop comes from one context (multi_apps b337d106: 7/8 → 0/8; the Calc context stays 8/8). A rank-1 removal moves the fs+ margin from 16.9 and 18.4 to 1.4 and 1.6 logits, but the true-finish margin to 4.75 and 2.75.

Merge, same kind of table (cohort of 2 fs+ contexts, 2 fs− contexts, 2 healthy): β=0.25: fs+ 15/16, fs− 11/16; β=0.5: fs+ 11/16, fs− 2/16, healthy 16/16. On the feasible fs+ context `chrome/47543840@13` the answer rate goes 8/8 → 3/8, on the true finishes 8/8 → 1/8 and 8/8 → 1/8 (`contexts/`). The other fs+ context (`chrome/480bcfea@4`) is an infeasible task where `answer` is the right action (8/8 → 8/8).

Online, AlphaEdit p100 on the reserve: 20.0/45 vs 19.0/44 or 21.0/45 depending on the original used (Δ −2.2 to +2.2, CIs contain 0).

## 3. Discriminability vs position (why it is not selective)
Can internal states tell a false success from a true finish? 19 vs 19 episodes, per-task cross-validation.

| Predictor | AUROC |
|---|---|
| keys of the 24 writers, before the reflection | 0.704 |
| keys of the 24 writers, end of reflection | 0.634 |
| keys at the beginning of the note (18 vs 19) | 0.594 [0.40 ; 0.77] |
| **step number** | **0.852** |
| text length | 0.845 |
| step number + length | 0.859 |

83–86 % of the false-success key energy lies inside the subspace of true-finish keys. The internal states discriminate **less** than the position in the episode; the metric-dependence of this ordering was flagged by a red-team review, so we write "no better than the position", not "worse in general". Also: the tool-name margin (14–19 logits) is measured after a thought that already says "task completed" and swaps sign when the donor's written text is transplanted (anchoring test, 1–2 feasible contexts): it measures copying of a written conclusion, not the decision.

## 4. Localisation of the merge effect (β=0.5; fs+ feasible / true finishes)
Full merge 3/8 and 2/16; layers 0–11 only 7/8 and 8/16; 12–23 only 8/8 and 9/16; 24–31 only 8/8 and 14/16. The drop in false successes appears only with the three blocks combined (an additivity test was not significant, Fisher p = 0.12, so we do not claim non-additivity); the drop in true finishes is spread over layers 0–23.

Note on the merge: `embed_tokens` is merged and Holo has `tie_word_embeddings=true`, so the effective output head changes too (it is not left intact).

## 5. Negative leads (all closed, none yields an admissible edit)
- Replication of the MIT recipe (L17/L20 × 64 columns): 0 useful result, a random control does the same at high dose.
- Hypotheses H2–H10 (DeltaNet gates, q_norm families, attention exit gates, late MLPs toward Qwen, RoPE redistribution): neutral or breaking; 22/25 batches, 637 requests, no admissible edit.
- TACT (literal grid, Gate and Add): no effect; strong dose corrupts text.
- Contrastive RegMean: −12.5 pt fs+ in BF16, no effect in FP16: probably noise.
- Evolutionary merge with a tool-position objective: stopped after 2 rounds without progress.
- Beginning-of-note editing: no discriminating signal (AUROC 0.46 on margins).
- Forcing a verification preamble: 0/8 full preamble; a random control changes as many texts.
- "Save before finishing": 0/14 false successes come from an unsaved file; they are wrong contents.
- Badly worded infeasible tasks: at most 1–2 legitimate lexical gains.
- ExPO λ=1.25: neutral online (test Δ −1.5, CI [−8.9 ; +5.7]). Output-row edit and corrective prompt: partial runs, no gain. Merge β=1.0: invalid format.
- Branching pilot (5 episodes, K=2): merge 4/10 vs original 5/10; no advantage.

## 6. Known limits
- Harness more permissive than the official one on infeasible tasks (RealtimeGUI @ a763361): scores are not comparable with H's.
- Some comparisons were first run against a pod-served original and later re-run Modal against Modal; only the latter is primary. The test split was read for ExPO before it was admitted.
- Small n offline; several offline contexts are single tasks; one fs+ context (`480bcfea@4`) is an infeasible task where `answer` is correct.
- BF16 rounding leaves 88 of 426 language tensors unchanged at β=0.5 (effective update norm 2.34 for 2.01 targeted).
