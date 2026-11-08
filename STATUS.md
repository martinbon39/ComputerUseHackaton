# STATUS — ComputerUseHackaton

## ares — 2026-11-08 05:50 UTC (bilan final : STOPPED, pas de gain détectable ; papier publié)
- Décisif en cours : merge_cua_b050 contre l'original servi par Modal, sur split_test (120 tâches, GitHub runs 42442054879 et 42442467233). Règle : gain seulement si la borne basse de l'IC95 apparié sur 165 tâches est > 0.
- Réserve à serveur identique : fusion +6,6 [−6,7 ; +22,1] ; AlphaEdit +2,2. ExPO test −1,5. lmscale16 invalide (vLLM figé).
- Ensuite : lot 21 astra-free (H10) sur le compte Modal 2 ; branchement apparié prêt (online-eval) si Δ test > +3 ; papier en local (paper-v2), à publier après le verdict.

## Astra merge — 2026-11-08 02:33 UTC
- All9 full HF checkpoints independently verified and uploaded. Static health: CUA beta0.25/0.5 and Fara beta0.5 pass; CUA beta1 rejected for16/48 invalid GUI outputs (6 truncated). Fara0.25/1 and dualmean NOT RUN after ares scope amendment. No OSWorld gain claimed; online45/120 owned by ares.
- CUA layers12–23 beta0.5 and0.25 are ready in Modal account2, QUEUED for smoke/full51 after H8. Each has159 exact selected formulas and565 bitwise-preserved other tensors. Last local full HF copy: pod `/dev/shm/merge_cua_mid_b025`. No more constructions (cap9/9).
- Source of truth: `holo-neurochir/astra-merge/REPORT.md`, `CHECKPOINTS.json`, `STATIC_RESULTS.json`; pod `/workspace/astra/astra-merge/`, root backup `/root/astra_merge_evidence/`. Preserve `/dev/shm/astra_merge_cua` for RegMean. No owned GPU/dev server, harness/prompt changes or reserve/test episode exposure. Orchestrator service window is the only remaining dependency for the2 static screens.

## Now
- astra-ratio closed 2026-11-08T02:02:40+00:00: no admissible candidate; 10 lots/19 batched requests, 224 audited proposals, 0/8 verified useful fs+ for every learned dose. GPU released. Report and independent final review: `holo-neurochir/astra-ratio/`.
- Shared checkout on main; pre-existing changes block `git pull --rebase`. No stash/reset or unrelated staging.
- Astra 4B resumed by astra-4b-x: inherited lot 4 finished naturally at 18:33 UTC; all 24 baseline outputs recovered. Own GPU process and inherited report waiter exited.
- Experiment source of truth: pod `/workspace/astra/REPORT_4B.md` and `/workspace/astra/4b/PROTOCOL.md`.
- Budget: 8/60 lots reserved (current exploratory ceiling19). L16 and L24 both completed24/24 and are independently rejected: each fs+ answer8/8, fs- answer8/8, healthy valid non-answer8/8, invalid/truncated0. Round1 has no protected Pareto improvement. Lot8 multi-layer addition16/24/28 was externally preempted by ares at22/24; all22 outputs independently audited. Six observed fs+ answers make the required50% relative drop impossible even if the last2 were nonanswers. Both protected strata are complete and unchanged; no complete Pareto verdict. No owned GPU remains; PRIORITY excludes4b.
- Refreshed snapshot:22 fs+,53 fs-,275 healthy; `/workspace/osw_shared/STATUS.json` still has `go_fs=false`.
- Ares authorized provisional causal screening before40; PILOT_PLAN.md defines bounded rounds. Pilot directions exclude all five evaluated task IDs (train20 fs+/50 fs-,14 matched pairs).
- Independently audited baseline: 24 outputs / six contexts / five tasks; fs+ answer8/8, fs- answer8/8, healthy valid non-answer8/8, invalid/truncated0/24. This is not causal improvement.
- Installed runner SHAb5131a2f9f7742c5893c6fb07249698dc1a64272c3a8087d0f71d339e5c6d04d passed167 independent CPU checks and an installed-path smoke check. Native SIGTERM/parent-death recovery and multithread-safe commits are verified; mandatory ASTRA_EXPECTED_PARENT_PID from launching tmux shell, through fleet semaphore. Exact sealed lot8 resume retains22 and leaves2 calls; none launched. Model+processor snapshot8c88265a5a159bfd1492db9243733dd2e6e04a6e, canonical45 reserve,19-lot cap and random control stay enforced. Cache tensor contents were not rehashed; historical lots lack per-lot cryptographic identity. No validated causal intervention or weight edits.
- Provenance audit:5 evaluation tasks plus70 direction-training tasks;45 diagnostic IDs now reserved by ares in `/workspace/osw_shared/confirm_tasks.json`, verified tasks-map SHA03726f07b411869a7a4004b0f3c89ba37d89e948f34ac19cb70e4bb0c3cb5bb7. Exclude them from all further construction/screening. Shared at21:13:13UTC: fs+38/fs-107, official gate false; local snapshot remains22 positives.
- Dose amendment was registered before any completed terminal L24 output: retain multi-layer addition and all-layer writer projection, then L24 multipliers2/4/8/16 with paired fixed random controls, stop at first learned protection failure or admission. L28 and residual-projection multi are deferred. Maximum12 candidates; two completed rounds without protected Pareto progress stop this search. See pod4b/PILOT_PLAN_DOSE_AMENDMENT.md.
- Other project work belongs to ares and the existing sessions; this status describes Astra's current unit only.

## Next (ordered)
1. Paused pending fleet readmission; no automatic GPU relaunch. CPU recovery work is complete and installed. Exactly2 calls are missing from lot8, but its efficacy bound gives no scientific reason to spend a lot merely to complete it. Remaining registered round2 arms begin with writer projection, then paired dose/random controls. All subsequent jobs use fleet gpu_slot.sh with current PRIORITY/STOP review and explicit launcher PID. No official AUROC or final direction below40 development positives.
2. At >=40 local fs+ plus shared confirmation, seal full exposure/confirmation provenance before official analysis.
3. Test causal steering, compile matching writers only after behavioral criteria pass, then request ares diagnostic online validation.

## Don't
- Never read `split_test.json` or its results. Diagnostic data and production harness remain read-only.
- Never stop the inherited lot 4, production vLLM, other tmux sessions, or modify osw-analysis data.
- STOP_GPU belongs to the production guard: stop above 10 s/step, resume below 8.5; no automatic GPU relaunch.
- The inherited `finish_report.py` waiter finished at 18:33; report ownership is now astra-4b-x.

## How to verify
- Pod `/workspace/astra/4b/VERIFY_TOOLING.md` records independent checks and their limitations.
- CPU checks use `CUDA_VISIBLE_DEVICES=''`; generated behavior and online success are separate gates.

_Updated 2026-11-07 21:16 UTC by astra-4b-x._

## Astra 4B — 2026-11-07
- Isolated experiment: pod `/workspace/astra/4b`, report `/workspace/astra/REPORT_4B.md`; no weight edits or patch.
- Diagnostic snapshot: fs+15/fs-42, below required40 positives; official direction analysis remains gated.
- Budget4/60; original generation pilot resumed with latency guard, four complete outputs retained; finite post-run report updater notifies ares when GPU lock is released.
- Read pod `4b/runtime_status.json` for post-run counts. No automatic causal search or GPU restart. Production/test split untouched.

## Astra broad — closed2026-11-08T03:16UTC
- No admitted repair.204 responses across original/learned100/random100/learned50, independently audited. fs+ / true-finish answer counts (/16):15/15,8/3,16/16,12/9. Healthy16/16 and3 coherent texts each. Learned arms damage genuine finishes; no OSWorld gain claimed.
- Three verified full checkpoints on Modal1: broad_residual_p100, broad_residual_p050, broad_residual_random100. All owned APIs and SSH tunnel stopped. Random050 verifier cancelled per ares6235; p025/random025 NOT RUN.
- A14 forwards: donor reasoning+JSONprefix flips both construction conditional margins. B20 forwards: common rank1/2 projection has no admitted sign-gate arm. C tiny-panel keyAUROC confounded by length/step (both1).
- Dpilot24 forwards then expanded D112 total (36 interrupted at nullnote,76 recovery), within114cap and originaldeadline. Frozen source38, eligible37 (18fs+/19finishes), reserve45/eval6 excluded, priorfs_1 construction overlap disclosed. All runtime prefix-identity assertions passed.
- D task-group-CV primaryAUROC0.593567 vsstep0.785088/length0.795322; all24 secondary0.508772–0.695906. All37 prefer forced completed continuation. GateFAIL; no new checkpoint. Final independent numerical audit PASS WITH LIMITATIONS, no refit/GPU rerun.
- Evidence/report: holo-neurochir/astra-broad/REPORT.md; canonical small files /workspace/astra/astra-broad, large retaineddata /dev/shm/astra-broad and mirrored locally. No active job or automatic continuation; ares informed.

## Astra evo — 2026-11-08 03:10 UTC
- Weights-only search complete: 45 candidates,1000 forwards,26.5min,exit0; stopped after2 rounds without validation progress. Independent search audit PASS. Best uniform a=.2,b=0 in8 mixer/MLP groups across layers12–27; validation score .332341,fs+8/8 and true6/6 retain positive answer margins. No demonstrated selectivity or OSWorld gain.
- Full HF /dev/shm/astra_evo_best independently verified: CPU724 PASS (147 actually changed,544 outside scope identical), CUDA180/180 bitexact PASS;3texts correctT0, actionJSON at originalschema/EOS PASS. Corrected two checker assumptions with regressions and preserved failures; weights/prompts unchanged. Uploaded Modal1 holo-models:/ckpt/astra_evo_best,15files,32s,exit0. Handoff for ares in holo-neurochir/astra-evo/HANDOFF_ARES.md; online OSWorld and50step guard remain his scope. Own checkpoint retained; source caches no longer needed by astra-evo, untouched.
- Evidence/report holo-neurochir/astra-evo/REPORT.md; pod /workspace/astra/astra-evo. Reserve/test episode contents untouched. No running owned researchGPU process.

## Astra infeas — 2026-11-08
- Closed after independent CPU audit: semantic wording gain 1 unique task / 2 episodes; at most 2 tasks with mixed GIMP case, below gate3. Of 10 final answers on 11 infeasible DIAG episodes, 8 claim success.
- Scope: ares allowlist75 only, no reserve45/test content. No GPU or weight, prompt, harness changes; conditional k8/checkpoint/Modal stages NOT RUN.
- Evidence: `holo-neurochir/astra-infeas/REPORT.md`, `ANSWERS.md`, `VERIFY.md`; pod `/workspace/astra/astra-infeas/`. Ares owns archival; no next experimental action.

## Astra RegMean — 2026-11-08T03:08:27.708430+00:00
- CLOSED, no admissible candidate after centered contrastive RegMean on24 writers12–23, BF16 then FP16 with frozen factors. Task-CV overlap measured before fitting: no total span overlap; AUROC confounded by step/context length.
- Paired held-out DIAG k8: BF16 fs+15→13/16, true16→15/16; FP16 fs+15→16/16, true16→16/16. Healthy16/16 and3texts each,0invalid/error/truncation. Both fail required fs+−25pp. Independent artifact and behavior integrity PASS; no online OSWorld claim.
- FullHF checkpoints verified/uploaded Modal1, holo-models:/ckpt/regmean_cua_centered and regmean_cua_centered_fp16 (requires float16). Own GPUs/API8023/tunnel stopped; both temporary HF copies removed, 20746103045bytes freed. Captures/factors remain /dev/shm/astra-regmean (134MB).
- Source: holo-neurochir/astra-regmean/REPORT.md, RESULT.json, VERIFY_BEHAVIOR_*.json; pod /workspace/astra/astra-regmean. Reserve/test untouched. No next search scheduled; ares informed.

## Astra TACT — 2026-11-08 03:24 UTC
- CLOSED, no candidate. OT development AUROC0.98279 vs position0.88303 (position+reasoning length0.94872), only2 paired OT/CAL tasks; OA1 paired task cannot support grouped validation or a task-disjoint OA pilot.
- Seven complete paired k8 arms: all fs+15/16 answer. Original/Gate/literal/random true finish12/16, strong residual Add11/16; strong dose corrupts3/3 texts and makes1/24 healthy actions unproductive. No useful fs+ correction.
- Integrity independently PASS; efficacyFAIL. Ten starts,392 GUI+21 text complete outputs plus8 partial GateGUI,421 retained. No more search scheduled; random-scaled startup stopped before output after healthy-collapse trigger.
- No weight edit, checkpoint compilation/upload or online OSWorld. Reserve/test contents unopened; owned GPU process group ended and lock free.
- Evidence: `holo-neurochir/astra-tact/REPORT.md`, `RESULT.json`, `VERIFY_*.md`, `ARCHIVE_SHA256SUMS`; pod `/workspace/astra/astra-tact/`. Ares informed and owns fleet Git archival.

## Astra preamble — closed2026-11-08 before06:30UTC
- No candidate: learned dose2 exact preamble+verification0/8, healthy14/16 full-text and11/16 exact-action differences; matched random0/8. Generic Before7/8 produces no additional verification. All arms3/3 text controls;81/81 complete outputs,72/72 valid GUI JSON, noerrors/truncation.
- Independent numerical and checkpoint integrity PASS; behavioral gatesFAIL.158/160 capture forwards. Ares6456 stopped dose1 during construction; no dose1behavior and no online evaluation.
- All owned experiment servers/builder/tunnel stopped;41,492,037,065bytes of temporary checkpoints removed. Captures/factors and complete evidence retained at /workspace/astra/astra-preamble; local REPORT.md under holo-neurochir/astra-preamble. No new experiment scheduled. Ares owns archival.

## Astra power — closed 2026-11-08T07:35:08.656848+00:00
- Expanded paired replay complete and independently audited PASS: 880/880 responses, 55 distinct tasks (19 feasible false finishes, 20 strict score1 true finishes, 16 healthy). All admissible requested-source FS tasks included; five infeasible RegMean rows excluded, leaving one below target20. Reserve/test episode contents untouched.
- C−A false-answer delta −17.1pp [−28.9,−6.6]; true-finish delta −8.8pp [−18.8,0]; selectivity −8.4pp [−22.6,+5.9], unresolved. B FS −10.5pp [−25,0]; D FS +15.8pp [+5.3,+27.6]. C−D FS −32.9pp [−47.4,−19.7]. No online OSWorld gain claimed.
- Independent checks: checkpoints67/67, 55 source/payload reconstructions, 880 raw schemas, 1536 statistical fields; all112 bootstrap endpoints exact. Zero invalids/errors/truncations. Task bootstrap100000, four matched seeds. Sensitivity excludes three C construction/preservation tasks and retains C FS reduction.
- Canonical pod /workspace/astra/astra-power and local holo-neurochir/astra-power: REPORT.md, RESULT.json, VERIFY_FINAL.md/json, effects.png/svg, raw outputs and small evidence archive. Final mirror211 files/139656275 bytes verified by SHA256. Owned APIs/engines/tunnel stopped; production8000 health200, same PIDs. No further measurement; ares owns paper integration and fleet Git archival.

## Verif-study — closed 2026-11-08T07:53:27.368733+00:00
- Completed 1,072 final-screen verifications on 268 existing original-Holo episodes (66 false / 202 true successes, 90 tasks); no new rollout. T=0 detects 35/66 (53.03%, Wilson 41.16–64.57) and rejects 97/202 true successes (48.02%, 41.23–54.88). T=.8 majority: 40/66 versus 98/202.
- Independent raw-data reconstruction PASS WITH LIMITATIONS; requirement ratings audited to 493 yes / 95 no / 126 cannot tell. Same-model discrimination is weak; no OSWorld gain established. Feasible replay-valid branch repair evidence is 0/2 from one state; naive 1/4 includes an excluded infeasible task. V2 unavailable in local model caches.
- Evidence: holo-neurochir/verif_study/REPORT.md, RESULT.json, audit/FINAL_AUDIT.md; pod /workspace/astra/verif-study. Mirror 389 files / 127326635 bytes SHA256-verified, including 268 image and task references. Only shared original :8000 used, max concurrency 4; owned runner exited, no owned server remains. Ares owns paper integration and fleet Git archival.

## moon-combo — 2026-11-08
Trois combinaisons CUA/protection done rejetées hors ligne ; aucun gain global de vrais fini et aucun candidat admis en ligne. Voir holo-neurochir/moon-combo/REPORT.md et RESULT.json. Ressources possédées arrêtées et checkpoints rejetés supprimés.

## moon-rl — 2026-11-08 08:02 UTC, offline complete
- Anti .5 is the sole offline admission, through narrow qualitative next-action improvements; no numeric false-finish reduction. RL .5, RL 1 and Anti .25 rejected.
- Ares notified for 45+120 online confirmation. Preserve pod `/dev/shm/moon_rl_anti_b050` and donor `/dev/shm/moon_rl_tmax`; no online result claimed. Own8031 server and18031 tunnel stopped.
- Evidence and independent audit: `holo-neurochir/moon-rl/REPORT.md`, `FINAL_AUDIT.md`, `DECISIONS.json`; pod `/workspace/astra/moon-rl/`. Three rejected checkpoints deleted; raw evidence retained.

## Moon-vision — closed 2026-11-08T08:07:05.439587+00:00

- Vision-only CUA doses 0.5/1.0 and predeclared Holo extrapolation 0.25: no candidate admitted. FS+ answer A55/76, V05 57/76, V10 54/76, E025 57/76; required maximum43/76.
- 660 new GUI outputs valid, 9 text controls correct; original A220 reused. Independent tensor, source/SHA, raw-result and task-bootstrap checks PASS. Semantic fs+ verdicts FAIL / UNCERTAIN / FAIL. Healthy E025 preservation PASS on next actions; V05/V10 uncertain.
- All own servers/tunnel stopped; 31,119,988,803 bytes of rejected checkpoint weights removed after metadata archival. No online run requested. Evidence: `holo-neurochir/moon-vision/REPORT.md`, `DECISION.json`, and `/workspace/astra/moon-vision/`. Ares notified and owns shared Git archival.

## proof-anchor — 2026-11-08T08:07:16Z, complete
- Original Holo-3.1-4B revision8c88265a, frozen feasible astra-power cohort19fs+/20true:156/156 HF teacher-forced forwards, no generation or weight edits. Joint note/thought neutralization removes mean task margin fractions.821/.800; answer remains favored37/39. Between-stratum attenuation difference−.461[−2.362;1.499],p=.645: no equivalence claim.
- Best72-cell LOTO probeAUROC.639[.466;.803], rawstep.704; selected-winner1000-permutationp=.04196,Bonferroni72p=1. Oracle80% power needsAUROC.725 one-sided; absence of decodable information is not established. Supplemental MLP remains.621 with232/702 convergence warnings.
- Independent final audit PASS:10098 checks,exit0; all81 archived evidence files match pod SHA256. REPORT.md/RESULT.json/VERIFY_FINAL.md under holo-neurochir/proof_anchor and /workspace/astra/proof-anchor. No owned GPU/server/analysis job; ares informed, no continuation.

## moon-leak — 2026-11-08 08:29 UTC — CLOSED / NO-GO

- Four targeted head attenuations and two random controls complete; no tested arm reduces fs+ answer versus originalA. All1320 GUI outputs valid. No admitted checkpoint or online request.
- Attribution39 contexts/128 heads/24 DeltaNet layers complete; no supported selective intervention. Independent data/statistical/weight reviews PASS; retrospective no-progress stop-rule check FAIL disclosed, numerical budget7426/8500.
- All owned GPU/server processes stopped; six rejected checkpoints retired. Final reviewed archive: holo-neurochir/moon-leak/REPORT.md and DECISION.json. Ares informed; no further work scheduled.

## Rescue bench — 2026-11-08 09:13 UTC
- Pilot running on one VM; new frozen-Guard escalation runner and control independently CPU-reviewed. First guarded trial score0, valid replay. No gain established.
- Source: holo-neurochir/rescue_bench/REPORT.md and RESULT.json; raw ~/osw/rescue_bench. Next: complete paired pilot, then parity shards if resource slot released by ares; cutoff11:20, hard stop11:29:50.
