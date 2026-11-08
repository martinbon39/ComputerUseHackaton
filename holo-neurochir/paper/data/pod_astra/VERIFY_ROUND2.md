# Round 2 independent verification — pre-heldout
UTC: 2026-11-07T16:36:49Z
RAN: CPU-only independent recomputation of frozen hashes, budget sequencing, all candidate rankings, directions, and safetensors reconstruction. No GPU forward, no heldout access.
PASSED:
- All 14 frozen hashes match.
- Budget 1–46 sequential, <=50. First45 contain18 Round2 screens; development already underway.
- Exactly18 new completed screen results, seed0–5 and row alignment checked. Entire ranking independently reproduced.
- Winner a2_r3_a3, deltas {'loop+': 0.009305053623393178, 'healthy': -0.0010669618980803837, 'loop-': 0.0022304730489850046, 'success': -0.0063211227866954035}; worst-healthy ratio 4.17178483.
- All four direction files reproduced, errors {'mlp': 0.0, 'matched_resid': 0.0, 'matched_mlp': 0.0, 'reference': 0.0}; matched directions use positive-frequency-weighted within-t loop+/loop- contrasts.
- Export revision 72da4c53b351eb60e10a7022279019633c479292; 30 writers, 1966080 targeted scalars. All column indices, before/after BF16 values, and export hashes independently verified.
- Full development 415 rows, seeds0–5; loop+/healthy overlap 1.
- Empty-group analysis guard and a2_final_patch export branch reviewed corrected before freeze.
CORRECT: Screening selection and patch reconstruction reproducible. Alpha3 is over-subtraction, not partial projection removal. Healthy is successful-rollout OR loop-, with overlapping classes. Random shares nominal count, not necessarily columns, BF16 nonzero count or norm. Scoring is raw reply+EOS, not rollout success.
NOT RUN: Full development outcomes, heldout outcomes, GPU weight-export equality, live GPU memory. Await final artifacts.

## Development and reserved-snapshot independent audit
UTC: 2026-11-07T16:50:24Z
RAN: CPU recomputation of full-development group means, all task-bootstrap confidence intervals, five strata, screening overlap repeatability, frozen hashes, and reserved manifest completeness against collection_status.py expected list.
PASSED: 415 development rows; all published means/intervals/strata match to 1e-12. Original and patch screen-overlap log probabilities reproduce exactly. All14 freeze hashes still match.
CORRECT: Full-development patch FAILS selectivity: deltas {'loop+': 0.003889972266430656, 'healthy': 0.00996839923941162, 'loop-': 0.009156443334414984, 'success': 0.010857450975371259}; ratio worst healthy 0.358276752. This contradicts generalization of the screening result, not replay reproducibility.
PASSED: Reserved snapshot timestamp follows freeze; exactly48 distinct task/seed pairs from declared24-task list crossed with seeds6–7; 142 unique selected rows, no train run overlap. Completeness source is recorded producer arguments as declared by collection_status.py; live producer arguments not independently reread.
Budget at audit: 48 sequential entries <=50.
NOT RUN: Final GPU result aggregation, random control comparison, actual GPU-weight export verification. Only heldout manifest/row metadata read at this stage, not final scores.

## Final independent audit
UTC: 2026-11-07T16:54:55Z
RAN: CPU recomputation of all original/patch/random heldout group means, full-response sums, task-bootstrap intervals (2000 draws), selection criteria and ratios; row/token alignment; frozen hashes; final50 budget records; CPU/GPU patch export comparison; Round2 report numeric tables and conclusions.
PASSED:
- Budget exactly50/50, sequential1–50. All14 pre-heldout freeze hashes remain unchanged.
- 142 aligned final rows from seeds6–7; identical scored token counts across arms.
- Every published final mean, sum and bootstrap interval matches independently to1e-12; report tables match rounded means.
- Patch and random specs equal frozen specs. Both target exactly1966080 scalar weights.
- GPU export contains1966080 targeted scalars; before weights/column indices match CPU reconstruction.
- Actual GPU patch changes 1953863 BF16 scalars; independently reconstructed Frobenius norm 4.63900955263, agreeing with reported float32 statistic.
- CPU/GPU after-value maximum absolute difference 0.0001220703125, differing entries 223; actual GPU export is authoritative.
CORRECT:
- Patch final deltas: {'loop+': 0.0023072647011798363, 'healthy': 0.008923234871711911, 'loop-': 0.010327669496958455, 'success': 0.009418616924516822}.
- Random final deltas: {'loop+': 0.0012979242221816726, 'healthy': 0.004189605920520776, 'loop-': 0.004199161163220803, 'success': 0.005328894286692419}.
- Patch worst-healthy ratio 0.223406133; random 0.243563515. Both FAIL the3x criterion.
- Patch suppresses loop+ more than random in point estimate, but also suppresses healthy actions more. This is not evidence of selective correction; patch loop+ bootstrap interval includes zero.
- REPORT.md Round2 correctly reports no validated selective edit, failure on full development and reserved data, unchanged patch after freeze, and no demonstrated rollout improvement.
- Count-matched random control is nominal only: BF16 effective changed counts and perturbation norms differ, as report explicitly states.
NOT RUN: No new model forwards, gradients, or rollouts. Random actual changed count/norm independently available only as recorded GPU statistics because no random weight export was requested. Live GPU accounting and producer command provenance not independently remeasured.
Final verification verdict: PASSED for reproducibility/accounting and truthful negative conclusion; experimental acceptance criterion FAILED.
