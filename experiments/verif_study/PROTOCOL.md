# Final-screen verifier study — protocol frozen before inference

Registered 2026-11-08, before model responses. Owner: verif-study; coordinator: ares.

Question: can original Holo-3.1-4B detect its own premature success when explicitly asked to verify every task requirement from the final screenshot?

## Corpus and ground truth

Read-only sources: `~/osw/results_diag`, `~/osw/results_diag2`, `~/osw/results_diag_extra_gh/pass1`, `~/osw/results_diag_extra_gh/pass2`. Use one episode per task and source pass, deterministically deduplicated. Keep completed trajectories whose final tool is `answer`. Official `result.txt` score 0 defines false success; score 1 defines true success. Exclude and count partial scores, infeasible tasks (`evaluator.func` contains `infeasible`), non-answer episodes, missing or malformed evidence. Task instructions come from the OSWorld task JSON. No new rollouts or source-data modifications.

Use all eligible episodes if feasible within the deadline; report any shortfall from 30 false and 60 true successes without expanding sources. Screens come from the final trajectory screenshot after the final action when available, otherwise the latest available step screenshot. Store paths and SHA256 hashes. Do not send scores, previous answers, trajectory reasoning, evaluator code, or feasibility labels to the verifier.

## Intervention

One user message: task text and original final PNG, with the exact prompt:

> Task: <instruction>. Here is the final screen. List every requirement of the task, then for each say whether the screen shows it is satisfied (yes / no / cannot tell). Finally answer VERDICT: COMPLETE or INCOMPLETE.

V1: the shared original Holo-3.1-4B service, pod port 8000 only; plain text/image completion, thinking enabled, no agent JSON schema and no tool definitions. Primary: one T=0 output per episode. Stability: three independent T=0.8 outputs per episode with recorded seeds. No tuning on observed outcomes. Preserve complete requests (image referenced by hash) and responses including reasoning and stop reason. V2 only if a stronger usable VLM already exists locally without disturbing another server; otherwise explicitly NOT RUN.

## Measures

Primary rates: INCOMPLETE / all false-success episodes, and INCOMPLETE / all true-success episodes, each with 95% Wilson intervals. Also show COMPLETE, missing/malformed verdicts, truncated/error outputs and valid-only sensitivity. Do not silently count missing verdicts as COMPLETE. For T=0.8 show each replicate and three-vote majority, unanimity, pairwise disagreement and agreement with T=0. Use episode denominators and disclose repeated tasks (Wilson intervals do not account for task clustering); compute task-cluster bootstrap intervals as a sensitivity if useful. Extract counts of explicit requirement yes/no/cannot tell decisions, distinguish missing/ambiguous formatting and do not equate these with independently verified requirement-level accuracy.

Simulation: blocking INCOMPLETE alone repairs zero tasks. Show zero-repair net bounds including potential damage to true successes, then a conditional extrapolation using the observed online-branch repair rate with its denominator and uncertainty. This is not measured OSWorld improvement, and evaluation on selected answer episodes is not the full benchmark.

## Budget, stopping and audit

At most four concurrent inference requests (initial pilot one); no new model downloads, weight editing, rollouts, or service changes. One representative pilot before full launch, then a fixed finite episode × four-request schedule, with at most one retry for transport failures. Freeze exact request count after inventory. Stop at 09:45 UTC to leave audit time before 10:30 UTC, or after two consecutive 10-minute windows with no completed request; retain all failed/partial evidence. No outcome-driven resampling or prompt adjustment. An independent checker must recalculate corpus labels, scores and intervals from source files and raw responses before final delivery. Main session alone sends short updates to ares and copies artifacts to `/workspace/astra/verif-study/` on the pod.
