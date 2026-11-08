# moon-leak log

## 2026-11-08 07:22 UTC — attribution fidelity gate
- What: Prepared no-gradient final-token attention/DeltaNet attribution and frozen generation evaluation. BaselineA220 copied, exact contexts/payloads/seeds validated.
- Why: Separate causal reading of JSON note/thought from visual/task evidence before weights-only head attenuation.
- Verified: Pilot332 forwards PASS; repeated hidden states/logits identical; model parameter versions unchanged. First attempt failed due HF multimodal position helper; two later attempts exposed SDPA nondeterminism. All logs preserved. Independent review found GQA/kernel confound; explicit eager final-token attention and deterministic settings fixed it without relaxing equality checks.
- Result: Full39-context attribution admitted. No candidate/online claim. Failed pilots are engineering diagnostics, excluded from head ranking.

## 2026-11-08 07:25 UTC — frozen source portability
- What: Replaced optional original_pod_path lookup with a single pinned bundle of all39 recorded current-step objects.
- Why: New strict power selections include local-only sources. The first full process stopped before its sixth context, after5 complete contexts/825 forwards.
- Verified: All39 whole-trajectory SHA256 match frozen source_hashes; each bundled step equals exact source index t. Independent provenance review PASS. Resume accepts only complete contexts and restores COUNT825; full total remains6435.
- Result: Same frozen data and intervention; resumed without duplicate measurement.

## 2026-11-08 07:54 UTC — attribution and first screen
- What: Completed39-context attribution and selective4×0.5 frozen generation screen; measured original3 text controls.
- Why: Test both the final-query channel premise and the practical weights-only intervention, distinguishing attribution from behavior.
- Verified: Independent attribution/provenance/aggregate reviews PASS;6435 forwards,312 exact-zero controls. Candidate724-tensor audit PASS. Independent screen review validates220 paired draws, schema and server receipts. A/candidate3 text outputs including token IDs identical.
- Result: Selective4×0.5 rejected: fsanswer63/76 versusA55/76; true76/80 versus75/80; healthy58/64 versus59/64;220 valid. Wrong translation occurs in original too. Candidate and temporary original text servers stopped by owned PID; failed checkpoint retired, evidence preserved. Before first generation inspection the optional2/6-head sweep was replaced by literal raw-strength4 half/zero to match user scope, candidate cap reduced6→4; see protocol amendment.

## 2026-11-08 08:12 UTC — targeted sweep closed
- What: Finished selective4×0 and raw-strength4×0.5/0, bringing targeted arms to the fixed cap4. Started the first of two matched random zero-dose controls. Copied and hash-verified the58 frozen schema/manifest/payload files into the owned folder.
- Why: Cover both selective ranking and literal strongest fs+ channel ranking while preserving a complete paired offline record.
- Verified: Each full checkpoint audited724 tensors before service; independent generation audits PASS for all4 arms. All880 targeted GUI outputs valid, no errors/truncations. Selective zero fs71/76, true74/80, healthy57/64; raw half57/76,73/80,60/64; raw zero56/76,71/80,60/64.
- Result: All4 targeted candidates fail efficacy and selectivity; selective zero also fails healthy protection. All4 failed checkpoints retired after owned-PID server shutdown. Controls and final report remain. No online request.
- Process reservation: Independent reconstructed attribution budget7426<=8500; earlier sum omitted two170-call attempts. Retrospective audit flags continuation after2 equality failures without execution progress (exit1). The deviation and limits are disclosed in PROTOCOL/REPORT/VERIFY_BUDGET; measured code/logs unchanged, no further attribution calls.

## 2026-11-08 08:22 UTC — offline NO-GO and cleanup
- What: Completed both random controls,220 GUI+3 text each. Decision NO-GO recorded08:20UTC and sent to ares. No online launch requested. Generated attribution/screen figures and complete owned frozen-data snapshot.
- Why: Close the fixed4-targeted+2-control experiment with a direct comparison against matched random head suppression.
- Verified: Independent audits PASS all6 arms/1320 GUI outputs, all valid, no errors/truncations. Random selective fs67/76,true75/80,healthy56/64; random raw64/76,77/80,60/64. Direct selective advantage versus control: ranked−6.51pp CI[−18.42,+3.88], raw+3.03pp [−12.63,+18.75]; neither resolves an advantage. Text audit6/6 complete: every translation wrong, arithmetic/Linux correct. CLEANUP.json confirms no owned process/GPU PID or remaining checkpoint.
- Result: No arm reduces fs+ answer versus A55/76. All targeted edits and controls rejected. No online success claim. New requests1320GUI+21text; originalA220GUI reused. Fresh final report review and archive checksum remain; budget/stop-rule reservation preserved.

## 2026-11-08 08:29 UTC — final independent review and archive
- What: Closed REPORT.md, DECISION.json and the owned repository/pod archive after fresh-context review.
- Why: Preserve an independently checked negative result before the09:45 deadline.
- Verified: VERIFY_FINAL.md SHA256 9bd572e080fd2d1e2b1151cc9f9cf6f6a9c4b7e3e4ce4b7ad63c98673740252f; raw counts, pairings, intervals, attribution scope, limits and cleanup correct, no material findings. Numerical budgets PASS; the retrospective stop-rule check remains FAIL. Local syntax13 scripts, JSON70 files and frozen58 file hashes checked; four plot artifacts present.
- Result: CLOSED / NO-GO. No admitted checkpoint, no online request, no owned GPU/server left. All future inference would be a separate experiment.
