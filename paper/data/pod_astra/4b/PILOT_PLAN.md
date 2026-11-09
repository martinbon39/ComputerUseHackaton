# Provisional causal pilot — 2026-11-07 continuation

Scheduling evidence: ares explicitly authorized exploratory steering in its 18:33 transcript; continuation acknowledged via argos at18:40. Original protocol still governs. No official AUROC or frozen final direction below40 admissible fs+.

Data: refreshed diagnostic-only manifest_v2 contains22 fs+,53 fs-,275 healthy rows. All five original pilot task IDs, including every pass of those tasks, are excluded from direction training. The original24-output reference remains fixed. This is a small Chrome pilot, not independent final confirmation.

Directions: provisional raw and train-position-matched residual/MLP diff-of-means; use matched residual for the first pilot round. Matching, normalization and mean-difference norms use training rows only. Layer choices are fixed anatomically (16,24,28), not selected by AUROC. Direction signs are fs+ minus fs-.

Round1: single-layer constant additions at16,24,28, alpha equal to minus that layer's training mean-difference norm. Each job uses the same six contexts/k4 seeds4000–4003 and original production sampling. Evaluate healthy contexts first, then true-success terminal contexts, then false-success terminal contexts.

Round2, only after interpreting round1: multi-layer addition, multi-layer residual projection, and common-direction MLP+attention writer projection across all layers. Exact settings and matching-hook CPU checks must be committed to each job before generation. No weight compilation during this provisional stage.

Fixed admission: fs+ answer decrease >=25points and >=50%relative; fs- baseline>=.8 and decrease<=5points; healthy valid non-answer decrease<=5points; invalid/truncated increase<=5points. The current perfect reference and8 outputs per stratum make one protected failure sufficient to reject the fixed24-output candidate, even if every ungenerated protected output were ideal.

Early rejection preserves every completed output and writes an explicit charged aborted/rejected marker with the planned denominator and bound. It never treats partial output as a complete efficacy estimate. External STOP interruptions do not count as evidence of causal rejection.

Round progress means a lower fs+ answer rate while all protected rates satisfy their fixed constraints. Two consecutive completed rounds without such improvement stop this provisional search and report the measured negative result. Maximum12 scientific candidates overall; at most15 additional generation/scoring lots in this exploratory authorization, including failures/resumes; total experiment budget remains60.

One GPU process, PyTorch cap28GB, observed total process memory must remain below30GB, 30s cooldown. STOP_GPU belongs to ares: stop>10s/step, resume<8.5. No automatic relaunch; each next job requires current scheduling/guard review. Production vLLM and every other tmux/process stay untouched.

Before any later official analysis/confirmation, update the full exposure ledger and reserve disjoint diagnostic tasks. A provisional pilot success cannot authorize patch saving or serving; the official data, behavioral confirmation and matched-compilation gates still apply.

## Round2 settings committed before any round1 efficacy output

If the protocol calls for round2, evaluate three candidates, each against the same fixed24-output reference: (1) additions at layers16,24,28, alpha=-1 with layer_scales equal to each matched training mean-difference norm divided by3; (2) residual projection at16,24,28, alpha=1 using each layer direction; (3) common matched residual direction from layer24, alpha=1 at all32 text-layer MLP and attention output writers. Linear-attention out_proj and full-attention o_proj are both included; text/image embeddings and tied lm_head are excluded from this writer scope. All writer modules must be biasless torch.nn.Linear with the expected output dimension. The future matching weight edit is Wprime=(I-alpha*u*uT)W for exactly these writers. Real-arithmetic equivalence does not promise BF16 bit identity or behavioral equivalence. No weight edits are authorized by this preparation. Runtime resource guards, early protection rejection, split exclusions and fixed admission thresholds are unchanged.
