# moon-rl — RL donor and anti-posttraining

Status: OFFLINE DECISION at 2026-11-08 08:02 UTC, before the 09:45 UTC deadline. Anti .5 is eligible for ares’s online confirmation through the qualitative branch only. RL .5, RL 1 and Anti .25 are rejected. No online test launched by this agent.

## Frozen experiment

Holo-3.1-4B `8c88265a5a159bfd1492db9243733dd2e6e04a6e`; Qwen chat `/root/expo/base`; Qwen Base `/root/expo/base_pt`; Tmax `allenai/tmax-4b@c733e09b808d837ae7450eccc8cb8dace07316d6` downloaded to `/dev/shm/moon_rl_tmax` after checking capacity. Four predetermined candidates: `H+.5(T−Q)`, `H+1(T−Q)`, `H−.25(Q−B)`, `H−.5(Q−B)`. No gradients, LoRA, prompt changes, or reserve/test access.

Tmax has426 BF16 language tensors and no vision or explicit head. The training mirror `hamishivi/Qwen3.5-4B` and official Qwen have identical public weight blobs. See `REVIEW_MERGE.md` for source evidence; local source hashes are separately checked.

The merge selects426 independent language tensors, including embedding and final norm. Holo ties its output head to embedding and stores both keys; the builder therefore writes the merged embedding to both keys. This yields427 exact formulas plus297 bit-preserved vision tensors. Config/tokenizer/processor/template remain byte-identical to Holo. The correction prevents loader-order dependence in the supplied builder. Independent verification checks the formula, dtype, finite values, tied equality, serialized index, file hashes, and auxiliary files.

## Geometry before construction

FP64 chunked differences and dot products, no double-count of tied head:

| Scope | cos(H−Q,Q−B) | cos(T−Q,H−Q) | cos(T−Q,Q−B) | norm H−Q | norm T−Q | norm Q−B |
|---|---:|---:|---:|---:|---:|---:|
| 32 blocks | −0.02071236 | 0.00035791 | 0.00004332 |31.7358|0.8030|43.1165|
| Language including embedding/norm |0.01521108|0.00001011|0.00000366|593.8303|0.8099|46.5312|

The stated approximately−0.02 cosine holds for the transformer blocks; embeddings change the full-language aggregate. The donor RL delta is much smaller than Holo adaptation. Doses remain exactly the requested ones. Full per-tensor evidence: `geometry.json`.

## Offline evaluation

Frozen cohort SHA256 `2faee8f1af5a1243b8c8bacbf0369e4e035ab9dc336307c9f6678c0d134c24d0`; frozen payload manifest SHA256 `9bf07af1f630ffbee0f628347270dff9c3abe068aa9fb76c9c8c747e47585839`. 19 feasible false-finish contexts,20 true finishes,16 healthy contexts. Each uses seeds17000–17003. All source, schema, and payload hashes are checked by the original astra-power probe before requests. Own wrapper changes routing and output paths only.

220 GUI generations per arm at T=.8, top_p=.9, top_k20, max_tokens3072, medium reasoning, thinking enabled, exact structured JSON schema, no automatic retries. Three standard text controls at T0. Original measured on the same dedicated vLLM0.23.0 configuration: BF16,32768 max length,32 sequences,prefix caching,qwen3 reasoning parser,.15 utilization flag,6GiB KV cache,port8031. Original completed07:15UTC; its own server was stopped afterward. Ports8000/8024 and other owners remain untouched.

Original A: false-finish `answer`56/76 (73.684%); true-finish `answer`75/80 (93.750%); healthy `answer`4/64 (6.250%), hence valid nonanswer60/64 (93.750%). All220 GUI outputs schema-valid; three text controls correct. See `runs/A` and independent baseline audit.

Admission requires≥95% valid JSON,3 healthy texts,healthy valid-nonanswer decline≤2 percentage points,and either false-finish answer decline≥15points or independently demonstrated visibly better actions. True finishes and healthy action-type/argument differences are reported as diagnostics. `valid_nonanswer` is a structural continuation metric; static probes do not establish OSWorld task success. Confidence intervals use paired task-cluster bootstrap100000 resamples,PCG64 seed20261108.

| Candidate | Integrity | GUI/text | fs+ answer delta | true-finish delta | healthy delta | Decision |
|---|---|---|---:|---:|---:|---|
| RL .5 |PASS|220/220; 3/3|+5.26 pp [−1.32,+13.16]|0.00 pp|−1.56 pp|REJECT: no efficacy signal or qualitative exception|
| RL 1 |PASS|219/220; 3/3|+7.89 pp [+2.63,+14.47]|−1.25 pp|−4.69 pp|REJECT: mandatory healthy gate fails|
| Anti .25 |PASS|220/220; 3/3|+1.32 pp [−3.95,+6.58]|0.00 pp|0.00 pp|REJECT: no numeric or demonstrated qualitative signal|
| Anti .5 |PASS|220/220; 3/3|+2.63 pp [−6.58,+11.84]|0.00 pp|−1.56 pp|ADMIT: narrow qualitative branch only|

RL .5 produced 60/76 false-finish answers versus 56/76 originally, 75/80 true-finish answers, and 59/64 healthy continuations. Independent blind action review found no demonstrated overall action-quality advantage. Its original numerical quality labels are retained only as audit history: a later raw-evidence challenge corrected unsupported claims about Nike history, image verification and PDF completion. In particular, an RL .5 terminal answer claimed completion despite eight visible PDF chapters and only seven misnamed outputs. The correction strengthens rejection. No initial qualitative count is presented here as a corrected measurement. See `REVIEW_RL050.md`.

RL 1 produced 62/76 false-finish answers, 74/80 true-finish answers, and 57/64 healthy continuations. One fs+ output was truncated and schema-invalid; it remains in the denominator. Exhaustive qualitative review was not run because it cannot override the mandatory healthy gate failure. See `REVIEW_RL100.md`.

Anti .25 produced 57/76 false-finish answers, 75/80 true-finish answers and 60/64 healthy continuations. All mandatory technical/health gates pass, but the numeric signal fails. An initial blind reviewer proposed qualitative admission; a raw-evidence challenge invalidated all three purported demonstrated examples. The Nike product list was already in the input history; `ls` checks file existence, not the required warm-to-cool ordering; the PDF answer falsely declares completion despite eight visible chapters and only seven incorrectly named/ranged files. The reviewer withdrew admission in a retained addendum. Original blind judgments are preserved and must not be presented as the corrected quality counts. One directly relevant folder-opening verification action remains, counterbalanced by the false PDF finish; no comparative qualitative advantage is established. Final decision: REJECT. See `REVIEW_ANTI025.md` and `REVIEW_STANDARD.md`.

All four full HF checkpoints passed independent verification: 724 tensors, 427 exact formula checks, 297 preserved vision tensors, two shards, eleven unchanged auxiliary files, compatible configuration and processor. Physical tensors changed after BF16 rounding: RL .5 328; RL 1 355; Anti .25 364; Anti .5 378. RL checkpoints were deleted after rejection and evidence preservation, freeing about 20.75 GB.

Anti .5 produced 58/76 false-finish answers, 75/80 true-finish answers and 59/64 healthy continuations. No schema error, transport error or truncation; three texts correct. Healthy exact recorded-tool rate is 57/64 versus 59/64 for A, a diagnostic decline of 3.125 points. Its registered healthy continuation proxy passes narrowly. Final decision: ADMIT through the qualitative alternative only. Independent blind judgments, decoded afterward and checked against the raw history/screenshots, identify directly relevant verification actions on three distinct fs+ tasks: minimizing Chrome to check whether the requested desktop shortcut exists (two seeds), opening the extracted extension folder to inspect its required files (one seed), and opening the rearranged image to inspect the requested order (one seed). These are comparative next-action improvements; they do not require or prove successful subsequent execution.

The signal is narrow and mixed. Anti .5 also introduces a clearly false PDF finish, and healthy action quality has adverse cases. The corrected fs+ task aggregation is 2 better / 1 worse / 14 equal / 2 indeterminate; healthy is 0 better / 2 worse / 13 equal / 1 indeterminate. These are qualitative judgments, not OS success scores or confidence intervals. No new numerical threshold was imposed. An initial reviewer rejection had wrongly required proof of the eventual resulting state, which a static next-action screen cannot provide; the reviewer corrected that interpretation while retaining the blind judgments. See `REVIEW_ANTI050.md`.

Complete verified HF checkpoint retained for ares: `/dev/shm/moon_rl_anti_b050`. Formula is `H − .5(Q − B)` on the full language tower with the tied head serialized consistently. `VERIFY_ANTI050.json`, `build_anti050.json` and `manifest_anti050.json` jointly record exact formulas, reference, donor, two shard hashes and preserved auxiliary files. This is a candidate for online confirmation, not a demonstrated model improvement.

Both anti runs completed. Total experimental requests: 1,100 GUI generations (A plus four candidates) and 15 T0 text controls. All 55 contexts and four seeds were used for each arm; no sample replacements or new doses. The last owned server (8031, PID437251/engine437646) and local tunnel were confirmed stopped by 07:59 UTC. No online test was launched by moon-rl.

## Infrastructure incidents

The first RL .5 integrity check passed tensor/formula/hash checks but the old Transformers bundled with vLLM could not instantiate Qwen3.5 AutoConfig. The unchanged checker passed in the existing `/workspace/venv` Transformers 5.22.2 environment; the canonical verification launcher now uses that environment. Original failed log retained.

The first anti .25 server failed during KV-cache allocation at 07:43 UTC, before any generation. GPU free memory fell from 30.21 GiB initially to 111.5 MiB amid other fleet workloads. Its OOM log is retained. At 07:44:48, 28,505 MiB were available; the single initialization retry succeeded with the unchanged configuration. Anti .25 completed all 220 generations and three texts at 07:51 UTC. No generated sample was retried or replaced.

## Limits and ownership

The gate is an offline screen; an admitted checkpoint still requires ares's paired online45+120. No claim of online improvement is made. No reserve45 or split_test contents were opened for construction. All new artifacts belong to `/workspace/astra/moon-rl`; astra-power and astra-merge sources are read-only. The shared local repository could not pull because of pre-existing changes; fetch confirmed HEAD was one local commit ahead and zero behind its upstream, and no third-party working files were changed.

## Handoff and retained artifacts

Ares was notified through `argos send ares` at 08:02 UTC with the complete checkpoint path, gate values, qualitative rationale and regressions. Ares owns the 45 + 120 online confirmation; no online result exists for this candidate in this report. The three rejected checkpoints were deleted after preserving manifests, build reports, verification evidence and raw outputs. Keep `/dev/shm/moon_rl_anti_b050` for ares and `/dev/shm/moon_rl_tmax` as the pinned donor. See `CLEANUP.json` and machine-readable `DECISIONS.json`.

Evidence is archived at `/workspace/astra/moon-rl/` on the pod and `holo-neurochir/moon-rl/` in the local checkout. Input payloads remain in the original read-only astra-power folder; the frozen manifest and hashes bind them to every recorded request. `FINAL_AUDIT.md` records the independent final report check. No third-party repository changes were staged or committed by moon-rl.
