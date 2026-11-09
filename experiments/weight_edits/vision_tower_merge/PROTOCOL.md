# Moon-vision frozen protocol — 2026-11-08 07:09 UTC

Scope: weights only. The 297 model.visual.* tensors, including merger, receive float32 Holo + beta*(CUA-Qwen), then cast to original Holo dtype. All 427 other tensors, configs and tokenizer stay byte-exact Holo. CUA norm nonzero: test beta .5 and1. No adaptive dose selection. Original plan: maximum2 candidate arms and1 original arm,223 requests each; see explicit amendment below. No reserve45/split_test data consulted.

Frozen cohort SHA256 2faee8f1af5a1243b8c8bacbf0369e4e035ab9dc336307c9f6678c0d134c24d0. Frozen payloads/schema/settings/source hashes from astra-power/FROZEN.json.19 fs+,20 true finishes,16 healthy; seeds17000..17003.220 GUI calls/arm atT.8,top_p.9,top_k20,max_tokens3072,reflection enabled,exact harness JSON.3 fixed text prompts atT0,max_tokens256,thinking off per canonical text setting. Original reused from complete power_A if available; otherwise own matching server. All requests retain errors,invalids,truncations; no silent retry.4-request pilot retained, then216 remaining. No restarting a completed statistical arm. Infrastructure can be repaired twice maximum; two rounds without progress stop and report.

Own server vLLM0.23,BF16,max_len32768,max_sequences32,KV8GiB,GPUutil.15,images5,qwen3 reasoning,prefix cache on,port8028. Scheduler gpu_slot.sh. Existing servers and files read-only. CPU2threads.

Acceptance: valid JSON>=95%,all3 text prompts sane,healthy semantic usefulness no drop>2percentage points,AND fs+answer down>=15percentage points OR independently visible better actions. Structural valid nonanswer is only a diagnostic, not healthy semantic success. True finish preservation reported separately. Invalids never count as corrected false successes. Comparison paired by task and seed, intervals bootstrap by task. No claim of online benefit from offline probe. Independent builder/checkpoint and behavioral audit required. If passing, complete HF checkpoint verified, ares notified to own online45+120.

End inference by09:40UTC and decide before09:45UTC, or earlier once two arms audited. Preserve evidence and stop owned server/tunnel. REPORT.md includes any incompleteness and failed gates.

Implementation: WORKFLOW_FREEZE.json pins the executing moon runner separately from the inherited canonical sources. Reused power_A outputs are copied verbatim to runs/A with IMPORTED_A.json provenance after checking exactly220 unique task/seed pairs and receipts; they are not resumed by the moon runner. GUI and three text controls are separate artifacts; candidate analysis requires both. Original baseline text controls are not required when reusing power_A, whose text cohort is empty.

## Explicit ares amendment, received message6520 before candidate inference
Cap3 checkpoints: retain CUA beta.5 and1, then add Holo_vis+.25*(Holo_vis-Qwen_vis) after CUA screening, within09:45. Message6532: never serve own baseline; reuse complete power_A. Baseline now imported220/220. Total cap889 requests =220 existing baseline +3*(220GUI+3text). E025 is specified before any candidate outputs. No additional dose search. Own baseline serving forbidden. Original v1 protocol/freeze retained.
