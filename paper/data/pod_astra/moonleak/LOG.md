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
