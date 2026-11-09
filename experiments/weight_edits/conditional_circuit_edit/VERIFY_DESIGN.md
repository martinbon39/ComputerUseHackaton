# Independent design audit — semantic_l19_d1

Audited read-only from the five frozen files requested. No raw episodes, heldout content, GPU, model run, or candidate file was opened. Input SHA256 values: `derive.py` 1a5d38052181b291435cb8fc62e3a0d06be48f834c3d865403c4366ae68ebe04; `manifest.json` d5d4c70f60334a22c36c39a5a9f1647592068aa5fa7b44ec23fd5012092de5c8; `detector_design.json` 27dcaab0dce30bc732fa7d9a1751def0874c01cd73d5374e2ca507de4c1effb8; `spec.json` c146269ea1a25cdef700bcf70f95d8ab9ff82c71c0a7122c807ed3fa9bf09e8d; `algebra.json` 62546efca7fad037c9b969e498042d99b18f716475295ec221ff53d5b66257bb.

## Verdict

**RAN:** analytic review of indexing, population construction, current split disjointness, leave-one-positive-task-out computation, and candidate state coefficients.

**PASSED:** the stated `X[j] predicts ids[j]` contract is used correctly. `end` is the index of the first `</think>` token and `x[target] = X[end]` is therefore the state immediately before predicting `</think>`, not the post-`</think>` state. The `len(X)=len(ids)+1` and `tail_state_offset==1` assertions support this alignment.

**PASSED for the current manifest:** design (6 tasks), screen (5 unique tasks), heldout (9), verification (6), and reserve (45) are pairwise task-disjoint. The disclosed candidate state checks use exactly the four positive design tasks, two healthy design tasks, and six verification/verified-done task pairs; none overlaps screen, heldout, or reserve.

**CORRECT, with limits:** this is a reasonable bounded experimental candidate. The captured evidence does not validate it as a useful verification circuit. Generation and semantic review remain necessary; the risks below are reasons to measure, not speculative vetoes.

## Findings

1. **LOCO is valid for these four positives, but narrower than a general task-group implementation.** Each positive belongs to a distinct task. Deleting `P[held]` therefore removes the held positive task, and `bg_keep` removes every background row from that task. `N` needs no same-task removal in this manifest because positive and negative task IDs are disjoint. If repeated positive rows per task are later admitted, `np.delete(P, held)` would leak sibling positives; the present result does not have that defect.

2. **The reported LOCO statistic validates the base detector procedure, not the exact final candidate threshold.** `detector_design.json` records L19-end `a=0.2111849821`, `b=1.0526263411`; the candidate instead freezes `a=0.5803486122=max negative terminal ratio+0.1`, `b=0.8303486122`, `k=16`. LOCO recomputes a 0.995-background threshold for each fold. Its four positive margins are all above zero, which supports task-level separation, but it is not cross-validation of the candidate's exact `max-negative+0.1` policy, dose, or writer.

3. **The detector is not a generic end-of-reasoning detector.** Every row is sampled immediately before `</think>`. Positives are unverified terminal-answer states (two fs+, two fs-); negatives include healthy non-answer terminals, concrete verification-action terminals, and final answers after successful verification. The evidence supports a captured-state discriminator for *unverified closing versus those negative states*. It does not distinguish false from true completion: both training fs- terminals activate strongly.

4. **Captured gating is strong at the selected end states and mostly quiet in the sampled negatives.** Candidate coefficients are 0.789–0.984 for the four unverified terminal positives. Negative-terminal absolute maximum is 0.0588; sampled background and all captured prefill are small (prefill absolute maximum 0.0255). Six original verified-done trajectories remain off in reasoning (maximum absolute 0.0588). This supports the intended timing on these captures only.

5. **Self-deactivation is not causally demonstrated.** Verified-done captures come from original successful episodes. They show that already-verified reasoning lies in an off region; they do not show that adding this writer causes a newly generated trajectory to enter that region, remain there, or avoid reactivation.

6. **There is one concrete non-end reactivation on a protected training fs- trajectory.** `libreoffice_impress/ef9d12bd...` has a JSON-position coefficient of 0.21485 and active positions `[117,334]`. At `alpha=residual_norm`, that is an added writer norm near 0.215 residual norms during JSON. This falsifies any claim that the circuit is active only at the reasoning terminus and creates a real schema/content/protection risk. It does not by itself invalidate a bounded generation test; strict parsing and fs- protection are the correct arbiters.

7. **The semantic writer is evidence-based but not mechanistically validated.** It is the unit contrast between early residual averages from six actual successful verification steps and four unverified terminal-positive reasonings. That is better grounded than a synthetic prefix, but it may encode task/domain/style differences, and it has no writer-specific LOCO result. Captured direction provenance does not prove it will produce a relevant observation or correction when written at L19.

8. **Exclusion enforcement is evidenced by the manifest, not enforced inside `derive.py`.** The derivation loads `capture01/metadata.json` directly and never loads or hashes `manifest.json`, nor asserts capture task IDs against screen/heldout/reserve. The disclosed IDs are clean, so there is no observed contamination. A claim of machine-enforced exclusion or exact manifest-to-capture binding would not be supported by these five files alone.

9. **The candidate remains a large intervention despite only two reassigned neurons.** End coefficients near one and `alpha=10.8936` write roughly one mean residual norm. Removed native contribution is small (maximum norm 0.1144), which supports the neuron choice, but it does not constrain the new writer's behavioral effect.

## What generation must decide

Generation must determine whether the L19 write delays `</think>` into a concrete evidence-seeking action, whether true finishes and healthy actions remain protected, whether JSON reactivation causes invalid or altered tool calls, and whether generated post-verification states actually deactivate the gate. No captured coefficient establishes those outcomes. Equal-norm random-writer comparison is still required to attribute any effect to writer semantics rather than a large terminal perturbation.

**NOT RUN:** GPU/model behavior, heldout evaluation, random control, online task execution, and independent semantic grading of generated actions.

## Addendum — paired semantic writer, `paired_l19_k48_d1`

Reviewed after the writer revision and before any reported patched generation. Inputs: `build_circuit.py` SHA256 `fbe88ee39fec76236d8acde829ad3e656d7e9b715a7abbdc76561abf06fc6e29`; paired spec `ae03a744e52dbbd080cc9e2f440cf0d741279d2041317e5623ce6f1b9d5bcebf`; paired algebra `59cdabb9107439fa71bbc09130850385c4c561b305ac3a311a6b8efcfce2baf6`.

**PAIRING CONFIRMED.** For each `task_id`, the code stores one early-reasoning mean for `verification` and one for `verified_done`, asserts exactly six complete task pairs, computes each within-task difference `verification - verified_done`, averages the six differences, and normalizes once. Dictionary pairing by task ID prevents cross-task row-order mismatches. This materially removes static task/domain offsets from the prior writer contrast. It intentionally retains the within-task phase distinction and therefore still does not prove that the direction will cause a useful check.

**EXCLUSIONS UNCHANGED.** `manifest.json` remains byte-identical to the audited version (SHA256 `d5d4c70f60334a22c36c39a5a9f1647592068aa5fa7b44ec23fd5012092de5c8`). Design, screen, heldout, verification, and reserve sets remain pairwise task-disjoint. The revised builder uses only the existing `capture01`; it performs no new data/model pass. The earlier enforcement caveat remains: `build_circuit.py` does not itself load or hash the manifest.

**K=48 effect.** Captured off-state leakage falls sharply: negative-terminal absolute maximum `0.003825`, prefill absolute maximum `0.0000493`, while positive end coefficients remain `0.792–0.948`. The known protected fs- JSON reactivation remains (`0.22174` at position 334), so sharper gating does not remove that concrete generation risk.

**Verdict unchanged:** reasonable first bounded experimental arm; writer confound is improved, while behavioral usefulness, fs- protection, JSON validity, causal self-deactivation, and semantic specificity remain generation questions. No screen outcome was used in the construction evidence reviewed here.
