# Independent audit — finalized original pilot

RAN: read-only CPU audit of all four reserved jobs, finalized raw shards and markers, pilot_manifest.json, recorded system-prompt schemas, pilot_summary.json, runtime_status.json, and the three generation logs. No model/GPU, budget write, process/STOP inspection, report mutation, forbidden split, or /workspace/runs access.

PASSED: exact six expected contexts, four samples per context, seeds 4000–4003; 24 unique complete generations, no missing/duplicate context-sample keys, no truncation or malformed thinking/EOS boundary. Every raw output matches its reserved batch, immutable manifest hash, selected row/index, and seed. Both strict Step validation and the recorded JSON Schema validate all 24 outputs. Diagnostic allowlist, canonical data paths, and deterministic task grouping pass.

The six contexts represent five unique diagnostic tasks. One task supplies both an fs- terminal and a healthy nonterminal context; it must remain one cluster in task-level bootstrap or split procedures. Counts independently match both summaries:
- fs+: 8/8 answers; invalid/truncated 0.
- fs-: 8/8 answers; invalid/truncated 0.
- healthy: 8/8 valid nonanswers; invalid/truncated 0.

All four durable reservations remain charged. Batch1 contains six conditional probes. Batch2 produced zero complete outputs and is explicitly inadmissible because its top_k differed. Batch3 preserved four complete outputs; its log records a fifth started generation that was interrupted without a completed record. Batch4 contains the remaining 20 complete outputs. No complete output was omitted: logged completed records agree with raw-file counts. The 24-sample denominator is the completed resumed k=4 design; interrupted computation is separately disclosed and is not a scored invalid sample because no final output exists.

The union of task AND context exposures in every reserved job, including failed/interrupted jobs, is exactly covered by pilot_original_probe.jsonl: six contexts/five tasks. The earlier confirmation-exposure limitation is therefore future-only for the currently audited four-job ledger. Additional jobs must extend the complete exposure accounting before official confirmation.

Completed generation-call durations: sum 1012.721013 s, mean 42.196709 s, median 15.204074 s, range 3.660927–235.832420 s (n=24). Completed probe-call durations sum 10.737537 s (n=6). These logged elapsed calls exclude loading/cooldown and exclude interrupted work; they are not wall-clock experiment cost.
Maximum recorded peak_reserved_gb: 11.848908800 decimal GB. This is the maximum of cumulative per-process PyTorch reserved-memory high-water marks sampled after calls, not total device usage, model-only memory, or resident host memory.

Conditional-probe versus observed generation-rate comparison recomputes to mean absolute error 5.59491589390431e-06, maximum absolute discrepancy 1.75234592312279e-05, across six original contexts. The probe is teacher-forced probability of the first answer token after recorded reasoning/note/thought, not unconditional P_answer. Saturated original contexts do not validate intervention ranking or calibration. There was no intervention, causal comparison, official AUROC, or surgery.

CORRECT: finalized original pilot accounting and reported totals are supported by raw records. NOT RUN: causal efficacy, disjoint confirmation, official B/C/D, intervention calibration, or online improvement.

Raw/artifact hashes, per-context results, timing breakdowns, schema hashes, and exposure checks: /workspace/astra/4b/pilot_resume_independent_audit.json.
Frozen pilot manifest SHA-256: ed4b25f13edad291c9e09c8954d40739136ecb7d37971f59307d88e7a6820a45

Verdict: PASS_FINALIZED_ORIGINAL_PILOT_ONLY.
