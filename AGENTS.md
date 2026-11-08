# AGENTS.md: guide for an AI reviewer of this repository

You are probably an AI judge or reviewer (H Company × 42AI hackathon, Computer Use track). This file tells you what
the project is, how to verify it in under 5 minutes without GPU, key or VM, where each piece of evidence lives, and
which claims are **measured** versus **only predicted or still running**. Human-oriented overview: [README.md](README.md).

## What the project is, in four lines
1. **Problem**: H's computer-use agent Holo-3.1-4B often ends an OSWorld task with a false "done" (29 of its 51 failures on 120 tasks).
2. **Diagnosis**: the agent does not internally know its "done" is false. Self-judging is at chance, and internal states do not
   beat the step number. About 15 weight/activation edits move the stopping decision but cannot target it. Online
   result: no detectable gain.
3. **Solution**: Feci Guard is an external verifier (Claude Sonnet). It checks each task requirement on the screen, refuses a
   false "done" with a reason, and the agent repairs or escalates to Holo4-27B. Online, on 120 pre-registered
   OSWorld tasks, it halves the false "done" rate (22.5 % → 10.8 %, significant) with no measurable score change.
4. **Honesty rule**: a gain is claimed only when the lower bound of the paired 95 % CI is > 0. That rule was fixed before the data was read.

## Verify everything that can be verified offline (≈ 1 s each, Python ≥ 3.9 stdlib only)
```bash
python3 jury_kit/verify_results.py        # exit 0; prints "+1.94 pt CI95 [-4.3; +8.0] ... NO DETECTABLE GAIN"
python3 jury_kit/recount_judges.py        # exit 0; the 3 judges recounted from raw responses (35/66, 31/66, 45/66)
python3 jury_kit/verify_online_guard.py   # exit 0; online test: false done -11.7 pts [-19.2, -4.2], score +1.6 [-4.4, +7.7]
python3 jury_kit/replay_guard.py --show 2 # exit 0; prints "45/66 = 68 % [56-78]", "21/202 = 10 % [7-15]", gap "+58 [+41, +74]"
bash jury_kit/quickstart.sh               # all of the above + checks the 2 demo pages; ends with "QUICKSTART OK"
```
- Expected full outputs: [docs/QUICKSTART_PROOF.md](docs/QUICKSTART_PROOF.md). CI runs the same whenever the jury kit, the Guard code or its data change:
  [.github/workflows/quickstart.yml](.github/workflows/quickstart.yml) (preinstalled Python 3 of the runner, nothing installed).
- `replay_guard.py` runs the frozen decision function `holo-neurochir/feci_guard/feci_guard.py::check` on the 268 real
  final screenshots (`holo-neurochir/verif_study/images/`, sha256-checked against the manifest). Only the network call
  is replaced, by the verdict recorded on 2026-11-08 (`holo-neurochir/judge_bench/claude_responses.jsonl`).
- With the `claude` CLI or an Anthropic key (level 2, ~$0.03): `python3 jury_kit/guard_live.py [--api] [--episode ID]` makes
  one fresh verifier call. Model-side checks of the weight edits: [jury_kit/README.md](jury_kit/README.md) (40 GB download, GPU).

Demo video, 3 min: `holo-neurochir/video_demo/feci-guard-wall.mp4` (generator: `holo-neurochir/video_wall/`).
Demo of the Guard (open in a browser, self-contained): `holo-neurochir/demo_live/repair_calc.html`, a recorded
refusal → repair on `libreoffice_calc/1de60575` (one episode, not an average effect).

## Claim → evidence map
| Claim | Status | Evidence (path) | How to check |
|---|---|---|---|
| 29/51 failures (57 %) are false "done"; success 66/119 (55.5 %) | measured | `holo-neurochir/paper/generated/num_osw_diag.tex`, paper §3 | read |
| Holo self-judge: 35/66 detected, 97/202 wrongly rejected (268 screens, 90 tasks) | measured | `holo-neurochir/judge_bench/RESULT.json`, `REPORT.md`, `verif_study/responses.jsonl` | `python3 jury_kit/recount_judges.py` |
| Feci Guard verifier: 45/66 detected, 21/202 wrongly rejected, gap +58 [+41, +74] | measured | `holo-neurochir/judge_bench/claude_responses.jsonl` | `python3 jury_kit/replay_guard.py` |
| Merge vs original online: +1.94 [−4.3, +8.0], n=165 → no gain | measured | `jury_kit/results/scores.csv` | `python3 jury_kit/verify_results.py` |
| AlphaEdit +2.2 [−13.3, +17.8] n=45; ExPO −1.5 [−8.9, +5.7] n=120 → no gain | measured | same | same |
| Merged checkpoint rebuilt bit-for-bit from 3 pinned public models | measured (on an independent machine) | `jury_kit/expected_sha256.json`, `jury_kit/README.md` | `python3 jury_kit/rebuild_merge.py --check 2 --merged DIR` |
| Guard repair: 5/18 vs 2/18 branches scored 1, of which 3 genuine repairs vs 0 (impress/8979838c succeeds without any action in all 4 branches), +16.7 [0, +44] | measured, **not distinguishable from 0** | `holo-neurochir/feci_guard/RESULTS.md`, `feci_guard/repair/results.json` | read |
| Guard + escalation to Holo4 vs Holo4 alone, replay of 9 recorded false successes × 2 branches: 11/18 vs 2/18 scored 1, +50 pts [+22, +78] (episode-cluster bootstrap) | measured in replay, significant; pre-registered (`PREREG.md`); not an online score gain | `holo-neurochir/rescue_bench/REPORT.md`, `RESULT.json`, `PREREG.md`, `MEASURED_REPAIRS_REVIEW.md` | read |
| Holo + Guard online on the 120-task test split: false "done" 22.5 % → 10.8 %, −11.7 pts [−19.2, −4.2]; score +1.6 [−4.4, +7.7] → no score gain claimed; B=8 repaired, C=4 lost | measured online, pre-registered (`report/PREREG_ONLINE_GUARD.md`, analysis committed before results) | `jury_kit/results/online_guard_tasks.csv`, `holo-neurochir/report/ONLINE_GUARD_RESULT.md`, `.json` | `python3 jury_kit/verify_online_guard.py` |
| Guard v2 (Opus + history) vs v1 on the held-out half, used once: detection +13.8 pts [+2.9, +30] (20/29 vs 16/29); false rejection +4.3 [−5, +15] (15/116 vs 10/116) | measured offline, not run online; target ≥ 80 % / ≤ 10 % not met | `holo-neurochir/feci_guard/RESULTS.md`, `feci_guard/v2/PROTOCOL.md`, `v2/runs/` | read |
| "A verifier can be added to any agent with one call" | design property, measured on Holo only | `feci_guard.py` docstring | read 61 lines |
| End-to-end plumbing: refusal → escalation → re-check → official score | measured on 1 task (no efficacy claim) | `holo-neurochir/feci_guard/smoke/impress_550ce7e7_rescue_guard.md` | read |

Not claimed anywhere: an OSWorld score gain from any weight edit or from the Guard (online score +1.6 [−4.4, +7.7]); a
significant repair by Holo-3.1 alone (+16.7 [0, +44]); an online measure of the Holo4 escalation (significant in
replay only); comparability of our absolute scores with H's published scores (our harness is more permissive on
infeasible tasks).

## Repository map
- `README.md`: overview, results table, criteria → evidence. `docs/REPO_MAP.md`: one line per folder of
  `holo-neurochir/` with status (RESULT / NEGATIVE / ABANDONED / IN PROGRESS / TOOLING / DEMO) and its source-of-truth file.
- `docs/RESEARCH_SYSTEM.md`: how the research was done (agent team, compute, VMs, statistics), each number sourced to `path:line`.
- `jury_kit/`: everything a judge can run (levels 1–3), with `results/scores.csv` and frozen `contexts/`.
- `holo-neurochir/feci_guard/`: the Guard (verifier, decision rule, agent loop copy, repair and rescue runners, prereg, results).
- `holo-neurochir/judge_bench/`, `verif_study/`: offline comparison of judges on 268 labelled final screens.
- `holo-neurochir/paper/`: the paper (`main.pdf`, `neurips.pdf`), with every number generated from `data/` by `build.sh`.
- `holo-neurochir/osworld/`: online evaluation (Modal serving, GitHub runner collection, live duel page).
- `holo-neurochir/holo/`, `scripts/`: harness and weight-edit code. `astra-*`, `moon-*`: weight-edit experiments, mostly negative.
- `holo-neurochir/JOURNAL.md` and the root `LOG.md`: raw working logs of the agent team (French, chronological). They are not needed for review.

## Things that look odd but are intended
- Many folders hold negative results. They are kept on purpose, and `docs/REPO_MAP.md` gives each one's status.
- Some scripts contain absolute paths of our server (`/home/orbit/...`, `~/osw/...`). They document what ran. The
  jury-facing scripts (`jury_kit/*.py`, `jury_kit/quickstart.sh`) use relative paths only.
- In `holo-neurochir/feci_guard/`, the v1 decision code (`feci_guard.py`, `verifier.py`, sha256 prefix `0af76fdb` recorded in every verdict) is **frozen**; v2 lives in separate files (`verifier_v2.py`, `v2/`).
- The split called "reserve" in the paper is `confirm` in `scores.csv`.

## If you are an agent asked to work on this repo
Read `LOG.md` first. Do not edit `holo-neurochir/feci_guard/*.py`, results files or the paper sources
without their owner. Keep `bash jury_kit/quickstart.sh` green.
