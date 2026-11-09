# Independent final verification — PASS

Reviewer: independent `final_verifier`, 2026-11-08 07:34 UTC. The reviewer did not create the cohort, runner, checkpoints, or analysis. CPU only; no generated model requests, no GPU use and no reserve/test episode access. Only `verifier_recompute.py` and `VERIFY_FINAL.{md,json}` were written by this reviewer.

- **RAN:** direct cohort/source and pool-coverage checks; independent reconstruction of all 55 payloads; independent parsing/schema validation of all 880 responses; seed/payload/receipt/model-root checks; server-log review; Wilson and 100000-replicate paired task-bootstrap recomputation; final report and figure review; direct cleanup checks.
- **PASSED:** all executed checks. Four arms complete at 220/220; 880 unique scheduled draws; zero missing, duplicated, invalid, transport-error or truncated responses. All 1536 compared result fields agree within absolute tolerance 1e-13. Maximum error over 1072 floating-point fields is 1.11e-16; all 112 bootstrap interval endpoints agree exactly.
- **CORRECT:** the recorded measurements and reported statistics match the frozen next-action replay estimands. C reduces false-finish `answer` frequency versus A, including after removing its three overlapping construction/preservation tasks. C-versus-A selectivity remains unresolved because its interval includes zero. D increases false-finish `answer` frequency; C−D is a valid secondary paired contrast.
- **NOT RUN:** online execution or OSWorld success evaluation; semantic usefulness of generated nonanswer continuations; GPU-resident tensor attestation; additional model generations. No selective online repair or general impossibility of repair follows from this experiment.

## Cohort and provenance

Cohort v2 SHA256: `2faee8f1af5a1243b8c8bacbf0369e4e035ab9dc336307c9f6678c0d134c24d0`.

Frozen SHA256: `9bf07af1f630ffbee0f628347270dff9c3abe068aa9fb76c9c8c747e47585839`.

All 55 selected `result.txt`, evaluator JSON, trajectories, meta files and source hashes were read directly. The independently checked composition is 19 feasible terminal false finishes with exact score0, 20 feasible terminal true finishes with exact score1, and 16 intermediate healthy contexts from feasible score1 episodes. Task IDs are globally distinct, in the75-task DIAG allowlist, and outside reserve45 and the prior evaluation exclusions. No selected evaluator is `infeasible`, including list-valued evaluator functions.

For the16 healthy steps, the verifier independently recomputes screen differences and previous-action repetition rather than importing the maker's taxonomy. Every selected step meets the nonrepeated, >=1% changed-pixel rule and precedes the terminal `answer`. This is a structural history label, not proof that a newly generated continuation is useful.

The verifier additionally scans all136 episodes in the two requested passes over68 admissible tasks, and the original RegMean false-finish rows. Their union contains exactly19 distinct eligible false-finish tasks, all selected. Five of the19 original RegMean false-finish tasks have officially infeasible evaluators and are rejected. Pass1 has12 eligible false-finish episodes and pass2 has14; repeated task IDs are deduplicated across sources. The target shortfall of one is therefore correctly reported for the specified source pool.

The v1 partial-credit task was replaced before the v2 freeze and first model request. The selected sources all satisfy strict score0/1 requirements. Construction/preservation flags agree with the historical broad manifest. Removing their union leaves18 false finishes,19 true finishes and15 healthy tasks, with identical exclusions for all arms.

## Payloads, responses and service identity

All55 frozen message payloads were independently reconstructed without calling the maker's `rebuild()`: exact system text, prior assistant action JSON, tool outputs and re-encoded screenshots match. Assistant history stops before the selected action. There are52 payloads with three images, two with two and one with one; absent history is not padded. Source/probe hashes, schema hash and generation settings match the freeze: T0.8, top_p0.9, top_k20, max_tokens3072, medium reasoning, thinking enabled and exact JSON schema.

Every arm contains exactly one draw for each of the55 tasks and each seed17000–17003. All880 payload hashes, full row objects, arm/model identifiers and time ordering agree with the freeze. Content is independently parsed and validated against the frozen schema; stored parsed/tool/answer/nonanswer/invalid fields agree. All880 finish with `stop`, with no transport error or length truncation. Completion-token counts equal recorded token-ID counts for every response; observed token-count ranges are A138–1141, B94–971, C137–1054 and D140–1203.

Start/end receipts account for exactly220 calls per arm; B consists of the retained4 pilot calls followed by216 calls. Each receipt has zero retries, eight workers, the frozen hash and the correct `power_A/B/C/D` root. Independent read-only inspection of pod logs confirms220 successful chat POSTs per arm and identical numerical service arguments: vLLM0.23.0, BF16, context32768, max_num_seqs32, KV8589934592 bytes, GPU utilization0.20, prefix caching enabled, qwen3 reasoning parser and port8024. Log hashes are retained in VERIFY_FINAL.json.

The first D server attempt failed loading a Triton shared object from a noexec cache before the API became ready: its retained log contains no chat-completion POST. The recovery precedes the first recorded D call, returns to the default cache locations and produces one complete220-call sample with no duplicate task/seed. This infrastructure failure does not remove or replace an observed response.

Checkpoint content identity and norm matching are covered by the separate independent `VERIFY_CHECKPOINTS.md/json` audit, now PASS67/67. The corrected checker preserves the initial failure and uses the historical D per-tensor control_scale; no weights or bit-exact formula criterion were changed. This final verifier checks recorded model roots and service logs, but does not independently attest GPU-resident tensors. D's realized norm ratio and restricted factor-randomization interpretation are accurately disclosed in REPORT.md.

## Independent numerical recomputation

Command: `/home/orbit/osw/venv/bin/python experiments/weight_edits/power_cohort/verifier_recompute.py --phase final` — exit0.

Final script SHA256: `ff4e26999c725ea1f7c9bd10859518897142eecdd462c3a7abcf1d686a5616cb`.

The verifier does not import or invoke `analyze.py`. It reclassifies raw content, recomputes four-draw task means and pooled counts, uses a separately written Wilson formula, and applies explicit `Generator(PCG64(20261108))` task resampling with100000 replicates. Tasks are resampled independently within strata, with common task indices across arms. Selectivity is Δfalse minus Δtrue. Full and overlap-excluded cohorts both agree with RESULT.json, including every per-task rate/delta and C−D contrast.

| Arm | False-finish answers | True-finish answers | Healthy-context answers |
|---|---:|---:|---:|
| A |55/76|75/80|5/64|
| B |47/76|66/80|0/64|
| C |42/76|68/80|2/64|
| D |67/76|75/80|8/64|

Selected independently reproduced effects, in percentage points:

| Contrast | False finishes: delta [task-bootstrap95] | Selectivity [task-bootstrap95] |
|---|---:|---:|
| B−A |−10.5263 [−25.0000,0.0000]|+0.7237 [−16.1184,+16.3158]|
| C−A |−17.1053 [−28.9474,−6.5789]|−8.3553 [−22.5658,+5.9211]|
| D−A |+15.7895 [+5.2632,+27.6316]|+15.7895 [+5.2632,+27.6974]|
| C−D |−32.8947 [−47.3684,−19.7368]|−24.1447 [−41.0526,−7.2368]|

Without C construction/preservation tasks, C−A false-finish delta is−16.6667 [−29.1667,−5.5556] and selectivity is−8.7719 [−23.7573,+6.2135]. C−D false-finish delta is−33.3333 [−48.6111,−19.4444] and selectivity is−25.4386 [−43.2018,−7.6754]. Full sensitivity estimates, Wilson intervals and arm-rate task intervals are retained in VERIFY_FINAL.json.

REPORT.md tables and the rendered effects.png were reviewed against this recomputation. Their rounded numbers, signs and interval endpoints agree. The report correctly distinguishes individual unadjusted intervals from multiplicity-corrected inference, describes Wilson intervals as descriptive despite within-task dependence, states that four fixed seeds define each task mean, and warns that degenerate empirical bootstrap intervals do not prove a population rate with certainty. It reports no online OSWorld gain and does not equate reduced `answer` frequency with useful continuation.

## Completion and archival

Direct read-only process/socket checks found no owned API/engine PID alive and port8024 closed. Production PIDs192904/193632 remain present and `/health` on8000 returns200. The reviewer did not stop any process.

The complete local evidence passed. At a supplemental mirror check, D raw responses and CLEANUP.json were not yet on the pod; the coordinator was notified and will synchronize final artifacts and issue a separate SHA256 mirror receipt. This pending copy does not affect the audited local measurements. Two supplemental remote-check attempts stopped on absent mirror files; no measurement or acceptance criterion was altered.
