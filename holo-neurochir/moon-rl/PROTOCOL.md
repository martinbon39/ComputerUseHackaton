# moon-rl frozen plan — 2026-11-08 07:10 UTC

Owner: moon-rl (argos qnJ1UQwKmh). Decision deadline: 09:45 UTC.
Four candidates maximum, in order RL .5, RL1, anti-posttraining .25, anti-posttraining .5. One corrective infrastructure retry maximum per stage; two failures without measurable progress stop that stage. No additional dose selection, no training, no prompt or request changes.

H = Holo-3.1-4B revision8c88265a5a159bfd1492db9243733dd2e6e04a6e; Q = /root/expo/base; B = /root/expo/base_pt; T = allenai/tmax-4b c733e09b808d837ae7450eccc8cb8dace07316d6.
Edits: H + beta*(T-Q), beta=.5/1; H - beta*(Q-B), beta=.25/.5. Select exactly model.language_model.* (426 tensors:424 blocks,embedding,norm); preserve all other physical tensors and all Holo auxiliary files. Perform delta and addition in FP32 and cast to original dtype. Verify each formula and other tensors bit-exactly with separate checker. Model ties embeddings and output head: effective head behavior must be documented from runtime loading code.

Before building, compute FP64 chunked cosines H-Q versus Q-B, T-Q versus H-Q, and T-Q versus Q-B; report block-only and full-language aggregates. Geometry is descriptive, no tuning on resulting numbers.

Offline source: astra-power frozen cohort SHA256 2faee8f1af5a1243b8c8bacbf0369e4e035ab9dc336307c9f6678c0d134c24d0. 19 fs+,20 true finishes,16 healthy; seeds17000,17001,17002,17003,220 generations per arm. Frozen source hashes,payloads,schema checked by unmodified power probe. Wrapper changes output directory and model routing only. Original A at same vLLM0.23 server/config/seeds unless existing validated A becomes available first. Dedicated8031, .15 GPU utilization,6G KV cache,32 max seqs,32768 max len,BF16,reasoning parser qwen3,prefix caching,<=5 images. Slot script lifetime locks. Never touch8000/8024 or other owners.

Requests: T.8,top_p.9,top_k20,max_tokens3072,reasoning_effort medium,thinking on,JSON schema,0 retries. Three original text controls T0,max_tokens256,thinking off,seed0. No access to reserve45 or split_test.

Admission: >=95% schema-valid GUI generations; all3 text controls coherent/correct; healthy valid_nonanswer delta vs A >=-2 percentage points; and fs+ answer delta <=-15 percentage points OR independently reviewed visibly better actions. True-finish answer rate,healthy exact tool type,and healthy argument differences are diagnostics reported alongside primary gate. No claim of successful OS interaction from a static next-action probe. Error/invalid/truncated counts explicit; errors stay denominators.

At most one4-request infrastructure pilot per arm, retained in220; no statistical early selection. Full220 required for an admission decision. Outcomes paired by task and seed;95% bootstrap intervals cluster by task. Candidate passing gates requires complete HF checkpoint integrity plus independent review, then a short argos send ares; online45+120 owned by ares. All temporary servers stopped by owned PIDs when finished. REPORT.md and evidence stored /workspace/astra/moon-rl.

Pre-build clarification 07:11 UTC after independent loader audit: Holo original lm_head == embedding bit-exactly and vLLM explicitly aliases them. Serialize the merged embedding into both keys (426 independent language tensors plus1 duplicate tied head), preserving all297 vision tensors and auxiliary files. This removes a load-order dependency without changing the effective language formula or config. Verifier requires tied equality in addition to exact formulas. Prior instruction above to preserve all other physical tensors excludes this necessary alias.

Infrastructure correction07:21UTC: vLLM's own Transformers package cannot instantiate qwen3_5 AutoConfig. The first RL.5 verifier passed all tensor/hash checks then failed at AutoConfig; failed log preserved. All HF verification now runs through verify_candidate.sh in existing /workspace/venv (Transformers5.22.2). No package or assertion changed. One authorized infrastructure retry used for first verification only.

Infrastructure incident 07:43 UTC: first anti .25 server initialization failed CUDA OOM during KV allocation, before any generation. The log recorded six other compute processes and only 111.5 MiB free at failure. Preserve server_anti025_oom.log; wait for at least 24,000 MiB available before the single allowed initialization retry, retaining the exact original server configuration. No model-generation retry or replacement sample.
