# Round 3 — preregistered operational protocol

Development: existing immutable Round 1 snapshot seeds 0–5 only. Heldout: seeds 6–7, no reading for tuning. Online: seeds 50–51 once after freeze, only if causal success and compiled patch validated. No new acquisition from protected diag paths.

A batch is a fixed list of contexts, four fresh generations per context, every started generation batch logged before generation in /workspace/astra/budget_r3.log (max 40, including failed batches). Holo.generate: T=.8, p=.95, k=20, max512, thinking off. Same RNG per context and replicate across arms. Original recorded action is never teacher-forced.

REPEAT: on loop+ contexts, fraction matching previous recorded action by taxonomy.same_action, including crop offsets, strict <15 pixels. HEALTH: union of loop- and success rows, valid parse+adapter and same tool as recorded action, strict <15 pixels for clicks. Failed parse is false for both; separately report parse rate to expose degenerate suppression. Report any overlap of loop+ and health.

Success: repeat <= .5*original and health >= original-.05. Zero baseline repeat cannot establish suppression. Per-step four draws are dependent; report counts, not inflated independent-sample certainty. Main screen: 12 loop+ and 12 healthy contexts randomly sampled with fixed seed 3107. Pilot: one of each, infrastructure only, never sufficient to select patch.

Directions: historical train U; shared U10; mean across layers; paired task+step loop+ minus action-change controls; paired MLP; leading uncentered SVD direction of paired differences (oriented to mean). Use seed0–5 captured activations only, no gradients or training. Pairs may share a positive and are not independent.

B: baseline, native L10 / shared10 L9–13 / shared10 all / native all; alpha 1 initially, then alpha2 and alpha-1. Alternative directions on all layers. Additive negative steering must be separately defined and measured, not called equivalent to negative projection alpha. Search at most 3 families of screens; stop after 2 consecutive rounds with no improvement in constrained repeat reduction. Total max40 including compilation, sparse variants, random and heldout.

C gated on B success: layer-end steering is not algebraically equivalent to projection of output writers. Test corresponding writer-level inference intervention first. Include embedding rows (right-side projection), attention o_proj/out_proj, MLP down_proj, visual merger output+bias. For shared embedding/head, preserve original readout explicitly and document untie/count denominator. Only compile a writer intervention that meets behavioral criteria, then test repeat agreement <=.05 with original successful steering; HEALTH must also retain threshold. BF16 rounding prevents bit-exact assumption. Search sparse layers/columns only after full compilation. Random direction control same scope/alpha/column count with disclosed delta norm.

D gated on validated frozen patch: adapt private launcher under r3 only (original hardcodes protected /workspace/projet and creates other tmux sessions). Only astra3 windows, <=2 shards, model Hcompany/Holo-3.1-0.8B; tags astra3_val_orig (--arm original) and astra3_val_patch; same task list and seeds50–51. Outcomes via holo.diagnostic, separate success and loop rates. No online tuning/re-run.

Resource gate: no GPU generation while it may contend with production OSWorld. CPU pilot restricted to one thread with CUDA hidden. Pilot runtime cap 10 minutes for two contexts; if not complete, terminate only own process and report actual measurements/infrastructure limit. No unattended generation beyond experiment. Other tmux sessions and protected source/data never modified.

## Execution amendments before the main screen
- Ares confirmed GPU cohabitation for the small model; one GPU process, allocator24GiB, no modifications to production sessions. CPU kernel failure counts as lot1; CPU reference startup aborted before model/budget. Scalar GPU pilot lot2; vector pilot lot3.
- Main screen uses num_return_sequences=4, stable SHA256(run,t,group,3107) seed per context. All compared arms use this vectorized implementation; pilots are not selection evidence. Shapes expanded by Transformers generation utilities; independent inspection verified multimodal expansion. Assertions require recorded input token count to match.
- Corrected paired population includes all saved steps with actual valid current and previous action; 97 pairs /10 tasks. Null/error controls are excluded. HEALTH sampling includes the success/loop+ intersection in its eligible pool; the random fixed screen happens to have no overlapping rows (24 unique).
- Negative additive intervention is h <- h - .25u, separate from alpha=-1 projection (which amplifies the existing signed component). Candidate list alternative_jobs.json includes both.

## Fit audit amendment, before any paired-direction behavioral result (17:30 UTC)
Independent audit found 24/97 pairs cross normal/impossible variants. The alternative family therefore also tests strict task+step+impossible matched fits (73 pairs /10 tasks), using strict/directions.npz, in addition to the original task+step contrast. This fit correction is included in the same alternative search round, not a post-heldout refinement. PCA uses centered paired differences; uncentered SVD directions were prepared but never behaviorally evaluated. Core directions unaffected bit-for-bit (independent verification).

## Resource stop amendment (before remaining_jobs generation)
Alpha=-1 projection amplification aborted after four saved invalid outputs (~92 seconds/context), during next context. It has no complete score, no HEALTH observation and stays charged to the budget; it cannot be selected. Remaining jobs use healthy-first row order, keeping fixed context-hash RNG. A new no-steering baseline_repeat checks this execution path. For candidates, stop only when observed health hits plus ALL unobserved health draws counted as successes still give HEALTH <.70 (=original .75-.05). This is a mathematically sufficient rejection, never acceptance. Incomplete candidates report upper bounds and no complete REPEAT score. Maximum remains40 lots. No threshold relaxed.

## Final additive runtime bound (17:57 UTC, before any additive output)
The additive job is computing but has produced no first context after five minutes. Bound this final job at ten minutes from process launch if no first result; interrupt only its PID and report it as unmeasured, not a behavioral failure. If output arrives within this bound, continue the existing HEALTH rejection protocol. This resource stop remains charged as a full generation lot and does not establish the additive hypothesis is false.

Additive first context arrived before the ten-minute no-output bound: four invalid outputs, 279.5 seconds generation. Applied the same degenerate-output resource stop as alpha=-1, interrupting own PID79689 during next context. This is an incomplete unselectable candidate, not a demonstrated HEALTH rejection.
