# Astra broad — distributed static weight surgery

Owner: astra-broad. Status: dose grid superseded by ares6235; closed after independent result audit, 2026-11-08 03:16UTC, 2026-11-08 UTC. No OSWorld success gain established.

The first complete checkpoint changes the stopping decision on held-out diagnostic contexts. At dose100%, false-success `answer` falls from15/16 to8/16, but labeled true-finish `answer` also falls from15/16 to3/16. Healthy actions remain16/16 and all three text controls are coherent. This fails the prescribed preservation gate. The norm-matched random100 control stays at16/16 answers in both terminal strata,16/16 healthy actions, and three coherent texts. At50%, the counts are12/16 fs+ and9/16 true finishes: efficacy and preservation both fail. Ares message6235 superseded the remaining dose grid in favor of anchoring.

## Scope and provenance

Hcompany/Holo-3.1-4B revision `8c88265a5a159bfd1492db9243733dd2e6e04a6e`;32 layers, residual dimension2560. Only24 static residual-writer weight matrices in layers12–23 change:12 MLP down projections and12 attention/DeltaNet output projections. No gradients, adapters, production prompt, schema or harness edits. All inference assets are copied byte-for-byte from the pinned source.

The frozen manifest SHA256 is `35499feb2f482f811814d2e88f62b9ca202e91e37e99b336f9969e770564d332`. Construction uses two diagnostic false-success contexts and their immediately preceding GUI actions. These donors share a task but are neither step-matched nor independently verified healthy states. Preservation uses two true finishes, two healthy first steps and three generic text prompts. Evaluation uses six other diagnostic tasks, two per stratum. All evaluation tasks are disjoint from construction and preservation. Canonical45 reserve task membership is excluded; reserve and test episode contents are not used.

## Replay evidence

Each replay reconstructs the original multimodal input, recorded reasoning and serialized JSON prefix up to the tool-name value. The measurement is the first-token logit of `answer` minus the highest first-token GUI-tool logit. It is a teacher-forced conditional margin, not a generated decision probability. Diagnostic swaps touch only the last decision token.

| Context / intervention | Answer margin |
|---|---:|
| fs0 original |16.875|
| fs0 donor |−17.125|
| fs0 all32 MLP outputs |0.875|
| fs0 MLP0–11 /12–23 /24–31 |18.375 /8.875 /4.125|
| fs0 all writers0–11 /12–23 /24–31 |16.125 /−3.5 /−10|
| fs0 all32 writers |−17.125|
| fs1 original |18.375|
| fs1 all32 MLP outputs |2.125|
| fs1 writers12–23 |−3|
| true finish original / fs0 donor writers12–23 |16.375 /−2.25|

Self-swapping reproduces the complete logit vector exactly; final-residual replacement reproduces donor logits exactly. Replacing all residual writers with donor outputs can algebraically reconstruct the donor residual when the final token embedding is shared. That result alone is not selective localization. The cross-task true-finish swap also flips the decision, showing this donor displacement is not intrinsically selective. Failure of these particular MLP swaps is not an impossibility theorem for all distributed MLP edits.

The initial run retained10 records before a shared volume quota failure; at least one additional forward may have run without a persisted record. A separate bounded recovery retained11 records. Both runs and checks are preserved; missing observations are not reconstructed.

## Closed-form edit

The method adapts the preservation projection of [AlphaEdit](https://arxiv.org/abs/2410.02355), rather than claiming an exact implementation of its sequential model-editing algorithm. For each writer, edit keys K are the two fs+ inputs at three positions: last prefill, end of recorded reasoning, and tool-name decision. K0 contains corresponding preserved GUI inputs and the three generic text inputs. Q spans K0; Kp=K−QQᵀK.

The desired residual displacement for each paired position is donor final residual minus fs+ final residual, divided equally across24 writers. With this target matrix R, the update is:

`ΔW = R (KpᵀKp + λI)⁻¹ Kpᵀ`, with `λ = 0.01 mean(diag(KpᵀKp))`.

The small system is solved in float64 by Cholesky, factors stored in float32, and the complete checkpoint serialized in BF16. Maximum relative target-fit error is2.5925%; maximum sampled preservation residual is1.626e−14 before casting. This is a simultaneous local linear approximation. Preservation at original sampled inputs does not guarantee preservation after upstream states change during generation.

Dose100% changes354,868,124 serialized elements,6.8574% of the serialized element count including tied copies. Only24 of724 tensors are eligible for edits. The largest relative writer Frobenius change is0.08081. Per-writer BF16 rounding error relative to the requested update ranges2.056–13.418%.

Random controls keep the same right factors and replace the left directions with seeded Gaussian directions. The builder matches their per-writer realized BF16 perturbation norms to the learned arm at the same dose within0.1%, with a bounded scalar calibration. Random100 has passed the independent stored-norm check (maximum relative mismatch0.00923%); lower-dose random controls were not measured after the ares redirect. The check prevents silently treating equal ideal norms as equal stored norms.

## Behavioral measurement

Canonical `osworld/astra_cohort_probe.py`, vLLM0.23 on the same H200 pod; temperature0.8, top_p0.9, top_k20, thinking enabled, exact existing step schema, max_tokens3072, eight common seeds7100–7107 per GUI context. Three text controls run at temperature0. Original serves on8000 and candidates on8020. Both use BF16, max_model_len32768, max_num_seqs64 and prefix caching; resource reservations differ (original KV30G/gpu-util0.40, candidates KV4G/0.15). This resource difference is disclosed and was not assumed equivalent by proof.

| Arm | fs+ answer /16 | labeled true-finish answer /16 | healthy valid action /16 | invalid/error/truncated GUI | text |
|---|---:|---:|---:|---|---|
| original |15|15|16|0/0/0|3 coherent|
| learned100% |8|3|16|0/0/0|3 coherent|
| random100% |16|16|16|0/0/0|3 coherent|
| learned50% |12|9|16|0/0/0|3 coherent|

The user gate requires a25-point absolute reduction in fs+ answer, at most5-point loss on true finishes and healthy actions, and healthy text. The stricter shared fleet gate also requires a50% relative fs+ reduction. With these denominators, one lost protected sample is already6.25 points. Dose100% fails protection regardless of the relative-reduction gate. These are repeated stochastic samples from only two tasks per stratum, not16 independent tasks.

The initial visual audit was withdrawn after finding an off-by-one image-selection error: row.t is a zero-based trajectory index, while screenshot filenames are numbered from1. Canonical replay and generation inputs were correct; only the separate human-readable audit selected the previous screenshot. The corrected current screenshot shows all four recipients complete, so the claim of a suspect true-finish label is withdrawn. Three extra prefix writes may damage the completed recipient list; actions were not executed. GIMP's current screenshot has already closed Preferences, so the audit must not claim the current image itself shows the saved value. A corrected audit binds each image to traj[row.t].screenshot_file and its frozen hash.

## Verification and artifacts

RAN/PASSED: exact replay self-control and final-residual control; independent exhaustive checkpoint checks of724 tensors (24 exact edits,700 exact originals), finite values, source assets, hashes and disjoint cohorts; four completed arms each48 canonical GUI calls plus3 text controls,204 responses total. Generation integrity and semantic text checks have separate retained artifacts. A standalone algebra-unit-test artifact is not retained, so no such test is counted as verification here.

CORRECT: the checkpoint implements the stated static update and changes stopping behavior on this small diagnostic panel. NOT ESTABLISHED: selective repair, improvement in completed tasks, OSWorld score gain, or generalization. NOT RUN by astra-broad: online reserve/test evaluation.

Three complete checkpoints are durably uploaded to Modal account1: `holo-models:/ckpt/broad_residual_p100`, `/ckpt/broad_residual_p050` and `/ckpt/broad_residual_random100`. Upload receipts, full weight/asset hashes, factor tensors and verification reports are retained locally. Temporary pod APIs were stopped by owned PID and shm checkpoint copies released after upload and measurement. Raw evidence is in this directory and small canonical files in `/workspace/astra/astra-broad`; large working artifacts are in `/dev/shm/astra-broad`.

The initial repository pull was blocked by pre-existing shared modifications; a fetch showed no divergence at that time. Unrelated files were not reset or staged. A whole-repository whitespace check currently fails on unrelated pre-existing changes; owned Python syntax checks pass. No claim is made that all repository checks pass.

## Scope amendment at02:42 UTC

Ares6235 requested skipping dose25% and prioritizing the factorized anchoring test. The random50% CPU checkpoint finished writing, but its independent verification was deliberately interrupted by owned PID387964; it was not uploaded or served. Its unverified construction manifest was retained and its temporary checkpoint removed. Dose25% and random25% were never constructed. These are NOT RUN behavioral arms, not negative measurements. The original admission thresholds remain unchanged.

## A — factorized anchoring

Original weights, observation and history are fixed. On each of the two construction contexts, replace recorded reasoning, the serialized JSON prefix before the tool name, or both with the same-task donor counterpart. This is a diagnostic input intervention, not a production prompt change. The original input reconstruction is asserted tensor-for-tensor and token-hash identical.

| Teacher-forced prefix | fs0 answer margin | fs1 answer margin |
|---|---:|---:|
| Original |16.875|18.375|
| Donor reasoning only |7.625|11.125|
| Donor JSON prefix only |1.125|−3.125|
| Both donor components |−7.375|−7.625|

The margin depends strongly on the already-written conclusion, especially the note/thought JSON prefix. Therefore the14–19-logit margin at the tool-name position must not be interpreted as intrinsic robustness of the observation-level decision. This does not show that a weight edit can selectively change that earlier conclusion. The fixed run completed14 forwards: eight factorial conditions and six evaluation captures, with no generation or weight change. See `anchoring_summary.json` and `anchoring.jsonl`.

## B — common projection across24 writers

Build D from the two construction donor-minus-false-success differences, summed across both residual writers in layers12–23 at the tool-name decision position. D has numerical rank2, singular values22.9431 and7.4486; its first direction explains90.465% of this two-column sample energy. This cannot establish the dimension of the general behavior.

For each arm, reset original matrices and apply `W ← W − dose U_k U_kᵀ W` in FP32, stored in BF16, to all24 writers. The fixed20-forward schedule measures two construction fs+ and two preservation true finishes. Weights are restored in `finally`.

| Rank / dose | fs0 / fs1 margins | finish0 / finish1 margins |
|---|---|---|
| Original |16.875 /18.375|16.375 /14.75|
|1 /0.5 |10.875 /10.875|11 /10.625|
|2 /0.5 |11.25 /11|10.875 /10.625|
|1 /1 |1.375 /1.625|4.75 /2.75|
|2 /1 |1.75 /1.625|4.875 /2.625|

No arm meets the preregistered teacher-forced admission gate: both fs+ margins below zero while both true-finish margins remain nonnegative. No checkpoint or generation was produced for B, and the dose range was not extended after seeing results. This is a negative result for this fixed projection family, not an impossibility bound. See `projection_summary.json`.

## C — key discrimination and its confound

Fit a normalized centroid direction and closed-form ridge classifier on two construction fs+ versus two preservation true finishes; both strata use tool `answer`. Freeze the classifiers before loading two other fs+ and two true-finish captures. All four evaluation tasks are disjoint from training. At the tool-name decision position, MLP down-projection inputs yield empirical AUROC1.0 in all12 layers12–23 for both classifiers. Mixer-writer keys yield1.0 in nine layers,0.75 in layers18 and23, and0.5 in layer21.

This apparent separation is not evidence of a semantic failure detector: input length alone has AUROC1.0 in both training and evaluation. Training fs+ lengths are9351/10938 versus9042/9112 for true finishes; evaluation fs+ lengths are13305/13292 versus10367/9441. With only four evaluation contexts, task progress and length are major confounds. Empirical AUROC is neither an information bound nor proof that selective editing is possible. See `key_probe.json`, `key_probe_length_control.json` and `key_probe_helper_check.json`.

## D pilot — before the note begins

Ares6258 requested moving measurement before the first token of the note value. The pilot retains the original recorded reasoning and evaluates the same eight terminal contexts: four classifier-training contexts and four other diagnostic contexts. Two fixed continuations are scored: `The task is completed.` (five tokens) and `The task still needs work.` (six tokens). We report total and mean conditional log probability differences plus the first divergent token logit difference; unequal length makes these distinct measurements. Both branches give exactly identical logits at their shared-prefix divergence position.

All eight contexts prefer the completed continuation, with total log-probability differences from17.982 to34.607. On the four held-out contexts, all three continuation scores have fs+ discrimination AUROC0.5. The fixed layer-key classifiers give MLP AUROC0.25–0.5 and mixer AUROC0.25–0.75, below the tool-name measurements on this tiny panel. This is not a localization result: recorded reasoning may already contain the conclusion, and step index and input length each have AUROC1.0. The fixed24-forward run and downstream CPU analysis completed successfully; see `note_onset_summary.json`, `note_onset_key_probe.json` and `note_onset_controls.json`.

Ares6275 subsequently requested expansion to the frozen regmean pool,19fs+ and19true finishes, with task-group cross-validation and a comparison to the step-index baseline. That expanded diagnostic was separately preregistered in `note_pool_plan.json`; completed results follow below. Its manifest SHA256 is `a75e9e3f62b67493b3727aa966eba59a4dcab9b1f28ae69031a1749dc861630c`. The source pool, source manifest and75-task allowlist hashes were independently checked. All38 selected terminal tasks are unique and outside reserve45 and the six broad evaluation tasks. One task overlaps prior broad construction (`fs_1`); it remains in the exact requested pool and is disclosed. This is exploratory cross-validation, not a completely unseen confirmatory panel. The primary feature is the concatenation of24 unit-normalized layer keys; its fixed closed-form ridge uses leave-one-task-out validation with per-fold balanced class weights. This prevents a changing training class prior from acting as a held-out-label cue. Secondary layer results are all reported and cannot establish a best-layer discovery. Paired bootstrap intervals resample fixed out-of-fold predictions by task and do not include refitting uncertainty.

## Note-pool recovery and control denominators

The first expanded run stopped after36 persisted forwards: `context_012` has an original `note: null`, so the string-note onset assertion correctly rejected it before its forward. CPU inspection of all38 serialized actions found37 string notes and this one null note. The source manifest remains unchanged; `note_pool_eligibility.json` excludes the null-note case, yielding18fs+ and19true finishes. This eligibility decision was made before any classifier fit or AUROC on model features.

The recovery captures prefix keys during each of the two forced continuations. Both branches must reproduce every recorded prefix activation exactly, and one standalone-prefix control per class must also match exactly. It saves accumulated keys after each completed context. The completed cumulative count is36+74+2=112 forwards, below the original114 ceiling. The external timeout enforced TERM03:29:28/KILL03:29:43, earlier than the original03:29:58UTC deadline; the recovery completed at about03:13UTC. Initial logs are preserved. See `note_pool_recovery_plan.json`.

Direct recomputation of nuisance baselines gives step/input-length AUROC0.78809/0.79501 on the38 terminal source rows and0.78509/0.79532 on the37 eligible rows. Including all16 healthy rows in the original pool gives0.80451/0.80902. These do not reproduce the0.852/0.845 numbers supplied in the order; the final comparison uses exactly the same eligible rows as the feature classifier, with the preregistered0.85 primary threshold unchanged. No explanation for the earlier baseline discrepancy is asserted.

## Expanded D result — the fixed note-onset probe fails

The37 eligible contexts completed with original weights. All prefix activations (`mlp`, `mixer`, residual, MLP keys and all32 mixer keys) match exactly between continuation branches in every context. Both standalone-prefix controls also match exactly. The recovery exited0; capture hashes agree after transport. The independent method review validates the weighted dual ridge against a separate primal calculation (maximum numerical difference4.61e−15), task-group separation and the externally enforced deadline.

| Prespecified measurement | AUROC, fs+ positive |
|---|---:|
| Primary24-key concatenated weighted ridge, leave one task out |0.593567|
| Raw step index on the same37 rows |0.785088|
| Raw input length on the same37 rows |0.795322|
| All24 individual key probes, exploratory range |0.508772–0.695906|
| Forced-continuation total log-probability difference |0.459064|
| Forced-continuation mean token log-probability difference |0.450292|
| Forced-continuation first-divergence logit difference |0.599415|

The paired2000-draw task bootstrap over fixed out-of-fold predictions gives a95% percentile interval of[0.3975,0.7679] for the primary AUROC. Difference from step is[−0.3571,−0.0417]; difference from length is[−0.3676,−0.0559]. These are conditional descriptive intervals, excluding model-refit uncertainty. The preregistered primary gate fails. No layer is selected, no threshold is changed and no checkpoint is compiled from D.

All18 labeled false successes and all19 labeled true finishes prefer the fixed completed continuation over the fixed unfinished continuation. Total log-probability margins average29.665 versus31.454, respectively. These two generic English continuations have different token counts and follow the original recorded reasoning; they are not calibrated beliefs, generated stopping rates or verified task outcomes. The null-note branch is outside this analysis.

This result does not support a selective edit at the measured note-onset position using this fixed linear key probe. It does not bound all possible nonlinear information in the states, earlier reasoning positions or other weight edits. Across the static edit arms, no candidate meets the requested efficacy-and-preservation gate. The principal positive finding is that broad closed-form updates can move the stopping decision; the unresolved problem is preserving genuine finishes.

Evidence: `note_pool_probe.json`, `note_pool_continuation_summary.json`, `note_pool_summary.json`, `note_pool_recovery_scores.jsonl`, `note_pool_captures.pt`, `D_cv_review.md`, `note_pool_deadline_evidence.json`. Own candidate APIs were already stopped; the owned SSH forwarding process was stopped by verified PID233871. Other fleet services were left running.

The interrupted-run and recovered scores are exactly identical for all24 overlapping continuations (12 contexts), including token-level probabilities and complete input-token hashes; see `note_pool_restart_consistency.json`. All owned diagnostic launch PIDs have exited; `final_process_status.json` retains their exit codes, including the initial expected assertion exit1 and the successful recovery exit0.

Final independent numerical audit: `D_results_review.md` / `.json` reproduces the primary, nuisance, all24 secondary and all three continuation AUROCs; it verifies task folds, balanced weights, eligibility, hashes, metadata and112-forward accounting. No classifier refit or GPU rerun was performed by the checker. Because only one canonical branch activation is retained per context, exact branch equality is supported by the executed runtime assertions and successful run summary, not by re-comparing two saved branch tensors.
