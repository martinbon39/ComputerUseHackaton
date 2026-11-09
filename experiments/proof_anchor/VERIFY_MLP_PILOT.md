# Independent MLP optimization pilot

Verified at 2026-11-08T07:52:04.900670+00:00. The checker did not modify the analysis or its original results.

- **RAN:** Two fresh fits on fold 0 of the highest original MLP, `L20_prompt_end_mlp64_l2`, with 300 and 3,000 iterations. Only the iteration cap changed.
- **PASSED:** The 300-iteration score exactly reproduced the stored OOF score. The longer fit ended without a convergence warning.
- **CORRECT:** The original iteration cap truncates optimization on this fold; its effect on the held-out probability is modest. This does not establish stability across other folds.
- **NOT RUN:** The other folds or cells, a complete supplemental AUROC, supplemental permutations, final result audit, or any GPU execution.

| Quantity | 300 iterations | 3,000 iteration limit |
|---|---:|---:|
| Actual iterations | 300 | 2,696 |
| Objective | 0.19889530 | 0.18734665 |
| Held-out false-finish probability | 0.74233694 | 0.73106812 |
| Largest absolute gradient component | 0.02984249 | 0.01777386 |
| Elapsed seconds | 0.100 | 0.652 |
| Termination | Iteration cap reached | Relative objective reduction |

The objective decreased by 5.81%; the held-out probability changed by −0.01127, without crossing 0.5. The largest training-probability change was 0.02489. The longer run stopped by the relative-objective criterion, with a gradient still above `tol=1e-5`; it is not a certificate of stationarity or a global optimum.

A separately frozen, descriptive sensitivity covering all 18 MLP cells at 3,000 iterations is reasonable and appears feasible. This one-fold timing extrapolates to roughly 8 minutes for 702 fits. A new 1,000-permutation MLP analysis extrapolates to roughly 7 hours, so it should not be implied as part of that sensitivity.

Preserve the original 72-probe analysis and its selected-probe permutation test. Do not replace its winner or apply its Bonferroni-72 p-value to a supplemental winner. Selection across both sets would cover 90 configurations and the extension occurred after seeing original results. The sensitivity can assess optimization dependence descriptively without an additional significance claim.

Use one bounded supplemental pass with `max_iter=3000`; keep `max_fun=15000`, the optimizer, seed, alpha, and preprocessing fixed, and report all warnings. The original warning-limited estimator remains reproducible, but its weak performance cannot establish absence of a nonlinear discriminator.

Verified analysis SHA256: `4c2d5cc7e2ef24c1a5bc11245a9faaea665c2b9f34f31b8b94a3f16e0061a77d`.

Original result SHA256: `80ab8c7ec4b031ea82c339f53294752d84351a3c82673f62c6d7d127023f4398`.

Detailed optimizer messages, gradients, and probabilities are in `VERIFY_MLP_PILOT.json`.
