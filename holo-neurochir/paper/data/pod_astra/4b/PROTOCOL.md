# Astra 4B — protocol, 2026-11-07

Goal: reduce false terminal answers with preserved correct answers and valid nonterminal actions, then demonstrate diagnostic task improvement. No gradients/training. Test split is forbidden.

Work is isolated in /workspace/astra/4b; source data and harness are read-only. Changes to shared checkout are not needed. Original git pull was blocked by existing dirty changes.

A: exact osw_replay messages, thinking enabled, T=.8, top_p=.9, top_k=20 (inherited production generation_config; verified in server log), max3072, k=4, JSON schema from recorded system prompt. Log parsing errors and truncations as failures, never silently drop them. Probe is only first-tool-token conditional probability given recorded thinking/note/thought, not P_answer. Validate ranking and calibration against generation before using for screening.

B: no freezing or official AUROC before osw-analysis confirms >=40 fs+. Group all passes by task ID, 5 deterministic folds. Train direction and nuisance correction only inside train folds. Compare raw and position/context-length adjusted diff-of-means for resid and mlp at final prefill. Separate held-out diagnostic fold for causal confirmation; never use split_test.

C: exploratory candidates: single layers then multiple layers; residual projection, signed constant additions, writer-output interventions, exact common-direction writer orthogonalization. Negative projection alpha is not a constant addition. Candidate admission: fs+ answer rate reduction >=25 percentage points AND >=50% relative; fs- decrease <=5 points and original fs- rate >=.8; nonterminal valid non-answer rate decline <=5 points; invalid/truncated output increase <=5 points. These thresholds operationalize 'strongly' and are fixed before observations, while directions remain provisional until B. Require disjoint diagnostic confirmation, retain task-level paired bootstrap intervals.

D: weight edits only after C passes generation. Compile only matching writer interventions; residual projection hooks are not generally equivalent to down_proj projection. Sparse top-k columns/few layers compared to dense. Fresh original weights per candidate. Patched P_answer within 5 points of steering separately for each stratum; retain efficacy. Save via holo.surgery.save_patched with original 4B processor/config.

Budget: at most 60 generation/scoring jobs, each reserved durably in /workspace/astra/budget_4b.log before execution, including failures. A job fixes model/intervention, manifest subset, seeds and mode; no adaptive candidate loops inside jobs. CPU preparation is not scoring. At most 12 exploratory candidates before review. Two successive rounds with no Pareto improvement -> stop causal search and report negative. No automatic GPU polling/launch; require explicit scheduling evidence that production will not be impacted. One own GPU process with allocation cap below30GB; tmux astra4b only.

Done: independent audit of metrics and split integrity plus actual online diagnostic improvement from ares. Negative outcome is reported as negative, not successful surgery. Missing data/resources are recorded, with independent CPU preparation continuing.
