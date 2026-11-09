# Selective RegMean — no admissible candidate after two paired precision arms

Started 2026-11-08 02:19 UTC. Holo snapshot 8c88265a5a159bfd1492db9243733dd2e6e04a6e.

Only static checkpoint weights may change. No gradients, adapters, prompts or production harness changes. The user-prescribed gates supersede the earlier stricter fleet gate: fs+ answer reduction >=25 percentage points; true-finish answer reduction <=30 points; zero invalid outputs; healthy text. Online success remains a separate outcome.

First finding: broad's cached construction contains two fs+ tasks, one of which is the explicitly excluded chrome/480bcfea@4. One positive task cannot support grouped cross-validation. Additional DIAG construction contexts are therefore needed before a separability claim. Broad's six evaluation tasks stay outside all construction. Reserved IDs are filtered using broad's existing exclusion manifest; neither the reserve file nor test split is opened.

Capture positions: last input token and end of recorded thinking, both before the JSON note. Tool-name-prefix activations are excluded from fitting because note and thought already verbalize the decision. End-of-thinking activations can nevertheless encode a decision already reached during reasoning; results must distinguish both positions.

Budget and stop: first overlap report before 03:04 UTC; first complete checkpoint target before 03:49 UTC. At most 64 new capture forwards, one capture recovery, two learned candidate mechanisms and one matched random control for any admitted mechanism. No parameter search on the six evaluation contexts. Stop after two candidate mechanisms without meeting the gate, two consecutive intervals without measurable progress, fleet STOP, or the 90-minute checkpoint deadline. Log all failures and incomplete calls. Evaluate original and candidate with common seeds 7100–7107, vLLM 0.23, T=.8, top_p=.9, top_k=20, thinking and exact schema, plus three deterministic text controls.

Infrastructure: initial pull was blocked by pre-existing shared modifications; fetch verified HEAD equals origin/main. Other agents' files remain read-only. Every numerical process uses two CPU threads. GPU jobs use the fleet semaphore and bounded timeouts.

Source identities, replay fidelity, task separation, overlap/CV, mathematical solve, exhaustive tensors and BF16 behavior passed independent integrity checks. Final FP16 behavior also passed independent integrity, schema and health checks; efficacy fails in both arms.

## 02:30 UTC — overlap delivered to ares

Construction was expanded using the existing DIAG manifest, filtered against the 75-task allowlist before episode content was read. Frozen set: 19 fs+, 19 true finishes, 16 healthy steps across 38 tasks, plus three text controls. The 57 captures completed in 199 seconds; peak reserved GPU memory was 14.35 GB. Input-token counts matched the frozen replay counts for all 54 GUI contexts. The current assistant JSON was never included. Capture SHA256: `b16a233837d6b19603e80e6359a45a48af5fbd19643ca2fba09ee95fa08d71f1`.

| Diagnostic across 24 writers | Prefill | End of recorded thinking, before note |
|---|---:|---:|
| Median principal angle | 66.83° | 68.68° |
| Mean squared principal-angle cosine | 0.277 | 0.245 |
| fs+ activation energy inside true-finish span | 86.23% | 83.21% |
| Median task-CV ridge AUROC | 0.704 | 0.634 |
| Writer AUROC range | 0.606–0.901 | 0.507–0.775 |

Primary AUROC aggregates positive-negative pairs within each held-out fold; pooled scores from differently calibrated folds are secondary. The inherited five-fold split has one fold with only one true finish. Task-label permutations preserve class counts within folds (199 permutations). Best prefill writer is layer14 DeltaNet out_proj, AUROC 0.901, uncorrected permutation p=.005. This is a multiple-comparison exploratory result.

Crucial confound: step index alone scores 0.852, context length 0.845, and both 0.859. There is no total empirical span overlap, but neither low overlap nor these probes establish a semantic discriminator or an information-theoretic impossibility bound. End-of-thinking keys contain recorded reasoning and can encode its decision even though they precede the JSON note.

## Formula correction and construction

Ares explicitly authorized adding `epsilon * W_H` to the numerator at message6156. The implementation is:

`W* = W_H + 0.5*(W_CUA-W_Qwen)*F*F.T*(F*F.T+T*T.T+G*G.T+epsilon*I)^-1`.

Each F/T/G block is divided by the square root of its column count, so each stratum contributes its mean covariance. G includes the three generic text keys. Both prefill and endthink keys are used. Only the 24 residual writers in layers12–23 change; actual input widths are 9216 for MLP and 4096 for attention/DeltaNet.

Independent FP64 checks passed for dense versus dual solve, normal equations and nullspace preservation. The original uncentered formula would annihilate unobserved directions. Nullspace preservation applies to the FP64 update; BF16 rounding introduces additional error and is reported separately.

The predeclared ridge grid was `epsilon = alpha * trace(XX.T)/d`, alpha in {.01,.1,1}. Alpha1 won construction-only grouped CV: objective .6664 versus .7208/.7308 at .1/.01; the unmodified-Holo reference objective is1. Components: relative donor-fit error on fs+ .3032, true-finish actuation .2513, healthy actuation .1118. This selects a research candidate, not an admitted behavioral improvement. Maximum full-fit normal-equation residual was2.37e-13.

The full HF checkpoint `/dev/shm/regmean_cua_centered` was built by 02:32 UTC:724 tensors,24 edited,105,314,253 changed BF16 elements. Exhaustive independent checking is running. All source inference assets are copied unchanged. No upload or serving before that check passes.

## 02:39 UTC — fresh original measured

The first baseline attempt submitted51 calls but retained no outputs: the privacy guard also matched timestamped PNG dictionary keys. The recorder now stores minimal context identifiers, sanitizes keys and values, and preflights every row before any request. A six-context regression check passed. One bounded recovery was run; the failed attempt and its cost remain recorded in `PROBE_RECOVERY.json`.

The fresh paired baseline `evaluation_original_v2` completed51/51 calls on pod vLLM0.23: fs+ answer15/16, true-finish answer16/16, healthy valid nonanswer16/16. Invalid/schema errors/truncations0. Three text controls are healthy. Thus the requested candidate gate on this panel is fs+ answer<=11/16 and true-finish answer>=12/16, with zero invalid outputs and healthy text. These are regenerated decisions, not an online OSWorld score.

The checkpoint audit found all724 tensors finite,24 intended edits and700 unchanged tensors, with13 inference assets identical. Its first full verdict was blocked solely by JSON converting float dictionary keys in ridge scores to strings. The checker preserves that FAILED receipt, tests canonical JSON equivalence while still rejecting changed values, and reruns the exhaustive verification. Candidate weights and metadata have not been altered to pass a check.

An equal finite-sample span would not itself imply a global scalar merge: covariance proportionality is also needed. The present overlap and linear probes are descriptive diagnostics, not information-theoretic bounds.

## 02:49 UTC — BF16 artifact verified, uploaded, evaluated

Exhaustive independent checkpoint verification passed (`VERIFY_CHECKPOINT.json`, SHA256 4941b654d31e783b0a7078ebba3936ebc74de404eebfa3c820b05a97981706ce). The full checkpoint was uploaded at about02:43UTC to Modal account1, `holo-models:/ckpt/regmean_cua_centered`, within25minutes of start. It remains a research artifact, not an accepted improvement.

The 51-call paired BF16 evaluation is complete. Fs+ answer15/16→13/16 (−12.5pp), true-finish answer16/16→15/16 (−6.25pp), healthy valid nonanswer16/16→16/16; zero errors, invalid JSON or truncations. The primary efficacy gate FAILS. Only two independent tasks per stratum; eight seeds are repetitions, not sixteen independent tasks. Fs+ per-task reductions are0 and25pp. The original server used a larger KV allocation than the candidate; both ran vLLM0.23 with identical sampling/schema/context inputs. Independent behavioral review is running.

Ares message6248 authorized one precision variant (FP32 or FP16). The revised secondary arm stores the same frozen FP64 updates on exactly24writers inFP16 and leaves all700 other tensors byte-identical. It replaces the optional discriminant-mask arm, without new fitting or hyperparameter selection. The amended stopping rule is two precision arms of the same learned mechanism; no third learned arm is authorized in this run. Both the original and candidate will run sequentially on the same dedicated server with `--dtype float16`, identical limits and paired seeds. Median BF16 error `||stored_delta-requested_delta||/||requested_delta||` is51.9%; this is not a literal fraction of erased signal and does not establish functional loss. FP16 error is measured during construction. The BF16 server was stopped by verified owned PIDs; no shared server was touched.

FP16 construction completed before02:52:34UTC. Quantization error across24writers: median12.425%, range7.348–16.011%;299,043,622 element values change. This is a4.18× reduction in median numerical error, not evidence of behavioral improvement. Original BF16 artifact and its audit remain intact.

At02:54UTC independent FP16 audit PASSED:724 finite tensors,24 exact FP16 writer formulas,700 original values/dtypes preserved,13 exact inference assets. Receipt SHA256 `a07fc9497eda080815ad7b6f2fd4a3b225d6a985e8d76a0b42a704ad97ad4d78`. Full checkpoint uploaded to Modal account1, `holo-models:/ckpt/regmean_cua_centered_fp16` (9.7G/33s). Runtime must explicitly use `--dtype float16`; converting back toBF16 would reintroduce storage rounding. Installed GatedDeltaNet rejects FP32; FP16 has no static prohibition and awaits actual baseline verification.

The first precision probe launcher selected systemPython3.14, which lacksOpenAI. It failed at import before any generation request or output creation; the readiness GET had already completed. Execution now reuses `/home/orbit/osw/venv/bin/python` (3.12.15, OpenAI3.46.0, jsonschema4.26.0); `run_probe.sh` pins this existing interpreter for subsequent runs. No packages or experiment settings changed.

## 02:59UTC — original FP16 baseline complete

All51 baseline calls completed: fs+ answer15/16, true-finish16/16, healthy valid nonanswer16/16, zero schema errors or request errors. Text controls are391, the correct French translation, and a coherent freezing explanation. The paired candidate must again reach fs+<=11/16 and true>=12/16. Original API and descendants were stopped by owned PIDs before candidate launch.

Independent BF16 behavior review passed data/protocol integrity and text health (`VERIFY_BEHAVIOR_BF16.json`), while explicitly failing efficacy. All16 healthy structured outputs plus8 stable/changed examples were read; no general corruption was found. Independent FP16 baseline audit subsequently passed all51 calls, canonical schema revalidation, exact paired keys/settings, finite values, stop reasons and text health. The candidate launch gate is recorded in `VERIFY_PRECISION_PROTOCOL.json`.

## 03:05UTC — final behavioral counts

| Runtime/storage variant | fs+ answer original → edited | Reduction | True-finish answer original → edited | Healthy valid nonanswer | Invalid/error/truncated | Admission |
|---|---:|---:|---:|---:|---:|---|
| BF16 | 15/16 → 13/16 | 12.5pp | 16/16 → 15/16 | 16/16 → 16/16 | 0 | FAIL |
| FP16, same frozen update | 15/16 → 16/16 | −6.25pp | 16/16 → 16/16 | 16/16 → 16/16 | 0 | FAIL |

Each row has its own original reference on the same vLLM0.23 backend and eight common seeds per held-out task. The FP16 arms additionally share exactly the same dedicated launcher/server limits. The three text controls are correct and identical to their originals in both variants. All four scored arms completed51 outputs each (204 recorded outputs). The earlier baseline recorder failure submitted51 additional generation calls but retained0; the precision import failure submitted0 generation calls. Total generation submissions therefore255, of which204 have retained scored outputs. No further learned arm or random control was run: neither learned precision arm met the fixed primary gate. The optional discriminant-mask arm was superseded by ares's precision amendment.

The empirical construction spans are not identical, but grouped separability is strongly confounded by step/context length. Better FP16 representation of the same selective update did not rescue behavior on this panel. This is a bounded negative result for this construction, ridge selection and tiny held-out cohort; it does not prove all RegMean edits impossible. Regenerated next actions are not executed OSWorld results. No reserve/test episodes were read or evaluated, and no online gain is claimed.

All owned GPU APIs, engines and the SSH tunnel are stopped, with PID cleanup receipts. The first overlap reached ares at02:30UTC (~11min); the first complete HF upload at02:43UTC (~24min). Both complete HF checkpoints are archived in Modal account1 under `/ckpt/regmean_cua_centered` and `/ckpt/regmean_cua_centered_fp16` on `holo-models`. FP16 requires explicit runtime dtypefloat16. Final independent behavioral review PASSED integrity and health, found the comparison CORRECT, and FAILED efficacy (`VERIFY_BEHAVIOR_FP16.json`, SHA256 bd878106f1ef6bad820da91eb2605aca03ecc879ed58fd025c99666aa0081c09). No further model search is scheduled.

Both temporary full-checkpoint directories were removed after validating their upload receipts, manifests and independent verification. This released20,746,103,045bytes; full HF artifacts remain inModal1. `/dev/shm/astra-regmean` retains134MB of captures, exact FP64 factors and calculation evidence. See `STORAGE_CLEANUP.json`; no other researcher directory was changed.

Evidence packaging: all75 archived evidence files were hash-verified on the pod. Extraction was rerun successfully with `--no-same-owner` because the shared mount rejects ownership changes. A full `git diff --check` flags trailing whitespace/CR in preserved raw vLLM, SSH and upload logs; those bytes are retained to preserve audit hashes. The same check on Python, shell, JSON, Markdown and ignore files passes. No numerical/behavioral check was relaxed.
