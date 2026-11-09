# First Holo4 Guard repair — independent bounded review

Reviewed read-only on 2026-11-08. Scope is the single `guard`, `k=0` branch for `libreoffice_calc/37608790-6147-45d0-9f20-1137bb35703d`. No model endpoint or VM was called, and no runner or result was modified.

## Verdict

**Verified genuine official success for this branch.** The journaled `score=1.0` is the value returned after the configured OSWorld evaluator loaded the saved workbook and compared its sheet data with the official gold workbook. The branch contains a real corrective continuation after a valid Guard refusal, not a no-op or replay-only pass. Replay and boundary fidelity pass the registered thresholds, and the logs show no setup, download, action, save, getter, model, or evaluator failure.

This establishes one successful Guard-triggered Holo4 continuation. The first matched Holo4 control (`k=0`) subsequently completed with official score 0, so the observed first pair is Guard 1 versus control 0. It does **not** establish a treatment effect or repair rate: `k=1` and the remaining registered branches were incomplete at review time.

## Evidence chain

1. The durable branch result (`/home/orbit/osw/rescue_bench/guard/libreoffice_calc_37608790-6147-45d0-9f20-1137bb35703d_k0/attempt_1/result.json`, not in the repository) records the original episode at `recorded_score=0`, the new official `score=1`, `finished_by_agent=true`, 17 valid model calls, zero model-call errors, and no infeasibility decline. Its SHA-256 at review was `711bd15c06f7babfa5e9200f4476787eb4006f3dc94c1909859203d683f30eef`.
2. The Guard journal (`/home/orbit/osw/rescue_bench/guard/libreoffice_calc_37608790-6147-45d0-9f20-1137bb35703d_k0/attempt_1/guard.jsonl`, not in the repository) contains one valid passive-Claude verdict, `INCOMPLETE`, with no verifier error. It identifies the concrete defect: the original combined data had been overwritten in A, outputs were shifted left, and D was empty. Decision is `refused` and the feedback directs restoration of A and placement into B/C/D.
3. The continuation performed state-changing work. The first new action was `Ctrl+Z`, followed by writes of three formulas into B2, C2, and D2, selection/copy of B2:D2, paste into B3:D22, and save. The formulas explicitly derive first name, last name, and rank from A, preserving A. These 16 nonterminal actions plus the terminal answer are recorded in `/home/orbit/osw/rescue_bench/guard/libreoffice_calc_37608790-6147-45d0-9f20-1137bb35703d_k0/attempt_1/frames/calls.jsonl` (not in the repository); `/home/orbit/osw/rescue_bench/full0.log` (not in the repository) records successful controller execution (`returncode=0`) after the refusal.
4. The official task config requires `compare_table` against `Employee_Roles_and_Ranks_gold.xlsx`, with a `sheet_data` rule comparing result sheet 0 to expected sheet 0. See the task config (`/home/orbit/osw/rtg/Env/OSWorld/evaluation_examples/examples/libreoffice_calc/37608790-6147-45d0-9f20-1137bb35703d.json`, not in the repository). The frozen evaluator implements that rule as rounded DataFrame equality, `sheet1.equals(sheet2)`, in table.py (`/home/orbit/osw/rtg/Env/OSWorld/desktop_env/evaluators/metrics/table.py:328`, not in the repository). No alternate or relaxed criterion appears in this task configuration.
5. Immediately before the journaled success, `full0.log` records successful postconfig window activation and save, successful retrieval of the 7191-byte result workbook, and successful evaluator loading of sheet `工作表1`. The next branch record is `score: 1.0`, `error: null`. This rules out a missing result, failed download, failed setup, or evaluator-load fallback as the source of the one.
6. Replay fidelity is valid: seven replay differences have maximum `0.0020748304`, boundary difference is `0.0000217966`, and both `replay_valid` and `strict_replay_valid` are true under the registered `0.05` threshold. The original seven actions were replayed before the answer boundary; the corrective actions begin only after the refusal.
7. The same successful row is durably journaled once in `/home/orbit/osw/rescue_bench/branches.s0-of-2.jsonl` (not in the repository). The row agrees with `result.json` on task, arm, K, score, refusal, call counts, fidelity values, actions, and final answer.

## First matched Holo4 control (`k=0`)

The durable control result (`/home/orbit/osw/rescue_bench/control/libreoffice_calc_37608790-6147-45d0-9f20-1137bb35703d_k0/attempt_1/result.json`, not in the repository) records official `score=0.0`, `error` absent, `finished_by_agent=true`, one valid model call, and zero model-call errors. Its SHA-256 at review was `06be56492a241a266b46a54e0f8ebcb7b266cf6e17246ef1683c9b55e60aa4a5`.

This control used the same task, original eight-step recording, branch boundary 7, model, v2 prompt, prompt SHA-256, 20-step cap, and official evaluator protocol. Its replay max difference was `0.0020769285` and boundary difference `0.0000206165`; both registered validity flags are true and closely match the treated branch's fidelity values.

There was no Guard call or feedback: `gate=null`, `guard_summary=null`, and `escalated=false`. The sole Holo4 output was an immediate `answer`, with `new_steps=0` and tools `['answer']`; control calls.jsonl (`/home/orbit/osw/rescue_bench/control/libreoffice_calc_37608790-6147-45d0-9f20-1137bb35703d_k0/attempt_1/frames/calls.jsonl`, not in the repository) contains that single valid call. Thus the control made no corrective desktop action after replay.

`/home/orbit/osw/rescue_bench/full0.log` (not in the repository) shows normal setup/open, successful official postconfig save, successful retrieval of the 6155-byte workbook, successful evaluator loading of sheet `工作表1`, then the branch row `score: 0.0`, `error: null`. The same result is journaled once in `branches.s0-of-2.jsonl`. The following `resource gate closed` warning occurs after this completed and journaled evaluation; it stopped the next launch and is not a failure or missing score for this control.

The only completed within-K comparison at this review point is therefore:

| Task | K | Guard | Control |
|---|---:|---:|---:|
| Calc 37608790… | 0 | 1.0 | 0.0 |

This is a verified paired observation, not an estimate. K=1 must complete before forming the registered per-episode K mean.

## Holo 3.1 reference, without trajectory inspection

`/home/orbit/projects/ComputerUseHackaton/holo-neurochir/rescue_bench/HOLO31_REFERENCE.json` (not in the repository) reports, for this same task, Guard scores `[0.0, 0.0]` and no-Guard scores `[0.0, 0.0]`, with no exclusion. The file itself warns that this contemporary Holo 3.1 measure is a historical reference and **not a randomized third arm** for the Holo4 rescue benchmark. It supports the narrow statement that the referenced Holo 3.1 continuations did not repair this task; it does not support a causal Holo4-versus-Holo3.1 claim.

## Bounds on interpretation

- The official success verifies final workbook sheet values, including preservation and populated columns as represented by the gold workbook. It does not independently score the model's prose explanation or formula elegance.
- The first treated branch can be compared descriptively with its completed `k=0` control: 1 versus 0 under matching replay validity and official scoring. Any claim about Guard lift, episode-level repair, repair rate, or statistical significance must wait for K=1 and the registered paired cohort analysis.
