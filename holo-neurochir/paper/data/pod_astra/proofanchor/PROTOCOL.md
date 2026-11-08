# Proof-anchor — frozen before measurements

2026-11-08. Original Holo-3.1-4B, revision `8c88265a5a159bfd1492db9243733dd2e6e04a6e`. Source manifest SHA256 `2faee8f1af5a1243b8c8bacbf0369e4e035ab9dc336307c9f6678c0d134c24d0`. Exactly 39 feasible contexts, 19 false finishes and 20 true finishes, one context per task. The 16 healthy contexts are not part of either requested analysis. Source data, source code and model weights are read only. No generation, no API evaluation, no weight intervention.

## Replay and anchoring

Reuse astra-broad `anchoring.splice`, `ceiling.extend`, and the canonical `holo.osw_replay` serialization. Frozen astra-power OpenAI messages were constructed by that replay; decode their images losslessly for the HF processor. Check payload hashes, source hashes, all evaluator functions, recorded history and retained images before forwarding. Use BF16 eval, `use_cache=False`, final-position logits only. Each condition has exactly the same prompt and total token count.

- a: original recorded reasoning, note and thought.
- b: original reasoning; note and thought replaced by repeated `Observing the current screen.` with contextual token lengths matched exactly.
- c: original reasoning; note and thought replaced by repeated `The task is not complete yet; I still need to inspect the screen.` with contextual token lengths matched exactly.
- d: original note and thought; recorded reasoning replaced by repeated neutral text, preserving reasoning token length and the closing think delimiter.

One selected true-finish context has a JSON null note. Preserve that null in every condition and intervene on its thought; retain all 39 contexts. Report this limitation and a 38-context sensitivity analysis. Terminal filler text may be truncated at a token boundary; record all actual strings and lengths.

Margin is the raw next-token logit of answer minus the maximum first-token logit of other schema tools. Record all tool logits and token IDs; multi-token tool names are represented by their first token, not full-string likelihood. Check tool-boundary identity. Report condition means, paired differences a-b, a-c, a-d (positive means the removed text favored answer), and ratios (a-b)/a by task. Also report ratio of stratum means and warn when original margins are zero or near zero. Bootstrap tasks within strata, 10,000 replicates, percentile 95% CIs; use the same paired resamples for all conditions. Compare a-b between false and true finishes by bootstrap difference and two-sided label permutation (10,000 shuffles). This is not an equivalence test. A null interaction cannot prove no discriminator.

## Representations and probes

Capture original-condition post-layer residuals at zero-based decoder indices 8, 12, 16, 20, 24, 28. Record that index convention explicitly. Positions: final prompt token; final token of recorded reasoning plus closing think delimiter; final token before the first semantic character of the note value (before null for the one null-note context). Save exact positions and token offsets; no note content is available at the note-onset position.

39 leave-one-task-out folds; positive label = false finish. No label-dependent hyperparameter tuning. All fitted preprocessing uses training tasks only. For each of the 18 layer-position cells: L2 logistic regression (C=0.1), cosine kNN (k=3 and k=5, uniform votes), and MLP (one 64-unit ReLU hidden layer, L2 alpha=10, fixed seed, maximum 300 optimizer iterations). Standardize residuals within each training fold for logistic/MLP; cosine kNN uses the original vectors. No test-fold normalization fit and no global supervised feature selection. Report convergence warnings. Step, prompt token length, reasoning token length, and joint step+length logistic baselines use exactly the same folds. Also report raw, direction-fixed metadata rankings to expose leave-one-out calibration artifacts.

Before measurements amendment: for computational efficiency, express standardized inputs in the complete nonzero right-singular-vector basis of the training fold (relative numerical cutoff 1e-10, no truncation of its signal subspace). This is an isometry on training examples, preserves L2 penalties and loses no training variation; test directions orthogonal to that span are unlearnable and discarded. MLP initialization occurs in this basis. Add an intercept-only LOO baseline, which has AUROC=0 from fold class-prevalence alone; no orientation flips.

Compute pooled out-of-fold AUROC and 10,000 stratified task-bootstrap CIs of fixed out-of-fold scores. These are descriptive resampling intervals: they do not establish 95% coverage for future learned performance, since overlapping training sets, fitting variability and winner selection are not resampled. Report paired bootstrap AUROC differences versus metadata baselines. All 72 probes are exploratory; their best observed AUROC is subject to selection bias.

Refit the selected best probe under 1,000 task-label permutations (39 unique tasks). Report the plus-one one-sided permutation p-value, full null distribution, and a conservative 72-test Bonferroni adjustment. With 1,000 permutations, the minimum adjusted p-value is 72/1001=0.07193: the familywise 5% threshold is unattainable. Do not call the unadjusted selected-winner test confirmatory. No post-result orientation flips.

Estimate 80% power at one-sided alpha=.05 for a pre-specified continuous score AUROC using binormal independent-task simulation with 19 positives and 20 negatives; report the minimum detectable AUROC and simulated power curve. Compute rejection thresholds from the exact Mann-Whitney null distribution; also give two-sided .05 and 72-test thresholds. This oracle-score calculation is optimistic relative to learning a high-dimensional probe from 38 training tasks and is not proof of probe sensitivity. The actual Bonferroni-corrected 1,000-permutation procedure has zero power at .05 because its resolution cannot reach the threshold.

## Bounds and independent verification

Completion: 156 distinct context-condition forwards and 39 residual tensors of shape (6,3,hidden), exact source/model provenance, all 72 OOF probe vectors, matched baselines, 1,000 completed permutations, power curve, REPORT.md and RESULT.json, independent checker verdict. Pilot first context before full cohort. Maximum 160 started forwards including failures/rechecks; maximum three launch attempts; stop after two failures without progress, any fleet STOP, or 10:05 UTC for GPU work. No open-ended search. All compile/temp caches under `/workspace/astra/proof-anchor/compile_cache`, no `/dev/shm` cache. GPU only through fleet gpu_slot.sh; kill only owned PIDs. CPU fits serialize with two threads. Deadline for audited report 10:15 UTC.
