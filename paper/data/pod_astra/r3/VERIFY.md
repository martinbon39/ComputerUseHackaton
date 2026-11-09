# Round 3 independent audit

RAN: CPU-only AST-isolated existing parser, adapter and taxonomy functions; independent enumeration from saved rows/actions. No model loading, generation or CUDA calls.

PASSED: 12 assertions, plus paired fit independently verified as **103 pairs across 13 tasks** and all source rows seeds 0–5. Checks: distance 14.999 matches; distance 15 does not match; missing call does not match; cropped pixel conversion and offsets; same text repeats; different text does not repeat; malformed coordinate rejected; screen seeds 0-5; screen unique contexts; pilot seeds 0-5; pilot unique contexts; manifest pair count matches.

CORRECT by inspection: four replicates; stable SHA256 RNG key (run,t,replicate); strict <15 pixel repeat comparison with crop offsets; HEALTH same tool plus click proximity; adapter errors invalid; locked budget reserves before generation and enforces <40; existing JSON/JSONL blocks duplicate restart. Prior pair-population restriction and successful-loop HEALTH exclusion are corrected. CUDA allocation fraction is set to 24 GiB before loading.

Limitations: PCA-named directions use uncentered SVD, not centered PCA. Two sampled populations are concatenated without general deduplication, though current screen uniqueness passes. PyTorch allocator cap does not bound external allocations or guarantee production throughput isolation. run.py lacks an independent seed-split assertion; current manifests pass. HEALTH follows permissive existing parser/adapter defaults for missing text/key arguments.

NOT RUN: behavioral efficacy, steering/weight equivalence, heldout 6–7, online 50–51, production latency. No behavioral success claim.

Invalid/null current-action controls in paired fit: 5.

## Persistent batch runner audit

Inspected batch.py and five core jobs without execution. Screen: 24 rows, 24 unique contexts, 12 loop+, 12 HEALTH, 0 overlap; four replicates imply 48 REPEAT and 48 HEALTH samples. Steering is reset per job, RNG is stable, budget is reserved separately for each job, and JSON/JSONL restart protection is present. No model-weight edits occur between these steering-only jobs.

Additional limitations: gpu.lock is used by batch.py but not run.py, so it does not mutually exclude pilot and batch processes. peak_reserved_gib is lifetime peak, not per-job peak because memory stats are not reset. Five paired controls have missing/error current calls and should be excluded to interpret the contrast strictly as valid changed actions.

## Corrected pairing and vectorized generation audit

Independent CPU-only enumeration verifies **97 valid-action pairs across 10 tasks** after requiring current and previous calls to have no parse error and an adapter action. This supersedes the earlier 103/13 counts and resolves the invalid-control finding.

Inspected vectorized batch.py plus installed transformers generation implementation. Qwen3_5ForConditionalGeneration inherits GenerationMixin; multimodal encoder preparation runs before expansion. GenerationMixin._expand_multimodal_outputs duplicates each entire image group in correct order; _expand_inputs_for_generation repeats text and attention masks and handles 3D position batch dimension. Therefore num_return_sequences=4 is supported for this multi-image context; layer steering hook broadcasts over batch dimension. No generation was run by this auditor.

The call preserves temperature=.8, top_p=.95, top_k=20, max512 and original EOS/padding/decode handling. RNG now uses one stable per-context group seed. Vectorized draws are valid four samples but are NOT the same RNG experiment as previous four scalar calls; only vectorized baselines should be compared with vectorized interventions. Replicate IDs identify rows within the group, not four separately seeded runs. CUDA peak stats now reset per job, resolving prior cumulative-peak issue.

NOT RUN: numerical image-expansion test, model generation, scalar/vector outcome equivalence. Assessment above is source-level, not behavioral validation.

## Compiler and additive hook audit

RAN: isolated compile.py and existing _writers with a tiny CPU synthetic model containing tied embedding/head, vision merger with bias, full attention, linear attention and MLP writers. No real model loaded or edited.

PASSED: all six writer targets present; head untied with original values preserved; both tie flags false; embedding transpose projection and linear weight/bias output projections match writer hooks at alpha=.7. Maximum elementwise writer-output discrepancy: {"torch.float32": 2.384185791015625e-07, "torch.bfloat16": 0.0078125}. Float32 tolerance 1e-6 passed; bf16 discrepancy reflects reordered rounding and is not bit-exact. Denominator captured before untie, and modified count uses actual rounded element differences.

Compiler limitations: writer-hook equivalence is established only for full-column compilation (topk=None). topk pruning is an approximation requiring behavioral revalidation. Writer hooks remain a different intervention from layer-end set_steering; a successful original steering result still needs an explicit writer-hook behavioral bridge. Hooks must be removed before executing compiled weights, to avoid double intervention. Actual save/reload tie preservation not tested. Paths match installed Qwen3.5 source.

Additive mode inspection: correctly subtracts alpha*u at each selected layer output, broadcasts over batch/token dimensions, and binds each direction/alpha in hook defaults. Old hooks removed between jobs and original steering reset. Positive alpha pushes opposite u; this is constant additive steering, distinct from negative projection strength. n_in assertion correctly checks rebuilt token count against recorded count but is not proof of token/image identity.

## Exhaustive saved-training coverage and state-reset audit

Independent scan of every saved training summary/steps file (no protected diag reads): {"saved_runs": 152, "manifest_runs": 152, "saved_steps": 839, "train_rows": 839, "missing_rows": 0, "all_pairs": 97, "all_pair_tasks": 10, "extra_pairs": 0, "extra_unique_controls": 0}. All saved seeds satisfy 0–5. No omitted controls or expanded construction needed; train_rows covers every saved step. 

Inspected batch_compiled.py reset: original Parameter objects and CPU clones captured before any edits; every original tensor copied back; original shared lm_head Parameter reinstated; both tie config flags restored; inference hooks removed and residual steering cleared. For this model whose original head is tied, the reset restores the original state between compiled and uncompiled jobs. Newly cloned head from prior compiled job is dereferenced on replacement. No model load or real-weight test performed by auditor. Limitation: resetting tie flags unconditionally assumes original configuration true (verified for Holo 0.8B). The runner should still log/assert numerical state restoration if empirical assurance is needed.

## PCA artifacts and raw-output recomputation

RAN with OPENBLAS_NUM_THREADS=1 and OMP_NUM_THREADS=1; no generation/model loading. Verified native/shared10/mean/paired/mlp bitwise unchanged versus directions_core.npz. Reconstructed 97 paired differences and independently solved centered Gram-matrix eigenproblems for all 24 residual and 24 MLP PCA directions; all absolute cosines >.99999 and relative eigen residuals <1e-4. This resolves the earlier uncentered-PCA limitation.

Independently reparsed raw text and converted coordinates for every completed core result (baseline,u10_L10,u10_L9_13,u10_all,native_all): all stored valid/repeat/healthy_match booleans, metric numerators and denominators match. Evidence: audit_numeric.json. No heldout files read.

## Identity behavioral reproducibility caveat

Identity alpha=0 rerun differs from baseline in 4/96 raw texts (92/96 identical); reparsing and coordinate reconstruction confirm stored booleans and REPEAT 46/48, HEALTH 35/48 versus baseline HEALTH 36/48. Thus one-generation HEALTH difference (2.083 percentage points) exists under an intended no-op, and exact stochastic reproducibility has not been established. Alpha=0 layer steering still executes matmul, multiplication and subtraction; for finite values it is algebraically identity, but does not bypass hook allocation/arithmetic. Kernel/runtime nondeterminism, numerical execution differences, or changed process/configuration are possibilities, not established causes. A single controlled original rerun could estimate repeatability if budget permits. Treat candidate differences near this scale cautiously.

Differing rows: [{"key": ["login-user__s4", 2, 0], "label": "loop-", "success": false, "baseline_call": {"name": "click", "arguments": {"element": "Password input field", "x": 400, "y": 610}}, "identity_call": {"name": "click", "arguments": {"element": "Password input field", "x": 400, "y": 580}}, "baseline_metric": [true, false, true], "identity_metric": [true, false, true], "target": {"name": "click", "arguments": {"element": "Password input field", "x": 400, "y": 580}}}, {"key": ["enter-text-2__s2", 0, 1], "label": "loop-", "success": false, "baseline_call": {"name": "click", "arguments": {"element": "text input field", "x": 400, "y": 350}}, "identity_call": {"name": "type_text", "arguments": {"text": "Cristin"}}, "baseline_metric": [true, false, false], "identity_metric": [true, false, false], "target": {"name": "click", "arguments": {"element": "text input field", "x": 300, "y": 300}}}, {"key": ["enter-text-2__s2", 0, 3], "label": "loop-", "success": false, "baseline_call": {"name": "click", "arguments": {"element": "Text input field", "x": 300, "y": 300}}, "identity_call": {"name": "click", "arguments": {"element": "Text input field", "x": 350, "y": 350}}, "baseline_metric": [true, false, true], "identity_metric": [true, false, false], "target": {"name": "click", "arguments": {"element": "text input field", "x": 300, "y": 300}}}, {"key": ["use-autocomplete__s1", 0, 2], "label": "loop-", "success": false, "baseline_call": {"name": "click", "arguments": {"element": "Tags input field - long rectangular text box below 'Tags:' label", "x": 450, "y": 380}}, "identity_call": {"name": "click", "arguments": {"element": "Tags input field - long rectangular text box below 'Tags:' label", "x": 450, "y": 385}}, "baseline_metric": [true, false, true], "identity_metric": [true, false, true], "target": {"name": "click", "arguments": {"element": "Tags input field", "x": 450, "y": 380}}}]

## Exact early HEALTH rejection and row-order audit

Inspected batch_next.py and remaining_jobs.json. Exhaustively checked 1225 possible (healthy seen, hits) states for the current denominator 48: implemented upper bound (hits+48-seen)/48 < .70 is equivalent to inability to reach 34/48, the minimum discrete score meeting fixed baseline .75 minus .05. Rejection begins at 15 healthy misses. It cannot reject a candidate capable of passing this fixed HEALTH criterion, irrespective of unseen outputs. REPEAT criterion remains >=50% relative reduction; early failure of either required criterion suffices, so no pass rule is weakened.

Original baseline_repeat has no direction and bypasses early rejection. Healthy-first sorting does not change intended context/RNG pairing: per-context SHA256 group seeds are order-independent. Compare results by (run,t,rep), never positional zip. However previously observed identity variation means numerical execution/order effects are not ruled out; baseline_repeat quantifies combined process/order repeatability, not order alone.

Incomplete rejection output's health is the observed partial mean, not full-panel HEALTH; health_upper is the rigorous full-panel upper bound. If loop rows were not evaluated, repeat=None is correct and must not be converted into zero. Interrupted amplification with four outputs similarly has no full score and is distinct from mathematically certified early rejection.

Scope limitations: .70 is hardcoded for the frozen .75 screening baseline; a new heldout baseline requires its own threshold, not blindly reusing this runner. Current remaining_jobs.json contains baseline plus ten projection jobs, no additive-mode job; this audit does not establish additive coverage elsewhere. No heldout data, generation, or implementation edits.

## End-of-screen audit before additive completion

RAN: CPU-only independent raw-text parsing, coordinate reconstruction and metric recomputation by (run,t,rep), every available completed/early-rejected result plus both successful pilots. PASSED: 1216 saved generations; every stored boolean, fraction, denominator and upper bound matches. All seeds 0–5, group RNG hashes and context/rep uniqueness verified. 23/40 ledger entries sequential and unique; 20 planned screening jobs plus 3 pilots account for expected 23 lots. Pending: ["u10_add025"].

CORRECT: all early rejections have mathematically impossible HEALTH under original frozen .70 threshold; incomplete metrics remain partial and no REPEAT inferred. report_negative.py refuses missing non-aborted plan results, including additive, and refuses any qualifying winner; do not run before additive outcome.

Identity caveat: 92/96 text matches, REPEAT46/48 unchanged, HEALTH35/48 vs36/48. Unsteered baseline_repeat HEALTH34/48 vs36/48 (4.167 points), REPEAT46/48 unchanged; cause/process/order effects unisolated. No threshold relaxation.

NOT RUN: real-weight compilation, export/reload, top-k search, heldout6–7, online50–51, production latency measurement. Report must preserve these absences. Evidence: audit_final_pending.json.

Strict feasibility artifact check PASSED: reconstructed exactly 73 pairs from raw summaries/actions matching task, step and impossible, then independently recalculated residual/MLP mean directions and centered PCA across all layers. Saved strict directions match (mean maxabs <1e-5; PCA cosine >.99999). {"paired": {"max_mean_difference": 9.776154441532015e-09, "pca_min_cos": 0.9999999977913805}, "mlp": {"max_mean_difference": 1.598946464120843e-08, "pca_min_cos": 0.9999999979534033}}

# FINAL INDEPENDENT VERDICT — 2026-11-07T17:59:04.508671+00:00

RAN: independent raw-text/coordinate metric audit for 1,216 completed or early-rejected/pilot generations (prior section), plus final parsing of all 8 outputs from both interrupted variants; report-table-to-result comparison for every final/partial arm; ledger/manifest, selection and GPU-process inspection. No generation or real model loading by verifier.

PASSED: **1,224 saved raw generations**, **23/40 lots**, all 20 screening jobs and 3 pilots accounted for. Both interrupted variants have exactly four invalid outputs each and are labeled non-evaluable, not certified HEALTH failures. All report scores and bounds exactly match saved results. Largest completed-result peak reserved GPU memory **6.017578125000 GiB**, rounding to6.02. Final selection patch_spec=null, modified weights0/0%, heldout=false, online=false. No active experimental batch Python process found; GPU compute listing at audit: `65221, 42814 MiB
82006, 900 MiB` (remaining process is outside experimental scope).

CORRECT: conclusion is only that this bounded search found no validated admissible intervention. Incomplete amplification/additive arms cannot support full-panel efficacy or failure claims. C/D were not executed, random control is inference-level, and no successful patch is claimed. strict_mlp bound is33/48=68.75%, not its observed partial21/36. Identity92/96 text matches; HEALTH35/48 vs original36/48; unsteered repeat34/48; all REPEAT46/48. This numerical variability remains unresolved and thresholds were not weakened.

NOT RUN: real Holo compilation, behavioral writer/weight equivalence, pruning, export/reload, seeds6–7 heldout, seeds50–51 online, production-latency isolation. Synthetic compiler checks do not substitute for these. Verification supports faithful reporting of a negative/incomplete experimental outcome, not achievement of a successful anti-loop patch.

Verified REPORT_ROUND3.md SHA256: `3fa27d1743e2e5e4ada57ceee131deb7d4f9c799d1c28bdec421ef86bbbeffaf`.

Final-version supersession: historical 103-pair/13-task and uncentered-PCA findings above describe corrected intermediate artifacts. Final tested pairing is97 valid-action pairs across10 tasks; strict task+step+impossible pairing is73 pairs across10 tasks. Final tested residual and MLP PCA directions are centered, independently numerically verified. Remaining GPU PID82006 command inspected as `/workspace/venv/bin/python runner.py pilot_generation_v2_job.json`, unrelated to the astra3 batch runners; it was not touched.
