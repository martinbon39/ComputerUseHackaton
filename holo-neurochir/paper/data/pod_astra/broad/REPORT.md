# Astra broad — distributed static weight surgery

Owner: astra-broad. Status: experiments running, 2026-11-08 UTC. No OSWorld success gain established.

The first complete checkpoint changes the stopping decision on held-out diagnostic contexts. At dose100%, false-success `answer` falls from15/16 to8/16, but labeled true-finish `answer` also falls from15/16 to3/16. Healthy actions remain16/16 and all three text controls are coherent. This fails the prescribed preservation gate. The norm-matched random100 control stays at16/16 answers in both terminal strata,16/16 healthy actions, and three coherent texts. Lower doses and their controls are pending.

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

Random controls keep the same right factors and replace the left directions with seeded Gaussian directions. The builder matches their per-writer realized BF16 perturbation norms to the learned arm at the same dose within0.1%, with a bounded scalar calibration. Random100 has passed the independent stored-norm check (maximum relative mismatch0.00923%); lower-dose controls are pending. The check prevents silently treating equal ideal norms as equal stored norms.

## Behavioral measurement

Canonical `osworld/astra_cohort_probe.py`, vLLM0.23 on the same H200 pod; temperature0.8, top_p0.9, top_k20, thinking enabled, exact existing step schema, max_tokens3072, eight common seeds7100–7107 per GUI context. Three text controls run at temperature0. Original serves on8000 and candidates on8020. Both use BF16, max_model_len32768, max_num_seqs64 and prefix caching; resource reservations differ (original KV30G/gpu-util0.40, candidates KV4G/0.15). This resource difference is disclosed and was not assumed equivalent by proof.

| Arm | fs+ answer /16 | labeled true-finish answer /16 | healthy valid action /16 | invalid/error/truncated GUI | text |
|---|---:|---:|---:|---|---|
| original |15|15|16|0/0/0|3 coherent|
| learned100% |8|3|16|0/0/0|3 coherent|
| random100% |16|16|16|0/0/0|3 coherent|

The user gate requires a25-point absolute reduction in fs+ answer, at most5-point loss on true finishes and healthy actions, and healthy text. The stricter shared fleet gate also requires a50% relative fs+ reduction. With these denominators, one lost protected sample is already6.25 points. Dose100% fails protection regardless of the relative-reduction gate. These are repeated stochastic samples from only two tasks per stratum, not16 independent tasks.

The initial visual audit was withdrawn after finding an off-by-one image-selection error: row.t is a zero-based trajectory index, while screenshot filenames are numbered from1. Canonical replay and generation inputs were correct; only the separate human-readable audit selected the previous screenshot. The corrected current screenshot shows all four recipients complete, so the claim of a suspect true-finish label is withdrawn. Three extra prefix writes may damage the completed recipient list; actions were not executed. GIMP's current screenshot has already closed Preferences, so the audit must not claim the current image itself shows the saved value. A corrected audit binds each image to traj[row.t].screenshot_file and its frozen hash.

## Verification and artifacts

RAN/PASSED: exact replay self-control and final-residual control; independent exhaustive checkpoint check of724 tensors (24 exact edits,700 exact originals), finite values, source assets, hashes and disjoint cohorts; original and p100 each48 canonical GUI calls plus3 text controls. A standalone algebra-unit-test artifact is not retained, so no such test is counted as verification here.

CORRECT: the checkpoint implements the stated static update and changes stopping behavior on this small diagnostic panel. NOT ESTABLISHED: selective repair, improvement in completed tasks, OSWorld score gain, or generalization. NOT RUN by astra-broad: online reserve/test evaluation.

The complete p100 checkpoint is durably uploaded to Modal account1, `holo-models:/ckpt/broad_residual_p100`; upload receipt, full weight/asset hashes, factor tensors and verification report are retained locally. Its temporary pod API was stopped by owned PID and its shm checkpoint released after upload and measurement. Raw evidence is in this directory and small canonical files in `/workspace/astra/astra-broad`; large working artifacts are in `/dev/shm/astra-broad`.

The initial repository pull was blocked by pre-existing shared modifications; a fetch showed no divergence at that time. Unrelated files were not reset or staged. A whole-repository whitespace check currently fails on unrelated pre-existing changes; owned Python syntax checks pass. No claim is made that all repository checks pass.
