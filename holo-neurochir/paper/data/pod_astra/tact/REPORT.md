# TACT on Holo-3.1-4B

Owner: astra-tact. Started 2026-11-08 01:32 UTC.

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

Final frozen construction:239 states,219CAL/13OT/7OA,58 tasks. Both axes now use the paper's strict average of within-task differences. Only two tasks have OT/CAL pairs and one has OA/CAL pairs. OA grouped CV is therefore not estimable and no OA generalization AUROC is reported. No task-disjoint OA pilot can be supported by this pool. The seven pilot contexts comprise two visibly false completions (wrong Budget month; wrong pivot-sheet name), two real completions, and three healthy actions, across seven excluded task IDs. Former pilot tasks remain excluded. Labels are now frozen; no behavioral outputs were inspected before this revision. Nine additional states were replayed successfully, for270 actual forwards in total.

Final OT grouped out-of-fold AUROC: best pooled0.98279; position(step,log context)0.88303; position+reasoning length0.94872. Best mean within-task AUROC0.9375 versus position0.5625, based on just two paired tasks. Top10 layers chosen by that development-CV mean:19,30,29,31,21,22,23,24,25,26 (zero-based). This selection is not an independent performance estimate. Typical CAL residual norms on those layers span12.06–49.87. Thus a literal Add strength-0.5 adds norm0.707 per layer, roughly1.4–5.9% of the residual norm; residual-scaled doses are a materially different regime. No causal conclusion follows from detection. Baseline vLLM generation launched02:07:32 UTC, with eight fresh paired seeds per context and three deterministic text probes. No model weights edited.
