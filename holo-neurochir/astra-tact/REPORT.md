# TACT on Holo-3.1-4B

Owner: astra-tact. Started 2026-11-08 01:32 UTC.

## Final result — no admitted candidate

Research stopped on 2026-11-08 at 03:20 UTC after the two bounded dose regimes. No learned intervention reduced false completion on this pilot. The large residual-scaled dose corrupted all three deterministic text answers. No weights were edited, no HF checkpoint was compiled/uploaded, and no online OSWorld gain is claimed.

| Completed arm | False-completion answer /16 | True-completion answer /16 | Healthy valid nonanswer /24 | Correct text /3 |
|---|---:|---:|---:|---:|
| Original | 15 | 12 | 24 | 3 |
| Gate, lambda 0.5, k 2 | 15 | 12 | 24 | 3 |
| Add -0.5, literal | 15 | 12 | 24 | 3 |
| Add -1, literal | 15 | 12 | 24 | 3 |
| Add -2, literal | 15 | 12 | 24 | 3 |
| Random -2, literal | 15 | 12 | 24 | 3 |
| Add -0.5 x median residual norm | 15 | 11 | 24 | 0 |

Each completed arm has seven task-disjoint-from-construction contexts, eight paired seeds per context, and three text prompts at temperature zero. There are only two false-completion contexts; sixteen samples are not sixteen independent tasks. Tool validity is not semantic success. Separate screenshot-grounded audits distinguish useful actions, harmless saves, and harm. The corresponding random residual-scaled arm was interrupted during startup after the learned arm's text collapse was discovered; it has no inferred behavioral result.

Semantic audit: useful healthy actions remain24/24 through the literal controls, but23/24 at the residual-scaled dose because one click becomes a no-op. Its extra true-completion nonanswer is a safe Ctrl+S on an already completed document, with the final user-facing answer omitted. All three strong-dose text outputs are harmful regressions. These distinctions do not rescue admission: false-completion improvement is zero and text health fails.

OT detection is promising only as a development result: best task-grouped pooled AUROC 0.98279 versus position 0.88303 and position plus reasoning length 0.94872. Only two tasks supply paired OT/CAL contrasts. OA has one paired task, so task-grouped OA AUROC and a separate-task OA behavioral test are unavailable. This is not a complete empirical reproduction of the paper's dual-axis claim. The detector result did not transfer to the requested behavioral correction.

Independent evidence: `VERIFY_QUANTITATIVE.md`, `VERIFY_SEMANTIC.md`, `VERIFY_RUNTIME.md`; completed-arm integrity passed, candidate efficacy failed. Machine-readable summary: `RESULT.json`. All reserve trajectory content and split_test remained unopened. First AUROC signal before 02:02 UTC and first causal pilot before 02:21 UTC met both deadlines.

## Objective and admission
Model-only, no gradients/training/LoRA or added prompts. Deliver a complete HF checkpoint only after causal steering and compilation equivalence pass. Candidate: false completion answer rate falls at least 25 percentage points (fleet also requests 50% relative), or externally substantiated useful OA action; true completion/healthy behavior losses at most 5 points; invalid increase at most 5 points; healthy text; matched-norm random control does not explain effect.

## Frozen boundaries
DIAG only. Canonical confirm_tasks.json is read solely as an exclusion set; no reserved trajectories or split_test opened. Group by task across passes. Separate construction and behavioral pilot tasks before extraction. Main thread owns outward actions. All Python capped to two CPU threads; GPU through gpu_slot.sh. No writes in sibling experiment directories. No other process stopped.

## Plan, budget and stop rules
First exact-boundary AUROC versus step/context baseline by 02:32 UTC; first steering by 03:32 UTC. At most 400 extraction forwards in the first sweep; at most 12 behavioral arms (baseline, Gate, three literal Add strengths, matched random, then a bounded residual-scaled sweep if needed), eight seeds per context, maximum 3072 generated tokens and three deterministic text probes. Stop at first healthy collapse; at most two successive dose rounds without measurable protected behavioral improvement. Record realized forwards and outputs. No checkpoint presented as a candidate without meeting the behavior gate. A negative/below-baseline detection result remains reportable, not fabricated success.

## Premises checked
- Holo snapshot: 8c88265a5a159bfd1492db9243733dd2e6e04a6e; 32 layers, width 2560.
- Existing osw_replay resid_post captures the newline after </think>, not the boundary token. Dedicated extraction required.
- Paper primary source https://arxiv.org/html/2605.05980v1 : contrasts average intra-task class mean differences over tasks containing both classes; OT primary, OA Gram-Schmidt secondary; Gate is two-sided.
- Static Add compilation applies at every position whereas paper steering is boundary-only. This is an extension requiring separate causal and equivalence tests.
- Existing studies change prose but leave a robust answer decision; fresh paired seeds and controls required.

## Operational state
Pod folder newly created, OWNER.md=astra-tact. Local shared checkout dirty, pull --rebase refused; fetch shows HEAD equals origin/main. No shared source modified. Ares notified through argos session Tj2frJD0DH. Read-only independent audits of data and runtime ongoing.

## Label freeze v2 (before any hidden-state metric)
Initial strict per-step conjunction (long reasoning + repeated action + unchanged screen) left only 5 OT steps and two paired tasks, while holding out two OA tasks exhausted OA construction. This was an excessively narrow interpretation of the requested proxies. The initial manifest is retained as manifest.preliminary_strict.json. No activations or AUROCs had been read before revision.

Final labels: OT = at least128 recorded reasoning tokens and same action in the preceding five actions; OA = non-OT steps from a failed50-step episode with no answer, where its final10 observations contain at least3 stagnant screens OR repeated actions; CAL = non-OT steps of episodes with score1. Screenshot delta uses the existing taxonomy threshold (<1% pixels with channel change>8). These are outcome/repetition proxies, not the paper LLM-judge labels. CAL can include locally poor steps from successful episodes. OA does not prove inability to progress from screenshots alone.

Frozen pool:2079 eligible DIAG steps. Construction971CAL/29OT/97OA; deterministic task/class capped sample220CAL/26OT/8OA =254 states,62 tasks. OT has8 paired OT/CAL tasks. OA has2 construction tasks and only1 OA/CAL pair. Behavioral pilot:2fs+,1OA,2true-complete,2healthy contexts,5 task IDs excluded from construction,8 seeds each. Pilot states are collected only for HF/vLLM prompt-count evidence and excluded from axes.

Strict intra-task OA cross-validation is mathematically unavailable. OT uses the paper intra-task mean-difference; OA will be explicitly exploratory: per-task class means then between-class mean difference, Gram-Schmidt against OT. Folds place the two OA tasks separately. This is an adaptation, not a strict dual-axis reproduction. Ares informed; new DIAG-only rollouts requested through him. No reserve/test trajectory opened.

## Runtime verification and launch
Independent extraction reviewer: token248069 unique, correct boundary index,32layersx2560 capture, canonical context rebuild, no gradients; CPU inter-op cap corrected to2. GPU not tested by reviewer. Independent runtime reader confirmed vLLM effective residual is (MLP hidden write + residual accumulator), and multimodal forwards pass embeddings instead of token IDs. Steering tests use exact equality to the END embedding when IDs are absent; no semantic classifier. Shape mismatch fails. Historical END is forbidden by a prompt-count assertion. Add alters only the MLP write to realize the residual offset; Gate is two-sided with lambda0.5,k2. Uniform random axes are orthonormal with identical per-layer intervention norms.

Extraction acquired fleet slot1 at01:44:06 UTC;261 planned forwards including7 unused-for-training pilot states. Model loading/real GPU verification pending. Recorded reasoning uses the canonical replay suffix; original sampled IDs were not logged, so byte-for-byte reconstruction of the original reasoning token sequence is not independently provable.

Independent CPU checks completed: extraction/prompt-boundary tests PASS; task-grouped folds and OT/OA formula tests PASS; runtime hook mocks PASS for exact embedding gate, two-sided Gate, learned/random equal-norm Add. Runtime SHA7d65651f…39c076, launcher26c734db…43948. GPU behavior remains untested at this point. All Python uses intra/inter-op2; runtime checks STOP before CUDA and watches STOP during generation. Canonical arm budget is locked/fsynced and capped12. Pilot HF token-count evidence is mandatory; any historical END in a prompt rejects it before steering. Raw unused action payloads were removed from the label-feature cache, which contains no email patterns.

## First signal and audited freeze v3, 02:08 UTC
The initial proxy run finished261 forwards with exit0. Its first signal, sent before02:02 UTC, was OT pooled AUROC0.974 vs position0.826 and position+reasoning length0.948. OA proxy AUROC0.791 was below position0.815. These numbers are superseded for interpretation by the audit below; full v2 artifacts remain in proxy_v2/.

Independent screenshot/action review rejected13/26 OT examples as useful work and all8 sampled OA examples as productive recovery or insufficiently supported. Two original fs+ contexts could actually satisfy their tasks and were removed. The original OA pilot was also productive and is now a healthy stress control. Seven later Writer scrolls are confirmed unproductive: each repeatedly leaves the relevant first page for page5, followed by navigation back, without image-export progress. These seven share one task.

Final frozen construction:239 states,219CAL/13OT/7OA,58 tasks. Both axes now use the paper's strict average of within-task differences. Only two tasks have OT/CAL pairs and one has OA/CAL pairs. OA grouped CV is therefore not estimable and no OA generalization AUROC is reported. No task-disjoint OA pilot can be supported by this pool. The seven pilot contexts comprise two visibly false completions (wrong Budget month; wrong pivot-sheet name), two real completions, and three healthy actions across five task IDs. Two former pilot task IDs also remain excluded, giving seven excluded IDs in total. Labels are now frozen; no behavioral outputs were inspected before this revision. Nine additional states were replayed successfully, for270 actual forwards in total.

Final OT grouped out-of-fold AUROC: best pooled0.98279; position(step,log context)0.88303; position+reasoning length0.94872. Best mean within-task AUROC0.9375 versus position0.5625, based on just two paired tasks. Top10 layers chosen by that development-CV mean:19,30,29,31,21,22,23,24,25,26 (zero-based). This selection is not an independent performance estimate. Typical CAL residual norms on those layers span12.06–49.87. Thus a literal Add strength-0.5 adds norm0.707 per layer, roughly1.4–5.9% of the residual norm; residual-scaled doses are a materially different regime. No causal conclusion follows from detection. Baseline vLLM generation launched02:07:32 UTC, with eight fresh paired seeds per context and three deterministic text probes. No model weights edited.

## Baseline and runtime correction, 02:16 UTC
The first vLLM startup failed before generation because ninja was installed in the virtual environment but absent from PATH. The launcher now selects the environment's bin directory, checks ninja, and caps compilation MAX_JOBS=2. Failed startup remains attempt1 in the twelve-attempt budget. Attempt2 baseline_v1 completed56 GUI and3 text outputs, exit0: false-completion answer15/16; true-completion answer12/16; healthy valid nonanswer24/24; no invalid/truncated GUI output. An independent screenshot review confirms8/8 useful Enter actions for the Calc stress control; remaining semantic checks are separate from JSON validity.

The baseline also exposed a real instrumentation defect that CPU-only hook mocks did not detect: decoder prehooks were never entered, despite exactly one END token per generated GUI response. Qwen3_5Model's support_torch_compile decorator overrides __call__ and invokes forward directly, bypassing nn.Module prehooks even with actual compilation modeNONE. The baseline makes no intervention and remains a valid original-model reference. Its source is archived as steer.nn_hooks.py. Before any edited arm, the runner was corrected to wrap the decoder's actual forward, set do_not_compile, assert compilation mode0, and keep layer hooks on the ordinary decoder layers. Runtime admission now requires positive forward/boundary counts and, for an edited arm, positive realized BF16 activation changes at all ten layers. Both requested and realized delta norms are logged. Gate began02:16 UTC; no edited result is claimed yet.

Independent final CPU review: strict within-task means, grouped folds, exclusions, degenerate-axis rejection and top10 selection PASS. Final metrics independently reread and confirmed. Paired comparison now rejects any mismatch of full context metadata or text probe prompt; adversarial label/task/path/t/prompt mutations are rejected. These checks do not establish behavioral improvement or compiled-checkpoint equivalence.

## First Gate observation, 02:22 UTC
Attempt3 Gate reached eight END tokens and80 selected layer rows on the first false-completion context. Requested and realized deltas were both exactly0: all projections remained within2sigma. All eight complete token sequences exactly matched their paired baseline, confirming faithful no-op replay. The runner's positive-delta admission was too strong for a conditional Gate and stopped this partial arm. The corrected guard separates target_rows from actual changed_rows, still requires every selected layer to be reached, and requires nonzero realized changes for unconditional Add/random only. Gate may legitimately do nothing; that is not a successful intervention. Attempt4 gate_v1 repeats the full cohort. The old runner is archived as steer.forward_sync.py. The first causal pilot occurred before02:21 UTC, within one hour of the mission start.

For following arms, the already computed boundary count is reused across layers instead of synchronizing the GPU ten more times for every token; the intervention formula is unchanged. A progress record every500 decoder calls exposes the actual boundary/target/change counters. Full baseline semantic audit independently confirms24/24 useful healthy GUI actions,12/16 appropriate completion answers plus4/16 harmless saves, and3/3 correct text probes.

## Gate complete, 02:31 UTC
gate_v1 completed56 GUI+3 text generations, exit0,545.98 seconds including startup. The runtime reached59 END tokens and590 selected layer rows;59 rows changed after BF16 rounding, aggregate realized delta norm15.5632. False-completion answer15/16, true-completion answer12/16, healthy valid nonanswer24/24: all rates unchanged. All40 protected GUI outputs are token-identical to baseline. Four fs+ outputs differ in wording/action payload, with no changed answer decision; one text probe differs and receives semantic review. No candidate.

The teacher-forced explanatory probe (gate_probe.json) places the Budget fs+ at max0.995sigma, pivot fs+2.045sigma, and late healthy Calc4.460sigma. This supports the observed nonselective triggering but is not used as a behavioral score. Gate remains fixed at2sigma.

Before starting Add, the two bounded dose rounds are defined as the requested literal grid(-0.5,-1,-2), then a residual-scaled regime only if needed. No progress across both regimes ends this experiment. A healthy collapse stops further dose escalation. Matched random controls receive the same per-layer norms. Total arm starts, including failed startup/partial attempts, remain capped12. add_m05 started02:31 UTC.

Independent Gate semantic review:0/4 changed fs+ payloads provide useful corrective action; all remain false completion answers. The altered third text response remains correct. Gate text health3/3.

## Literal Add -0.5 complete, 02:42 UTC
add_m05 completed56 GUI+3 text probes. All590 targeted layer rows changed; the realized norm is within0.1% of the requested0.7071 per row. False-completion answer15/16, true-completion answer12/16, healthy valid nonanswer24/24, invalid0/56: unchanged from baseline. Ten fs+ outputs and ten protected GUI outputs change their full token sequences. Four protected tool payloads differ: three completion-answer wordings and one system-menu click moving from x985 to975 at y10. Independent screenshot-grounded review confirms both coordinates open the same menu,0/24 harmful healthy actions,0/16 harmful true-completion outputs,0/10 useful fs+ corrections, and3/3 coherent text probes. No candidate. add_m1 launched02:42 UTC with the same contexts/seeds and twice the literal amplitude.

## Literal Add -1 complete, 02:51 UTC
add_m1 completed56 GUI+3 texts in509.52 seconds, exit0. All590 targeted rows changed; aggregate realized delta norm834.4982 versus requested834.3860. Counts again fs+answer15/16, true-completion answer12/16, healthy valid nonanswer24/24, invalid0/56. Full-token agreement:7/16 fs+,15/24 healthy,10/16 true-completion. Protected nonanswer tool changes comprise two system-menu clicks x985→975,y10, the same coordinate change already independently validated. Three completion answers are reformulated. Text controls1–2 are identical,3 differs and is under semantic review. No candidate; add_m2 started02:52 UTC, the last literal dose.

Independent add_m1 review confirms0/24 harmful healthy actions,0/16 harmful true-completion outputs,0/8 useful changed fs+ actions, and3/3 coherent texts.

## Literal grid complete, 03:01 UTC
add_m2 completed56 GUI+3 texts in472.34 seconds, exit0. All590 targeted rows changed; realized aggregate norm1668.8127 versus requested1668.7720. Counts remain fs+answer15/16, true-completion answer12/16, healthy valid nonanswer24/24, invalid0/56. Full-token agreement5/16 fs+,12/24 healthy,9/16 true-completion. Three healthy clicks change to the system menu at975,12, including one formerly choosing Activities; both routes were established as valid baseline actions. Three true-completion answer payloads change wording. Independent semantic review continues. The literal grid has no false-completion decision benefit at any of the three doses. random_m2 launched03:00 UTC with the pre-generated orthonormal random axes and the same2.8284 target norm per layer.

Independent add_m2 semantic review confirms0/24 harmful healthy actions,0/16 harmful true-completion outputs (three changed payloads across two contexts), no useful fs+ correction, and3/3 coherent texts. A changed false Budget answer also invents a different Minivan price; this is a wording regression, not progress.

## Independent quantitative verification of completed literal phase
Fresh reviewer verdict RAN/PASSED/CORRECT for baseline_v1,gate_v1,add_m05,add_m1,add_m2. Each has56 GUI+3 texts, exactly7 frozen contexts×8 seeds, matching row metadata and prompt lengths, no truncation/error, and END followed by the expected end-of-message token. Every paired answer decision is unchanged, not merely the aggregate rate. All job manifest hashes and axis hashes match; source archives account for the failed startup/partial Gate attempts, which are excluded from completed-arm conclusions. The reviewer checked real activation counters and the comparison hashes. Screenshot semantics were handled by a separate reviewer. No online rollout or checkpoint equivalence has run.

## Matched random literal control complete, 03:09 UTC
random_m2 completed56 GUI+3 texts in489.52 seconds, exit0. Every590 target rows changed; realized norm1668.8013 versus learned Add-2 norm1668.8127, effectively matched. Counts remain15/16 fs+answer,12/16 true-completion answer,24/24 valid healthy nonanswer,0/56 invalid. Healthy actions24/24 agree with baseline. Random perturbation changes text but supplies no false-completion rate advantage. Independent semantic review continues.

scaled_m05 started03:09 UTC. This is Add-0.5 times each selected layer's fixed median CAL residual norm, so the sum of its two orthogonal axes has norm70.71% of that layer's typical residual. A matched scaled random arm will follow. This is the second and last dose regime; without protected improvement, the no-progress stop applies and no weight compilation is justified.

Independent random_m2 semantic review confirms no useful correction among twelve changed fs+ actions (eleven false-answer wordings and one scroll coordinate change), four harmless true-completion answer reformulations, all24 healthy actions unchanged, and3/3 correct texts. Quantitative review confirms every paired answer decision unchanged and learned/random realized GUI norms matched within0.00125%.

## Residual-scaled Add and safety stop, 03:20 UTC

scaled_m05 completed56 GUI+3 text outputs in517.51 seconds, exit0. All590 targeted rows changed. Requested aggregate delta norm10365.9990; realized10365.8364. False-completion answer remains15/16; true-completion answer11/16 versus12/16 baseline; healthy valid nonanswer24/24; no invalid/truncated GUI output. Full-token agreement is2/16 fs+,11/24 healthy,3/16 true-completion. The three deterministic text continuations are corrupted after END: arithmetic no longer answers42, the French translation starts with an unrelated Greek fragment, and the water response mixes languages and loses the requested list.

The matched random residual-scaled job was launched before the comparison text was read. Once the text collapse was observed, only owned launcher PID398692 was sent SIGTERM. It exited143 before any output JSONL or completed marker. The stopped attempt remains in the budget ledger and is not a completed control. No further dose, all-position pilot, weight compilation, equivalence test, upload or online rollout is justified by these data. The completed matched random literal control is retained.

The causal search ends because neither dose regime supplied a protected improvement and the strong regime violates text health. The result is a bounded negative result for these axes, layers, doses and held-out DIAG contexts, not a universal impossibility claim about TACT or Holo.

Independent scaled_m05 semantic audit: fourteen changed fs+ payloads (thirteen false answers and one equivalent scroll), zero useful correction; four changed healthy clicks, three equivalent and one nonproductive no-op; nine changed true-completion payloads, eight correct reformulations and one harmless save replacing the final answer; three harmful text regressions. No task state is claimed improved.

## Final verification and accounting

Fresh quantitative reviewer: RAN/PASSED/CORRECT for generation integrity of all seven completed arms. All original metadata, prompt lengths, keys/seeds, JSON schema and output termination checks pass. Every fs+ answer decision is unchanged per seed. The strong dose has exactly one true-completion answer-to-nonanswer flip, Calc seed4103; the independent semantic reviewer identifies its harmless Ctrl+S. Integrity PASS is not an efficacy PASS.

Ten arm starts are retained in budget.jsonl: seven completed arms, one failed baseline startup, one partial Gate, one interrupted random-scaled startup. Completed arms:392 GUI+21 text=413 outputs. Partial Gate:8 GUI. Total retained:400 GUI+21 text=421 outputs. Extraction used270 forwards; the separate explanatory Gate probe used seven original pilot states. No completed output exists for the failed baseline or interrupted random-scaled job. The interrupted launcher/process group is gone and the owned GPU lock was independently checked free after termination; no owned research server/watchdog is left running.

## Reproduction and archive

The frozen v3 manifest, axes, per-arm job/done records, complete outputs, comparisons, source archives and independent reviews are retained in `/workspace/astra/astra-tact/`, mirrored as small artifacts in `holo-neurochir/astra-tact/` on orbit. Full hidden-state caches remain on the pod. Superseded v2 metrics/axes/manifest are explicitly under `proxy_v2/`; they must not be combined with final v3 behavior.

`extract.py` replays the frozen manifest at the actual END token; `axes.py` computes the documented within-task axes and grouped diagnostics; `steer.py` runs the boundary-only causal pilot through `launch.sh` and the fleet GPU allocator; `compare.py` checks paired output identities. `prepare.py` and `freeze_audit.py` document the earlier label construction/audit transitions and must not silently rebuild the final manifest. Preserve existing outputs and the ten-start ledger. Environment versions are in the two `*.environment.json` files. Each arm records manifest, axis, runner and reference-generation hashes; earlier runner versions are archived under their original hashes.

Frozen manifest SHA256: `cdef6ea3b55406a1bd7574b3840a632ffa72c5ee39f4efbe5756b9a1b577d2f7`. Axes SHA256: `eff834646fa65134a545094c67745dbcb560b63b82f170a047d86f7dde9c1a44`. Original model snapshot: `8c88265a5a159bfd1492db9243733dd2e6e04a6e`. Local shared checkout had pre-existing changes and rejected pull --rebase; fetch confirmed HEAD=origin/main at session start. Only this research archive and an additive state/log entry are supplied locally; shared source and sibling experiments are untouched, and fleet Git archival remains with ares.
