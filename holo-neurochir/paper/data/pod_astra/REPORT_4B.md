# Astra 4B — anti-false-success experiment

Updated 2026-11-07T19:44:26.897620+00:00. **The first provisional causal candidate (negative addition at layer16) is rejected: no observed reduction in false terminal answers. Layer24 is the next predeclared test and has been launched. No checkpoint weights edited, no patch saved, no online improvement demonstrated.**

## Current state

- Budget **7/60** charged lots; at most15 additional exploratory lots beyond the original4, maximum12 scientific candidates. Failures and resumptions count. No refunds.
- Original inherited lot4 finished naturally at18:33 UTC; its20 outputs plus the4 preserved outputs were recovered. The GPU job and inherited report waiter were not killed.
- Lot5 tested layer16, saved8 healthy outputs, then exited on external STOP_GPU. Lot6 resumed exactly16 missing outputs with unchanged intervention, contexts and seeds. All24 are now complete and independently audited. Lot7 is the planned layer24 candidate if reserved in the ledger above.
- Current diagnostic manifest: 22 fs+, 53 fs-, 275 healthy. Shared status at2026-11-07 19:32:50: 32 admissible fs+, go_fs=False. Official direction analysis remains gated by shared and local40-positive requirements.
- One owned GPU process at a time; PyTorch allocation cap28 decimalGB, total process must remain below30GB. Cooldown30s. STOP_GPU remains owned by ares: stop>10s/production step, resume<8.5. No automatic GPU relaunch. Production, other tmux sessions, source data and harness are untouched.
- No test split or test result has been accessed. All selected tasks are diagnostic.

## Behavioral result

Six Chrome contexts / five task groups, k4, seeds4000–4003. Exact recorded replay, thinking enabled, T=.8, top_p=.9, top_k20, max3072; recorded structured JSON schema. Invalid/truncated samples stay in the denominator.

| Arm | fs+ answer | fs- answer | Healthy valid non-answer | Invalid/truncated | Decision |
|---|---:|---:|---:|---:|---|
| Original |8/8|8/8|8/8|0/24|Reference|
| Layer16 addition, alpha=-1.2008471488952637 |8/8|8/8|8/8|0/24|Reject: zero efficacy reduction|
| Layer24 addition, alpha=-5.544219493865967 |Pending|Pending|Pending|Pending|Running|

Layer16 preserves the protected outcomes but fails both fixed efficacy thresholds (>=25 percentage points and >=50% relative reduction). Both fs+ contexts remain4/4 answer; all eight answer contents still claim task success, none is a readable refusal. Protected Pareto progress is false. The paired task bootstrap gives observed binary deltas[0,0]; with only two tasks per stratum those degenerate descriptive intervals do not establish absence of effect on unseen tasks.

Independent audit:48 original/candidate raw outputs satisfy strict Step validation and the complete recorded JSON Schema. No duplicate, missing, truncated or invalid sample. `4b/VERIFY_L16_RESULT.md`, `4b/pilot_c1_add_l16_metrics.json`, and `4b/pilot_c1_add_l16_independent_audit.json` contain evidence and hashes.

## Provisional directions and confirmation boundary

The fixed pilot snapshot is350 rows (manifest SHA256ced58cdc941ea79c9bbe032cd6180e85635eff7b0c7ef5d4e2d5eff87be69fcf). Directions train on20 fs+/50 fs- across70 tasks after excluding every pass of all five evaluated task IDs. Matching on log1p(step) and log1p(context length), with train-only scaling and unique pairs, retains14 pairs. Direction sign is fs+ minus fs-. The pilot uses matched residual directions, bundle SHA256f975153853fde0086ff6c3d7c13ddb834db96726857a08b162b8f4ea97f57856. No official AUROC has been computed or final direction frozen.

The shared confirmation reserve is45 diagnostic tasks, exactly split_diag minus70 construction tasks minus5 pilot tasks. Canonical source `/workspace/osw_shared/confirm_tasks.json`; tasks-map SHA25603726f07b411869a7a4004b0f3c89ba37d89e948f34ac19cb70e4bb0c3cb5bb7; whole-file SHA256a47533d90a7d4e59bb81bd191529c41adf9af2d3676100539bd4d603c14b67cb. Exact copy `4b/confirm_tasks.canonical.json`; normalized IDs `4b/confirm_task_ids.json`. These IDs are excluded from all further construction and screening and reserved for confirmation of a committed candidate. Future official preparation must enforce this complete exposure boundary, not only the five pilot exclusions.

Frozen label semantics remain compatible between f6ffd521765d and shared1e5079afb500; the latter only adds provenance metadata. The existing192-case real-parser proof remains valid. A correct refusal still uses answer: tool-level P_answer alone cannot recognize that correction. One pilot fs+ context is officially infeasible; the observed L16 answers continue claiming completion. A schema-valid non-answer does not establish task progress.

## Next bounded tests

Round1 consists of the predeclared single-layer additions16,24,28, each at minus its train-only matched mean-difference norm. Layer16 is complete with no progress; layer24 is launched; layer28 is pending. A round is not complete until its predeclared candidates are assessed.

If round2 is needed, committed settings are: additions at16/24/28 scaled by each norm/3; residual projection at16/24/28 with alpha1; and common layer24-direction ablation of all32 text-layer attention+MLP writers with alpha1. The latter includes linear-attention out_proj and full-attention o_proj, excludes embeddings/tied lm_head, and matches Wprime=(I-alpha*u*uT)W in real arithmetic. BF16 equivalence still needs behavioral verification. Details and stop rules are in `4b/PILOT_PLAN.md` and authoritative `4b/PROTOCOL.md`.

Two consecutive completed rounds without protected Pareto improvement stop the causal search. No editing/compilation before the fixed behavioral criteria and disjoint diagnostic confirmation. No online serving before matching dense/sparse weight compilation and patched-vs-steered P_answer within5 points per stratum. Only then save via holo.surgery.save_patched and notify ares for diagnostic online tests.

## Implementation verification and provenance

Independent preparation/metrics checks37; pilot runner19+17 new checks; multi-layer/writer suite48; integrated STOP-resume suite105 total (20 new plus85 existing), CPU1 and CUDA uninitialized. The resume code binds prior raw output, marker snapshots, budget reservations, intervention identity, manifest, sampling and seeds, preserves completed samples, carries protection denominators, and finalizes even charged zero-output interruptions. Partial efficacy remains rejected.

Installed runner SHA25624eb845454aba5048e5af768d5a28c231782232ebc40925a26e19b3bdc9314bd; metrics SHA256216462185bc4e5f25ba90d203b387b8b72dbf8cf4f38e97ae22fe30d70df7874; resume helper SHA25690ba64a91fea019d8439b1954e5d07ee9129ce64d7e6eb3b14bbb4ff436aeb7f. Legacy lot5 did not reserve its runner hash; its archived code is bound to the prior independent CPU report. Lot6 directly reserves the verified runner hash.

Reports: `4b/VERIFY_TOOLING.md`, `VERIFY_RESUME.md`, `VERIFY_RUNNER_RESUME.md`, `VERIFY_PILOT_RESUME.md`, `VERIFY_CAUSAL_PILOT_CPU.md`, `VERIFY_ROUND2_CPU.md`, `VERIFY_STOP_RESUME_CPU.md`, and `VERIFY_L16_RESULT.md` under4b. Historical synthetic aggregation fixture was superseded, not edited to pass; current independent suites are identified separately. Teacher-forced first-tool-token probe remains unvalidated for intervention ranking and is not used to select candidates.

Prior narrative is preserved in `4b/REPORT_4B.before_l16_result.md` and `4b/REPORT_4B.pre_resume.md`. Raw outputs, immutable preparation bundles, job files, charged ledger and markers remain the audit trail. Initial checkout pull was blocked by pre-existing shared changes; no stash/reset or unrelated staging was performed.
