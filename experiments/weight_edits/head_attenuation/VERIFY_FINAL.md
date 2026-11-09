# Fresh independent final verification

Reviewed read-only on 2026-11-08 UTC. No model, GPU, server, generation, network, reserve45, or split_test access was used.

## Verdict

**RAN:** independent CPU reconstruction from `attribution.jsonl`, all seven GUI JSONL files (original A plus six arms), all seven text-control files, the six screen/audit pairs, control contrasts, frozen manifest/schema/payload receipts, run/completion receipts, six weight-audit receipts, budget evidence, decision/status/log, and cleanup receipt.

**PASSED:** artifact completeness, frozen-key pairing, JSON/schema validity, raw count reconstruction, bootstrap signs/intervals, matched-control algebra, attribution completeness/arithmetic, receipt consistency, and cleanup. This is not a full process-compliance PASS.

**CORRECT:** the reported **NO-GO** is supported. It was recorded at 08:20 UTC, before the 09:45 UTC deadline. No tested arm reduced false-finish answers versus A, every selectivity point estimate versus A is negative, no qualitative GUI improvement is claimed, and no checkpoint is admitted.

**NOT RUN:** model or GPU execution, checkpoint reconstruction or direct tensor reinspection after retirement, generation requests, online OSWorld/task-success evaluation, and any reserve45/split_test analysis.

## Recomputed evidence

Raw `content` was parsed independently, its tool name was used to reconstruct `answer`/`valid_nonanswer`, and all outputs were checked against the frozen schema. Each arm has exactly the same 55 tasks × seeds 17000–17003, with no missing, extra, or duplicate task/seed key; every frozen row and payload digest agrees.

| Arm | fs+ answer /76 | True-finish answer /80 | Healthy valid nonanswer /64 | Selective reduction vs A |
|---|---:|---:|---:|---:|
| Original A | 55 | 75 | 59 | reference |
| Selective4 ×0.5 | 63 | 76 | 58 | -9.28 pp |
| Selective4 ×0 | 71 | 74 | 57 | -22.30 pp |
| Raw-strength4 ×0.5 | 57 | 73 | 60 | -5.13 pp |
| Raw-strength4 ×0 | 56 | 71 | 60 | -6.32 pp |
| Random selective-layer control ×0 | 67 | 75 | 56 | -15.79 pp |
| Random raw-layer control ×0 | 64 | 77 | 60 | -9.34 pp |

All 1,320 new GUI outputs are syntactically valid and schema-valid, with zero stored errors or truncations. The six reported task-bootstrap intervals reproduce exactly. The two direct control contrasts also reproduce: selective-family differential selectivity -6.51 pp, 95% interval [-18.42,+3.88], and raw-family +3.03 pp, [-12.63,+18.75]. Layer multiplicities and random exclusions match within each family. Both controls correctly use the preregistered zero-dose fallback because neither targeted dose passed the numerical gates.

The attribution file contains 6,357 records for 39 unique finish contexts (19 fs+, 20 true finish). Every context has exactly one baseline, eight zero-mask controls, all 128 full-attention heads, one same-length note/thought neutralization, 24 DeltaNet final-output patches, and one completion record. All 312 zero-mask effects are exactly zero; the final counter is 6,435. Independently recomputed neutralization, selected-head, raw-head, and DeltaNet means match the report, including the top-four sets. The intervention is represented accurately as final-query link masking, while the candidate edit is represented accurately as a global all-position `o_proj` column edit.

The requested screening scope is complete: four targeted arms and two matched random controls, 220 GUI draws per arm, plus three T0 text controls for each arm and original A. Arithmetic and Linux renaming are acceptable for all seven models. The translation is wrong for every model (`dossier ... renommé` is rendered as a file being “opened” or “processed”), so the report correctly declines a general text-health PASS.

All six preserved tensor-audit receipts report 724 tensors, exact declared `o_proj` column scaling, unchanged non-target bytes/artifacts, and PASS before serving. Because all six checkpoints were retired, this review verifies those receipts and their consistency with specs/build logs rather than reopening weight files. `CLEANUP.json` records all 14 owned PIDs absent, no owned GPU PID, and no remaining checkpoint entry.

The attribution accounting reconstructs 7,426 attempted forwards, within the amended 8,500 cap; the main run is 6,435/6,500. Counts 3/170/170 are control-flow inferences, as disclosed. Attempts 3 and 4 failed the same exact-repeatability gate without execution progress, after which the passing repair and main run continued. The conservative two-round stop rule therefore **failed**. The numerical caps pass, but the process as a whole does not.

## Findings and remaining limits

No material inconsistency or misleading inference remains in `REPORT.md` or `DECISION.json`.

The evidence is exploratory because the same 39 finish contexts select and estimate the heads, and the same frozen cohort screens behavior. Same-length neutralization retains boundary-crossing tokens; a DeltaNet output substitution is not attribution to a single recurrent edge; final-query head masking does not cover earlier/distributed routes; and global `o_proj` attenuation changes every use of each head. Original GUI A also used different serving capacity (0.20/8 GiB versus 0.15/6 GiB), the healthy metric is a valid-nonanswer proxy rather than task success, qualitative GUI improvement was not assessed, and no online outcome was measured. These limits narrow the negative conclusion to the six tested edits and controls; they do not weaken the NO-GO decision for this experiment.
