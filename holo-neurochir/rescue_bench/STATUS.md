# Rescue benchmark — completed

Updated 2026-11-08 10:46 UTC.

- Collection finished at10:41:44 UTC:12 episodes ×2 arms ×K2 =48 successful outcome slots; no infrastructure error attempts. Pilot retained. Both worker processes exited0, all owned Docker VMs closed, ares informed. No further model calls planned.
- Registered primary:9 common replay-valid episodes, Guard11/18 official score1 versus control2/18; after-action successes9 versus0. Paired episode mean difference+0.50, bootstrap95%[0.2222,0.7778]. Two no-action positives in each arm are retained officially but not credited as repairs.
- Strict replay+boundary sensitivity:8 episodes,10/16 versus2/16 official; after-action8 versus0; difference+0.50[0.125,0.875]. d682 excluded here because controlK1 boundary was invalid.
- All12 completed episodes, ignoring invalid replays:11/24 versus3/24 official;9 versus1 after action; difference+0.3333[0.0417,0.625]. The control's f5K1 correction is real, but the episode is excluded from the primary because other repetitions have invalid replays.
- Primary conditional repair after initial refusal:9/11 across6 refused episodes, cluster95%[0.4286,1]. All24 initial Guard checks:13 refusals,0 verifier errors. Required output missing for d682controlK1 and all four VLCaa branches; official zeros retained and qualified.
- Predicted online change, not measured: reserve+2.73 to+6.20pp; test+6.42 to+11.62pp for assumed loss1 to0. Formula and conditional repair-only intervals are in REPORT.md/RESULT.json. Transport, prevalence and false-rejection loss uncertainty are not covered by these intervals. Three calibration IDs overlap reserve; none test.
- Historical Holo3.1 snapshot0/10 remains distinct from its completed9-episode reference:official5/18 versus2/18, after-action3 versus0. Different15-turn cap and Guard policy; not a concurrent randomized model comparison.
- data/ stores exact copies of the three source journals (4+20+24 rows). Numerical reproduction is Python3 stdlib only; see README.md. Raw screenshots/calls/Guard/evaluator artifacts remain under /home/orbit/osw/rescue_bench/.
- Frozen Guard and canonical harness:9 original SHA256 hashes unchanged. Runner and scheduling independently reviewed. verify_analysis.py passed. Completed raw-evidence audit PASS in MEASURED_REPAIRS_REVIEW.md; independent numerical verdict PASSED/CORRECT in FINAL_REVIEW.md with reviewed hashes. Repository quickstart passed exit0.
- Delivery branch feat/rescue-bench, isolated worktree /home/orbit/worktrees/rescue-bench; PR1 https://github.com/martinbon39/ComputerUseHackaton/pull/1 . Latest main merged at10:43. Final archive and reviews complete; delivery commit contains all48 outcomes and reproducible estimates.
