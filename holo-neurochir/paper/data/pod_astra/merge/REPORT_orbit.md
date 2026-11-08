# Astra merge — 2026-11-08

Owner: astra-merge. Started 01:35 UTC. Status: preparing first CUA-Lite beta 0.5 language-only checkpoint.

## Constraints and success criteria
Only static weights change. No gradients, adapters, prompt changes or inference harness changes. Output is a complete HF checkpoint preserving Holo processor/tokenizer/config and all vision and lm_head tensors. Ignore source mtp tensors. Exact Holo revision: 8c88265a5a159bfd1492db9243733dd2e6e04a6e.

Every source must match all retained tensor shapes and architecture parameters. Compare donor to Qwen post-trained and Base by aggregate language-layer cosine and distance before editing. Cosine supports proximity, not proof of training history. Pin revisions and validate cached Qwen weight SHA256 against HF metadata.

Primary deliverable: CUA-Lite beta 0.5, then beta 0.25 and 1.0. Up to nine candidates total: three CUA doses; three Fara doses if compatible; a two-donor arithmetic mean, TIES retaining the largest 20% absolute delta entries per tensor, and DARE retaining 20% with inverse-probability scaling. All candidate coefficients fixed before results. First two-donor dose beta 0.5. No vision edits in this bounded initial campaign.

Stop a candidate on nonfinite/shape/provenance failure or unhealthy generation. At most two repairs of a technical failure; two rounds with no measurable progress stop further expansion and report to ares. A complete healthy checkpoint is progress and is sent for online evaluation even if static answer rates stay unchanged. No automatic open-ended search.

Static screen: three text prompts T=0, healthy OSWorld JSON, then DIAG fs+ k=8 with T=0.8/top_p=0.9/top_k=20, reflection and exact schema using existing cohort scripts. Confirmation reserve and split_test never used for construction or screening. Online confirmation on 45 fresh paired tasks and subsequent 120 test tasks are owned by ares. Static answer rate is not OSWorld success.

## Resource and provenance
Pod rules FLEET_ORDERS.md and CPU_RULE.md read. Python CPU threads limited to 2, CPU affinity 40,41 for analysis. No GPU jobs started. Existing Qwen caches read-only. CUA donor revision df6eba93efb2df3ed9adc810e0f7f4e038959c74 downloaded to /dev/shm/astra_merge_cua. Source repository: https://huggingface.co/OnAnOrange/CUA-Lite-Qwen3.5-4B-ScaleCUA-gpt5_5-epoch3-public .

Initial shared repository pull blocked by other agents' dirty files; fetch showed HEAD equal to origin/main. No shared files reset or stashed.

## Verification
Independent source/code review and full tensor checks completed for the released candidates below. Original and CUA beta0.5 static cohorts passed health checks. Online success remains pending and is owned by ares.

## Source gate — 01:41 UTC
- Qwen post-trained revision 851bf6e806efd8d0a36b00ddf55e13ccb7b8cd0a and Qwen Base revision 1001bb4d826a52d1f399e183466143f4da7b741b: all four local weight shard SHA256 values match official HF metadata. Full evidence: reference_provenance.json.
- CUA-Lite: 723 common Holo tensors, zero shape mismatch; 15 mtp keys ignored. Holo's separate head retained. Config-only independent check established that Qwen's nested vision model_type qwen3_5 is normalized by Transformers 5.22.2 to qwen3_5_vision. Raw dtype metadata differs, architecture fields do not.
- Language layers (embeddings excluded): cos(donor,Qwen)=0.9999278604; cos(donor,Base)=0.9979053199; L2(donor-Qwen)=4.0146597, L2(donor-Base)=43.2947754. Evidence favors post-trained origin, consistent with donor training metadata. cos(tau_d,tau_H)=0.00740704. Full per-tensor sums and embedding/vision results: cua_metrics.json.
- Fara downloaded to /root/astra_merge_fara, revision 776a33ae5b2ad503796a97ae20fdc66f61d2feea; 723 exact common keys/shapes. TMax revision c733e09b808d837ae7450eccc8cb8dace07316d6 has only426 text tensors and no vision: excluded from the strict full-architecture campaign, not downloaded.
- Screening cohort sealed in cohort.json: two fs+, two fs-, two healthy DIAG contexts, seeds0..7, three generic text prompts. Zero overlap with canonical45-task reserve, tasks-map hash03726f07b411869a7a4004b0f3c89ba37d89e948f34ac19cb70e4bb0c3cb5bb7. No test content accessed. Original pod reference screening started with unmodified astra_cohort_probe.py.
- CUA training-data contamination limitation: public ScaleCUA adapter includes OSWorld-shaped generated and RL tasks. Exact donor training examples and overlap with our reserved benchmark are not established. Virgin-to-editing reserve does not establish absence of donor training contamination. Ares informed; retain this limitation in any paper.
- Independent source/code review: density range validation added; sparse TIES density explicitly per tensor. No gradients or harness modification. Artifact verification pending build completion.

## First complete checkpoint — 01:48 UTC
- Checkpoint `merge_cua_b050`, formula Holo +0.5(CUA-Qwen), language only, was built at01:42 UTC and uploaded to Modal account2 in42 seconds. Durable HF directory: `holo-models:/ckpt/merge_cua_b050`; served root `/models/ckpt/merge_cua_b050`, served name `Holo-3.1-4B-merge_cua_b050`.
- Independent exhaustive artifact PASS:724 tensor keys/shapes/dtypes/finite; exact arithmetic on426 language tensors; all298 remaining tensors exactly preserved;338 changed tensors,88 language tensors unchanged after BF16 rounding;2,125,448,677 elements changed; actual update L2=2.33773893. Eleven auxiliary files byte-identical to Holo; local config/processor loads succeeded. Evidence VERIFY_CUA_B050.json and astra-merge-artifact-review.md.
- Weight SHA256: shard1 `b7acdd12152d0f2b351831ce7b691259cbd9e4188eba084050505e504c60eecd`; shard2 `6f88c913b715d1f66ae08ddc995c4eb3df0bd75e1919df7e60a944d5b61652ad`. Builder v1 SHA256 `2a947d84ec0c3d1644b618915c60e012c7171c96e0e69f1a6129b01b76cece0a`.
- Modal smoke PASS at01:48 UTC:3/3 coherent nontruncated generic text responses, healthy structured OSWorld step valid and expected `write` action. Full51-generation DIAG cohort launched next. Initial endpoint identity request timed out during startup; subsequent health returned200 and expected model identity was checked before any generation. No generation from another checkpoint was accepted.
- Baseline original pod:51/51 completed; fs+ answer16/16, fs- answer16/16, healthy nonanswer16/16; no invalid/error/truncation; three coherent text responses. SHA256 generations7c56871078e6cd4db5dff71a834abba92d272db19d70732f5c9054db104ec89e. Original uses H200 pod and candidate H100 Modal: this static comparison is exploratory across backends, not the paired online success claim.
- After verified upload and successful vLLM smoke, only the redundant local `/dev/shm/merge_cua_b050` copy was removed to free space for beta0.25; the complete Modal checkpoint and manifest/report remain intact. Shared weights/other agents' artifacts untouched.

## Fara source gate
Language-layer cos(donor,Qwen)=0.9986756976 vs cos(donor,Base)=0.9967178023; distances33.8877201 vs54.6415271. cos(tau_d,tau_H)=0.02332451. This donor vector is8.44 times the CUA language-vector norm, so equal beta is a stronger perturbation. Compatibility723/723 passed. Full evidence fara_metrics.json.

The other OnAnOrange repo `qwen3.5-4b-lite-osworld-scalecua-cuagym-sft-ep3` at75822745d08cf23eea35f7db1514c1cad968f6fb has identical config/layout but different weight hashes. It is a separate donor explicitly trained on Lite.OSWorld+Lite.ScaleCUA+Lite.CUAGym, not an alias of our selected ScaleCUA-gpt5_5 model. Not included in this bounded campaign.

## CUA beta0.5 behavioral screen — 01:50 UTC
Independent raw-output audit confirms exactly51 generations with matched tasks/seeds:48 structured plus3 texts; no invalid output, error, truncation or non-stop finish. Static counts:

| Group | Original pod | CUA beta0.5 Modal2 |
|---|---:|---:|
| fs+ answer |16/16|11/16|
| fs- answer (true completion)|16/16|2/16|
| healthy valid action|16/16|16/16|
| coherent generic text|3/3|3/3|

This is not a protected improvement: fs+ answer drops31.25 percentage points, but true-completion answer drops87.5 points. The5 fs+ actions are extra scrolls after already recognizing apparent success; the14 fs- actions are coherent extra verification clicks (open Files or reselect slide2). A non-answer alone does not prove useful recovery. Audit: VERIFY_CUA_B050_BEHAVIOR.md/json.

Ares launched the actual45-task reserve evaluation with6 GitHub jobs against this Modal2 checkpoint. No reserve task/result content is read or used in this experiment. A same-backend original replay was requested to separate H200/H100 effects, then explicitly deferred when the online run took priority: never replace an in-use evaluation service. All subsequent variants remain from the predeclared coefficient/method grid, independent of reserve results.

Beta0.25 is built; upload to Modal2 storage only and independent verification in progress. No service redeployment by this session.

## Same-backend original reference — 01:54 UTC
Ares/modal-serve supplied original Holo on Modal account1 with pinned revision and matching source hashes. The51-call cohort completed: fs+ answer16/16, fs- answer16/16, healthy valid-action16/16, text3/3; no errors/truncations/invalid outputs. Independent audit VERIFY_MODAL_REFERENCE.md/json confirms identical tasks, seeds and settings to candidate Modal2. Both are H100/vLLM0.23.0, resolving the earlier backend-class confound; separate accounts/containers remain, so seeded outputs are not claimed bitwise deterministic.

Interpretation: loss of `answer` on fs- is a deterioration of a stopping proxy, not an observed OSWorld score regression. OSWorld success depends on evaluated final state. Extra verification can be harmless or useful; continuation can also undo completed work or spend steps. Only the untouched online run can adjudicate this. No candidate is rejected solely for the fs- stopping count.

Beta0.25 has independent exhaustive PASS and complete uploads on both Modal accounts. Its redundant local copy was removed only after verified upload, with manifest preserved. Fara beta0.5 is building; no new hypotheses are selected using reserve outcomes.

## Storage and log correction — 02:00 UTC
Fara beta0.5 independent assertions all passed (381 changed tensors), but writing the final evidence on `/workspace` raised Errno122: shared quota exceeded. No model operation failed. Full experiment directory backed up to `/root/astra_merge_evidence`; verifier published backup JSON/Markdown on orbit and the root backup. New build logs/evidence use root until quota recovery; canonical workspace source remains available. Current authoritative updates also remain in orbit local REPORT.md. The fleet was notified; no foreign files were deleted.

A Modal expiry warning exposed a token identifier in upload logs. All affected owned logs (workspace and root backup) were sanitized. New `upload.py` invokes the existing authorized upload command with client stdout/stderr discarded before storage, then records only safe checkpoint/account/hash/exit/timing fields. This removes the cause instead of relying on future warning text. No credential values are put into reports or commands.

CUA primary training provenance independently confirmed: full BF16 SFT from Qwen851bf6..., exact Lite.ScaleCUA dataset revision3aa5998a84cdf034e7907b1bb597899dce890417, desktop.use.train.gpt5_5,5000 trajectories/42427 serialized steps,3 epochs,LR5e-6,action-only format with reasoning disabled during donor training. Original Holo inference/reflection settings remain unchanged in every merged checkpoint measurement.

## CUA doses and next donor — 02:06 UTC
CUA beta0.25 smoke passed on Modal1: three coherent T=0 responses and one valid healthy write action. Full matched51-generation DIAG screen completed: fs+ answer15/16, fs- answer11/16, healthy16/16 valid nonanswers, no invalid/error/truncation. Independent behavioral audit PASS: VERIFY_CUA_B025_BEHAVIOR.md/json. CUA beta1.0 full HF build completed and independent exhaustive verification PASS:724 layout/shape/dtype/finite,426 exact language formulas,298 bitwise preserved,364 changed tensors. Uploaded account1; runtime health pending. Fara beta0.5 is independently verified and uploaded on account1, awaiting its service window. Only ares/modal-serve changes services.

Workspace quota has recovered after owners moved their own files; root backup remains authoritative until evidence is synchronized back. No foreign files or processes were changed.

## Fara pilot health — 02:09 UTC
Fara beta0.5 passed runtime smoke and the full51 matched DIAG screen on Modal1:3/3 coherent complete T=0 texts, fs+answer16/16, fs-answer14/16, healthy16/16 valid nonanswers, no invalid/error/truncation. Independent behavior audit PASS. Fara beta0.25 complete checkpoint passed independent exhaustive audit and account1 upload; runtime health awaits its service window. Its lower dose and the remaining fixed grid were selected before any online reserve outcome.

CUA beta1 independent artifact PASS and account1 upload complete. Redundant local checkpoint removed after matching uploaded manifest and PASS evidence, freeing shared memory; full cloud checkpoint and manifest preserved.

## Remaining fixed grid — 02:11 UTC
Fara beta1 construction started after Fara beta0.25 exhaustive PASS. Next names are `merge_dual_mean_b050`, `merge_dual_ties_b050`, `merge_dual_dare_b050`, each with donor order CUA then Fara and beta0.5. Sparse density0.2 and DARE seed20261108 remain fixed. Shared CPU build/check operations are serialized. Account1 is temporarily assigned to another fleet experiment; no endpoint is replaced by this session.
