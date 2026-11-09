# astra-stuck — Holo-3.1-4B causal stuck pilot

Status: original reference complete and independently audited; first intervention rejected by the exact health bound. Three lots reserved of20 (one pre-generation resource abort, one complete original, one rejected candidate). No admissible causal candidate or weight edits. All results in this experiment are exploratory. Model: Hcompany/Holo-3.1-4B. Diagnostic tasks only; test split and its results have not been read.

## Frozen data and design

The established OSWorld diagnosis is taken as given. This experiment targets scored 50-step failures at zero-based t>=25, labeled positive when the current recorded action repeats the previous action or the current screenshot is almost unchanged from the previous screenshot. Health controls require successful nonterminal steps, a different recorded action and a changed prior screen. See PROTOCOL.md and PROTOCOL_V2.md for exact action/screen thresholds.

The initial same-domain pairing was infeasible: the first valid frozen snapshot had only3 pairs in one connected task component, with no construction or screen component. It was stopped before any direction or GPU work. An earlier empty discovery artifact arose from assuming a flat trajectory directory; it was retained, and discovery now fails on empty input. Neither artifact is efficacy evidence.

V2 was declared before direction calculation or generated outcomes. It permits cross-domain pairs, retaining same tool, same pass, absolute step difference<=3 and disjoint task-pair assignments. Domain is therefore a remaining confound. This design is exploratory and does not establish generalization to arbitrary stalled-screen states.

Immutable manifest SHA256: `39b27a41ee0fbb76d06fa2eedd5591a13fcc0c099ab05b89c3d5c8cd441f91dc`.

| Frozen quantity | Count |
|---|---:|
| stuck+ contexts / tasks |84 /15|
| successful late controls / tasks |16 /5|
| true-healthy controls |10|
| matched row pairs / disjoint task pairs |13 /5|
| construction groups / row pairs |3 /6|
| screen groups / row pairs |1 /6|
| reserved confirmation groups / row pairs |1 /1|

All copied trajectories, replay metadata, activation arrays and row labels were independently reproduced from the immutable snapshot with zero discrepancies. Fresh production-log audit covers119 completed diag tasks and21 completed diag2 tasks, with zero logged env-step exclusions. Discovered tasks absent from the frozen completed-task audit are excluded. Every task and all of its passes belong to a single assignment.

Screen selects three repeated-action stuck+ contexts and three true-healthy controls, with four fixed seeds per context. The screen task and its health task are excluded from direction construction. Its repeated-action selection is deliberate and is not a representative estimate for all84 stuck+ rows. Confirmation is untouched by direction fitting and candidate selection.

## Directions and checks

Paired mean differences use equal total weight per construction task pair. Residual and MLP prefill directions were computed; fixed intervention sites are zero-based L16, L24 and L16/L24/L28. The three-group leave-one-task-pair-out CV is descriptive only. Direction AUROC is not causal evidence.

| Site | L16 AUROC | L24 AUROC | L28 AUROC |
|---|---:|---:|---:|
| residual |0.7500|0.6944|0.5833|
| MLP |0.6944|0.7500|0.5000|

The position baseline has AUROC0.5000. Context length has signed AUROC0.3333 (0.6667 after reversing its sign); residual L16 therefore exceeds that oriented baseline by only0.0833 in this tiny sample. These figures use12 OOF rows from three construction groups. Full per-layer metrics, direction hashes and train-task provenance are in direction_summary.json. Nuisance regression was not run: the tiny construction set supports stage matching and baseline reporting, not a reliable fitted correction.

## Behavioral gate and budget

Original and intervention generate native thinking with temperature0.8, top_p0.9, top_k20, max3072 tokens and seeds6100–6103. Escape means a valid non-answer action different from the preceding action. Health means a valid non-answer close to the recorded action. Invalid/truncated outputs remain in denominators.

Required: escape increases at least30points, health decreases at most5points, invalid/truncated rises at most5points. The separate common false-success gate remains required for admission; no stuck-only result is called a common-gate success. All results before40 admissible fs+ remain exploratory.

Budget cap20 lots, charged before allocation, including failures/resumes. Two rounds without protection-compatible escape improvement stop screening. A baseline escape rate above70% makes the fixed30-point target impossible for this subset. One own GPU process, allocator cap12.5GB, process guard14.5GB, mandatory STOP_GPU checks and20s inter-lot cooldown. Production vLLM is untouched.

## Verification and limits

RAN/PASSED: independent CPU audit of immutable V2 row labels, source hashes, activation mapping, task-disjoint pairing, assignments and exclusions.

CORRECT: recorded labels and frozen split satisfy the explicit V2 definitions. The initial strict protocol failed feasibility and was not treated as an experiment.

RAN/PASSED: the generated baseline and independent raw-output audit. Signed-addition screening is in progress. NOT RUN: reserved confirmation, common false-success checks, weight compilation, random-direction control and online task evaluation.

No OSWorld score improvement is claimed. Patch spec: null. Weights changed:0.

## Execution log

- Lot1: reserved, aborted by fail-closed guard after ownPID was absent in three NVML polls; no model load and no generations. Root-cause hypothesis: CUDA allocator setup without an allocation does not register a process memory entry. The explicit one-element CUDA allocation was independently checked and the same runtime reproduction passed in lot2. This failure remains charged.

- Lot2: started19:27UTC; memory watcher readiness and model load succeeded after explicit one-element CUDA allocation. Original generation completed24/24; see the behavioral results.

## Behavioral results — in progress

Original reference:24/24 generations complete, strict/executable24/24, errors/truncations/answers0. Stuck+ valid escape4/12 (33.33%); healthy action preservation12/12 (100%). First stuck context t25 escapes4/4 naturally; t27 and t29 escape0/4 each. All24 context/sample/seed keys independently audited from raw text. Original JSONL SHA2567217fc666e89029b2747a038029c91000bc5495e69c71d418787ccc870543712. Peak process13.144948736GB.

Lot3, residual negative addition L16 (alpha=-1, scale2.580998182296753): REJECTED_PROTECTION_UNREACHABLE. Generated5/24 planned outputs, all healthy controls. One action changed from Save As to Export. Even perfect remaining health outputs can reach at most11/12=91.67%, below required95%; full efficacy is NOT ESTIMATED. Observed peak process13.270777856GB. Candidate raw outputs and mathematical rejection marker retained. No positive stuck context was generated for this candidate.
