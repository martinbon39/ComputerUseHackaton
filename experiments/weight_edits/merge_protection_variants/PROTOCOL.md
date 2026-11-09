# Registered experiment — moon-combo

Registered before construction or candidate outputs, 2026-11-08 07:07 UTC.

Base Holo-3.1-4B revision 8c88265a5a159bfd1492db9243733dd2e6e04a6e. Donor /dev/shm/astra_merge_cua. Reference /root/expo/base. Reproduce the complete language merge H + 0.5(CUA-Qwen), preserving the original merge policy outside the protected residual writers, and preserving vision and explicit output head. No gradients, LoRA, prompt or harness change.

Head precision: `lm_head.weight` is preserved in the serialized checkpoint, while `embed_tokens` is merged exactly as in B. The unchanged Holo config has tied embeddings, so the effective output head at load time follows the engine's tied-weight handling; no claim of an unchanged effective head. All contrasts against B keep this loading policy identical.

Fixed candidate cap: three. Round 1: remove the rank-one B done direction from the merge delta on writers 12–23, then on writers 0–31. Round 2: project the merge delta into the nullspace of already captured genuine-finish input keys, using available construction-only writers. The direction and keys come only from pre-existing astra-broad construction artifacts, never from the screening cohort. Freeze exact factor provenance and overlaps before generation.

No adaptive coefficient search. Build and check one candidate before scaling; builds and numerical verification serialized, CPU two threads. Retain at most two owned full checkpoints simultaneously; free rejected checkpoint only after evidence is archived. Each candidate is served through gpu_slot.sh, port 8026, vLLM 0.23, GPU utilization <=0.15; 8000 and 8024 untouched. Stop owned services by recorded PID only.

Mandatory frozen astra-power cohort SHA256 2faee8f1af5a1243b8c8bacbf0369e4e035ab9dc336307c9f6678c0d134c24d0: 19 feasible fs+, 20 genuine finishes, 16 healthy contexts. Identical frozen payloads, canonical schema, reflection enabled, T0.8/top_p0.9/top_k20/max_tokens3072, four paired seeds 17000–17003, 220 completions per arm. Three text controls at T0. Reuse complete astra-power original A with identical request semantics when available, otherwise serve A under the same configuration as candidates. Do not access reserve45 or split_test contents for construction.

Report answer frequency separately on fs+ and genuine finishes, valid nonanswer frequency on healthy, JSON validity, errors and truncation; task-level paired uncertainty, and construction-overlap sensitivity. Healthy valid nonanswer is a structural proxy, not task success. Assess useful continuation from saved action text/screenshots without counting mere answer suppression as better actions.

Admission: JSON validity >=95%, three healthy text controls, healthy structural success loss <=2 percentage points vs A, plus fs+ answer reduction >=15 points OR independently documented visibly better actions. Genuine-finish restoration vs unprotected CUA is the central outcome and must be shown prominently; no claim of online benefit from replay. Only an admitted, independently verified complete HF checkpoint is handed to ares for online45+120.

Stop conditions: fixed three-candidate cap; no further tuning after two rounds with no measurable progress on true-finish retention at preserved fs+ suppression; maximum one infrastructure recovery per failure and stop after two attempts without progress. Final offline decision before 09:45 UTC, even if incomplete. Missing arms are NOT RUN, never imputed. Independent fresh-context review of formulas, provenance and behavior before conclusion.
