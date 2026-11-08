# Independent statistical methods verification

Verified at 2026-11-08T07:43:05.437033+00:00 by `/root/stats_check`, which did not write the analysis implementation.

- **RAN:** Source review and lightweight synthetic CPU checks on the deployed pod. Exit code 0; two CPU threads; no GPU or remote file writes.
- **PASSED:** Both requested regression fixes and all six check groups.
- **CORRECT:** No remaining method blocker found for launching the cohort analysis. This is a scoped methods verdict, not a verdict on results that have not yet been audited.
- **NOT RUN:** Integrity audit of all 156 forwards and 39 captures; complete cohort probe, baseline, and permutation verification; final report and result audit; model/GPU execution.

Verified `analyze.py` SHA256: `4c2d5cc7e2ef24c1a5bc11245a9faaea665c2b9f34f31b8b94a3f16e0061a77d`.

Verified `PROTOCOL.md` SHA256: `c9fcfc025c016080208bbc6166161f163c5982b2f0e76a8a09fbb7b7c6cabf0d`.

| Check | Evidence |
|---|---|
| Undefined ratios | Zero stratum means and all-zero denominators serialize with strict JSON; undefined values and empty finite bootstrap intervals are null. |
| Exact permutation ties | Two sklearn AUROC values, 0.4855263157894737 and 0.48552631578947364, share exact 2U=369. Selection and permutation comparison now use integer 2U. |
| Bootstrap weighting | Weighted pairwise AUROC matched explicit resampling in 12 synthetic replicates; maximum error 1.11e-16. |
| Training-only SVD | Three logistic folds matched unreduced training to within 7.86e-13 in predicted probability; retained rank 37. |
| LOO prevalence artifact | The intercept-only score produced AUROC 0 as analytically expected. |
| Oracle power | Exact upper thresholds 250, 261 and 301 independently matched SciPy exact Mann–Whitney probabilities. Bilateral rejection includes both tails. |

The 80% power grid crossings are AUROC 0.725 (one-sided 5%), 0.755 (two-sided 5%) and 0.845 (one-sided 0.05/72). Simulation standard error at power 0.8 is 0.00283, with an AUROC grid step of 0.005. These are oracle-score calculations. The actual 1,000-permutation Bonferroni procedure cannot reject at 5%.

The interpretation limits remain binding: fixed-score bootstrap intervals are descriptive; the selected best probe is exploratory; low pooled LOO AUROC cannot establish absence of signal; raw-margin ratios are unbounded. The amended SVD preserves the training geometry and L2 penalty, while the MLP is explicitly initialized in that basis.

Detailed numerical evidence and scope are recorded in `VERIFY_METHODS.json`.
