# Prospective dose amendment after fleet preemption

This amendment is written after the historical half-strength addition failed (24 complete outputs, no answer reduction) and after full-strength addition was preempted (six healthy outputs complete, all valid; no fs+ or fs- result). It does not retroactively preregister those results. No GPU launch is authorized while astra-think is excluded from fleet PRIORITY.

## Fixed intervention and units

Keep layer 31 and the existing learned direction fixed. This isolates dose from layer selection. The literature note about layers 22–30 is a different recommendation, not evidence for moving the current layer after outcomes. The learned direction hash is 791089598cb62680b9276a2733b916937a0fe29af88140f9352aa2f809d72ade.

The historical scale was 24.51417350769043 (norm of the mean difference). The new scale is R31=50.02117300961911, the mean Euclidean norm across each fixed five-token conclusion window, then across the four original samples per task, then equally across four construction tasks. No evaluation activations contribute. This is a mean of norms, not the norm of a mean. Calibration hash: dcce13a5f407534684baa863d3058c5dbb0a644cd04da4436f547b63d9371151.

New addition: h' = h - d * R31 * u31, at every generated position consumed by the decoder, including action JSON. Doses in increasing order: [0.5, 1, 2, 4, 8, 16]. Historical additions represented approximately 0.245 and 0.490 times R31; their labels and units remain unchanged.

For every dose, run a paired random direction v31 drawn once from isotropic Gaussian PCG64 seed 271828, unit normalized, then fixed across all doses. Its addition has the same Euclidean magnitude d * R31. Random direction file hash: 38478a1a3e1e701e27b4767ac28b1f72d5ff2eabc833d5944c32268315155db4. No resampling or choice among random vectors is permitted.

Projection remains h' = h - alpha * (h dot u) * u, with dimensionless alpha 0.5 and 1 in the two historical pending jobs. Alpha is not a residual-norm dose. The same alpha on a random direction would not guarantee matched perturbation magnitude. Any promising projection requires a separately specified magnitude-matched control before a causal claim; no such result exists now.

## Order, controls and stopping

First resume only the 18 missing full-addition outputs with the same context IDs and seeds. Aggregate with the preserved six outputs only after unique-key, seed, source-hash and intervention checks. Then finish the two already registered projection jobs. If a completed historical job meets the common screening criteria, pause escalation for the required control and diagnostic confirmation.

Otherwise run learned then random additions for each increasing dose on the same six disjoint screening contexts, four seeds each, with protected strata first. Both arms keep the existing early protection rejection. A protected-stratum rejection is the operational point of breakdown, not proof of global model damage. Finish the paired random arm at that dose, then stop higher doses. If both arms reject earlier, retain that as their measured result; never fabricate missing fs+ rates. A selective learned screening result pauses higher doses for its matched control and held-out diagnostic confirmation. A random arm passing too prevents interpreting the effect as specific to the learned direction.

Five lots are already reserved. Exact resume (one), historical projections (two), and six learned/random pairs (twelve) total at most twenty. Failed allocations, preemptions and any extra controls or confirmation also consume the same absolute cap20 and reduce remaining grid coverage. No hidden retries and no automatic extra budget. If coverage is cut short, report that limitation. A family may be called unpromising only over doses actually measured, with its measured protection boundary; this supersedes the earlier stop rule based solely on two weak families.

Admission thresholds are unchanged: fs+ answer drop >=25 points AND >=50% relative, fs- answer loss <=5 points, healthy valid non-answer loss <=5 points, overall invalid/truncated increase <=5 points. No partial arm is admitted. Everything remains exploratory until the common threshold of40 admissible fs+ is reached; the two-task fs+ pilot also needs independent diagnostic confirmation. Keep the canonical45-task diagnostic reserve out of construction. Never read split_test.json or its results. No gradients, training or weight editing is authorized by this prospective plan.

Fleet safeguards: one owned GPU child, process below15 decimal GB, parent-death guard verified, CPU thread caps2 before imports, shared gpu_slot, STOP check and >=20-second cooldown. All twelve jobs are prepared on CPU only and hash-pinned. No unattended GPU controller is started.
