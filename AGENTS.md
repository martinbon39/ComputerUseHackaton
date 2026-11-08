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
   false "done" with a reason, and the agent repairs or escalates to Holo4-27B.
4. **Honesty rule**: a gain is claimed only when the lower bound of the paired 95 % CI is > 0. That rule was fixed before the data was read.

## Verify everything that can be verified offline (≈ 1 s each, Python ≥ 3.9 stdlib only)
```bash
python3 jury_kit/verify_results.py        # exit 0; prints "+1.94 pt CI95 [-4.3; +8.0] ... NO DETECTABLE GAIN"
python3 jury_kit/replay_guard.py --show 2 # exit 0; prints "45/66 = 68 % [56-78]", "21/202 = 10 % [7-15]", gap "+58 [+41, +74]"
bash jury_kit/quickstart.sh               # both of the above + checks the demo page; ends with "QUICKSTART OK"
```
- Expected full outputs: [docs/QUICKSTART_PROOF.md](docs/QUICKSTART_PROOF.md). CI runs the same on every push:
  [.github/workflows/quickstart.yml](.github/workflows/quickstart.yml) (Python 3.9 and 3.12).
- `replay_guard.py` runs the frozen decision function `holo-neurochir/feci_guard/feci_guard.py::check` on the 268 real
  final screenshots (`holo-neurochir/verif_study/images/`, sha256-checked against the manifest). Only the network call
  is replaced, by the verdict recorded on 2026-11-08 (`holo-neurochir/judge_bench/claude_responses.jsonl`).
- With the `claude` CLI or an Anthropic key (level 2, ~$0.03): `python3 jury_kit/guard_live.py [--api] [--episode ID]` makes
  one fresh verifier call. Model-side checks of the weight edits: [jury_kit/README.md](jury_kit/README.md) (40 GB download, GPU).

## Claim → evidence map
| Claim | Status | Evidence (path) | How to check |
|---|---|---|---|
| 29/51 failures (57 %) are false "done"; score 56.7 % on 119 scored tasks | measured | `holo-neurochir/paper/generated/num_osw_diag.tex`, paper §3 | read |
| Holo self-judge: 35/66 detected, 97/202 wrongly rejected | measured | `holo-neurochir/judge_bench/RESULT.json`, `REPORT.md` | `judge_bench/independent_recompute.py` (paths are absolute to our server) |
| Feci Guard verifier: 45/66 detected, 21/202 wrongly rejected, gap +58 [+41, +74] | measured | `holo-neurochir/judge_bench/claude_responses.jsonl` | `python3 jury_kit/replay_guard.py` |
| Merge vs original online: +1.94 [−4.3, +8.0], n=165 → no gain | measured | `jury_kit/results/scores.csv` | `python3 jury_kit/verify_results.py` |
| AlphaEdit +2.2 [−13.3, +17.8] n=45; ExPO −1.5 [−8.9, +5.7] n=120 → no gain | measured | same | same |
| Merged checkpoint rebuilt bit-for-bit from 3 pinned public models | measured (on an independent machine) | `jury_kit/expected_sha256.json`, `jury_kit/README.md` | `python3 jury_kit/rebuild_merge.py --check 2 --merged DIR` |
| Guard repair: 5/18 vs 2/18 branches, +16.7 [0, +44] | measured, **not distinguishable from 0** | `holo-neurochir/feci_guard/RESULTS.md`, `feci_guard/repair/results.json` | read |
| Guard + escalation to Holo4 | **running** (interim 4/10 vs 0/10 at 09:51 UTC; do not treat as final) | PR #1 (`rescue_bench/`) | read the PR |
| Holo + Guard on the 120-task test split | **running**, pre-registered | `holo-neurochir/report/PREREG_ONLINE_GUARD.md` | read |
| Guard v2 (Opus + history) on held-out half | **running**, protocol fixed before results | `holo-neurochir/feci_guard/v2/PROTOCOL.md` | read |
| "A verifier can be added to any agent with one call" | design property, measured on Holo only | `feci_guard.py` docstring | read 61 lines |
| End-to-end plumbing: refusal → escalation → re-check → official score | measured on 1 task (no efficacy claim) | `holo-neurochir/feci_guard/smoke/impress_550ce7e7_rescue_guard.md` | read |

Not claimed anywhere: an OSWorld score gain from any weight edit; a statistically significant repair effect (as of
this writing); comparability of our absolute scores with H's published scores (our harness is more permissive on
infeasible tasks).

## Repository map
- `README.md`: overview, results table, criteria → evidence. `docs/REPO_MAP.md`: one line per folder of
  `holo-neurochir/` with status (RESULT / NEGATIVE / ABANDONED / IN PROGRESS / TOOLING / DEMO) and its source-of-truth file.
- `jury_kit/`: everything a judge can run (levels 1–3), with `results/scores.csv` and frozen `contexts/`.
- `holo-neurochir/feci_guard/`: the Guard (verifier, decision rule, agent loop copy, repair and rescue runners, prereg, results).
- `holo-neurochir/judge_bench/`, `verif_study/`: offline comparison of judges on 268 labelled final screens.
- `holo-neurochir/paper/`: the paper (`main.pdf`, `neurips.pdf`), with every number generated from `data/` by `build.sh`.
- `holo-neurochir/osworld/`: online evaluation (Modal serving, GitHub runner collection, live duel page).
- `holo-neurochir/holo/`, `scripts/`: harness and weight-edit code. `astra-*`, `moon-*`: weight-edit experiments, mostly negative.
- `holo-neurochir/JOURNAL.md`, `LOG.md`: raw working logs of the agent team (French, chronological). They are not needed for review.

## Things that look odd but are intended
- Many folders hold negative results. They are kept on purpose, and `docs/REPO_MAP.md` gives each one's status.
- Some scripts contain absolute paths of our server (`/home/orbit/...`, `~/osw/...`). They document what ran. The
  jury-facing scripts (`jury_kit/*.py`, `jury_kit/quickstart.sh`) use relative paths only.
- `holo-neurochir/feci_guard/` code is **frozen** during the measurements (hash `0af76fdb`). Do not expect recent edits there.
- The split called "reserve" in the paper is `confirm` in `scores.csv`.

## If you are an agent asked to work on this repo
Read `LOG.md` first. Do not edit `holo-neurochir/feci_guard/*.py`, results files or the paper sources
without their owner. Keep `bash jury_kit/quickstart.sh` green.
