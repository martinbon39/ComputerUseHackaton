# Paired branching on recorded OSWorld episodes — pilot report (2026-11-08)

## Why
With ~45 complete episodes per arm, the standard error of a paired difference in success is ~7-8 points: no realistic
gain is detectable. Branching from recorded states gives several paired continuations per episode for a fraction of
the cost of full episodes.

## Method
Harness: `holo-neurochir/osworld/branch_runner.py` (launched through `osworld/run_branch.sh`, which reuses
`~/osw/run_osw.sh`'s exact environment; OSWorld Docker + KVM on orbit, one VM per process).
1. Take a recorded baseline episode (run_holo task dir) that ends with `answer`.
2. In a fresh VM of the same task (`env.reset`, 60 s settle, as run_holo), replay the recorded actions of steps
   0..t−1 at the recorded pace (sleep until the original inter-step gap, cap 20 s), rebuilding the agent history as
   `HoloComputerAgent.run` does: fresh screenshot, recorded assistant JSON, fresh tool output.
3. From that state, the model continues for at most 15 new steps (harness-exact call: v2 prompt, schema under
   structured outputs, T=0.8, top_p 0.9, image budget 3). An `answer` is sent to OSWorld as DONE (or FAIL for a
   declared infeasibility), then the task evaluator scores the final state.
4. Fidelity: every replayed screenshot is compared with the recorded one (mean absolute pixel difference on a
   480×270 resize). A branch is valid when the maximum difference is ≤ 0.05 (`replay_valid`).
Pilot: branch at t−1 = the recorded final-answer step; K=2 continuations per arm per episode. Both arms served by
Modal (H100, vLLM 0.23.0, same image): original = `Holo-3.1-4B-modal-orig` (account 1), candidate =
`Holo-3.1-4B-merge_cua_b050` (account 2). A first launch of the original arm on the pod (H200, port 8000) was
stopped before any branch finished, to remove the server confound (kept in `orig_pod_aborted/`).

## Replay validation (precondition: ≥ 9/10)
10 distinct true successes of the confirm baseline (≤ 20 steps), replayed in full (including the recorded answer):
- unpaced replay: 7/10 (`~/osw/branch_valid/`): VS Code extension install and terminal commands ran faster than
  the original episode (which waited 4–9 s per model call) and diverged;
- paced replay: **9/10** (`~/osw/branch_valid2/`); max pixel difference ≤ 0.005 on the 9 successes. The failure,
  `os/5c1075ca`, diverges for real (difference 0.21): the task looks non-deterministic under replay.
Mean cost of a full paced replay: 166 s.

## Pilot results (`~/osw/branch_pilot/{orig,cand}/branches.jsonl`, 20 branches, 0 errors)
| Episode (recorded outcome) | replayed steps | original (K=2) | merge_cua_b050 (K=2) |
|---|---|---|---|
| gimp/fbb548ca (false success) | 10 | **1/2** success (7 and 2 new steps) | 0/2 (answers after 3, 2) |
| libreoffice_writer/6f81754e (false success) | 23 | 0/2 (answers after 2, 3) | 0/2 (answers after 7, 3) |
| chrome/6c4c23a1 (false success) | 15 | 0/2 — **invalid replay** (diff 0.49 from step 0, dynamic web page) | 0/2 — invalid |
| os/23393935 (true success) | 8 | 2/2 (answers at once) | 2/2 (0 and 3 new steps) |
| thunderbird/f201fbc3 (true success) | 3 | 2/2 (answers at once) | 2/2 (answers at once) |
| **total** | | **5/10** (8 answered) | **4/10** (8 answered) |

Cost: 251 s per branch on average (median 227 s; 135 s with 3 replayed steps, 340–360 s with 23). Replay
dominates; an episode with K=2 per arm costs ~17 VM-minutes.

## Lessons
1. A fidelity filter is required: 1 episode in 5 (dynamic web content) diverges from the first step.
2. Branching a true success at t−1 carries almost no information: the model concludes again at once. The signal is
   in false-success and failed episodes; branching earlier (t−3) leaves room to change the plan.
3. The mechanism works: on gimp/fbb548ca an original continuation recovers a task the recorded episode had failed —
   the paired within-episode signal the design is meant to measure.
4. No advantage for merge_cua_b050 on this pilot (4/10 vs 5/10; n is far too small to conclude either way).

## Next (decided by ares, 04:45 UTC)
No generalisation now. If the 120-task test of merge_cua_b050 vs original (Modal) shows Δ > +3 points, branch every
baseline false success of confirm and test with the fidelity filter at t−1 and t−3
(`--branch_back 0` / `--branch_back 2`), K=2 per arm (~40 episodes, ~160 branches, ~2 h 50 on 4 VMs); otherwise stop.
