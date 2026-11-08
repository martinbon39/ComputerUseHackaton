# Guard v2, sprint S1 — protocol (written 09:31 UTC, before any dev result was looked at)
- Corpus: judge_bench / verif_study manifest (268 episodes, final screen = the answer step's screenshot).
  Split by task hash: SPLIT.json (commit af668e6). The held-out half is evaluated ONCE, with ONE variant.
- Metric: detection = INCOMPLETE among false successes; false rejection = INCOMPLETE among true successes;
  no verdict (timeout, error) = pass. Wilson 95 % CI; gap CI by task-cluster bootstrap (10 000).
- Variants on dev: v1 (frozen, existing responses, no new call), a = history (2 previous screens + action list),
  c = strict file-evidence prompt, b = opus; then at most one combination of the best ones.
- Selection rule on dev: the variant with the highest detection among those with dev false rejection <= 10 %;
  if none qualifies, the highest (detection - false rejection). Ties -> lower false rejection, then lower latency.
- Target (ares): >= 80 % detection with <= 10 % false rejection on the held-out half.
- Limits: at most 3 concurrent claude calls (shared subscription with the online relay). v1 stays frozen.
- Note (09:31): v1's held-out scores (existing judge_bench responses, no v2 call) were printed while testing score_v2.py: 16/29 detection, 10/116 false rejection. No v2 variant has touched the held-out half.
- Dev results (09:46): v1 29/37 det 11/86 FR; a 28/37, 7/86; b 29/37, 8/86; c 35/37, 33/86. Offline ensembles were looked at (no calls): a|b 31/37, 11/86 (fails FR). The one combination run: ab (opus + history).
- ab on dev: 31/37 det, 8/86 FR. SELECTED by the rule (highest detection with dev FR <= 10 %): ab = opus + history (2 previous screens + action list), non-strict prompt. Held-out evaluation launched once at 09:54 UTC.
- Held-out (10:04), ab, single run: 20/29 detection [51–83], 15/116 false rejection [8–20]; v1 on the same half 16/29, 10/116. Paired task bootstrap: detection +13.8 pts [+2.9, +30.0], false rejection +4.3 pts [−5.2, +15.2]. Target (>= 80 % / <= 10 %) NOT met.
