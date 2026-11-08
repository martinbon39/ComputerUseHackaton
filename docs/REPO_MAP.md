# Repository map

One line per folder of `holo-neurochir/`: what it is, its status, and the file that states its outcome (paths relative
to `holo-neurochir/`). Status values: **RESULT** (a finding used in the README or paper), **NEGATIVE** (ran to a
verdict and found no effect, or was rejected by its gate), **ABANDONED** (stopped before a verdict), **IN PROGRESS**,
**TOOLING**, **DEMO**, **DATA**. The "in git" column says whether the folder's files are committed. A folder marked
*summaries only* has its text summaries committed (REPORT, PROTOCOL, VERIFY, RESULT files); its checkpoints, raw
logs and images stay on our server. *not committed* means nothing of it is in git.

Start with the Guard (solution), then the diagnosis, then the weight-edit experiments.

## The solution: Feci Guard
| Folder | In git | What | Status | Source of truth | Headline |
|---|---|---|---|---|---|
| `feci_guard/` | yes | External verifier (Claude) that refuses a false "done" with feedback; repair and rescue runners | RESULT | `feci_guard/README.md`, `RESULTS.md`, `PREREG.md` | repair 5/18 vs 2/18 branches (3 genuine repairs vs 0), +16.7 [0, +44], not distinguishable from 0 |
| `feci_guard/v2/` | yes | Guard v2 variants (history, strict prompt, Opus) on a dev/held-out split | RESULT (offline) | `feci_guard/RESULTS.md`, `v2/PROTOCOL.md` | held-out, used once: detection 20/29 vs v1 16/29, +13.8 pts [+2.9, +30]; target not met |
| `judge_bench/` | yes | Three judges on the same 268 labelled final screens | RESULT | `judge_bench/REPORT.md`, `RESULT.json` | Claude 45/66 detected, 21/202 wrongly rejected; Holo-3.1-4B 35/66, 97/202 |
| `verif_study/` | yes | Holo-3.1-4B as its own verifier; the 268-episode manifest, screenshots and tasks | RESULT | `verif_study/REPORT.md`, `manifest.json` | detects 35/66 (53 %), rejects 97/202 (48 %): chance |
| `rescue_bench/` | yes | Guard refusal → Holo4-27B escalation vs an unguarded control, replayed false successes | RESULT (replay) | `rescue_bench/REPORT.md`, `PREREG.md` | 11/18 vs 2/18, +50 pts [+22, +78], 9 episodes |

## The diagnosis
| Folder / file | In git | What | Status | Source of truth | Headline |
|---|---|---|---|---|---|
| `paper/` | yes (sources, PDFs) | The paper, arXiv and NeurIPS versions, every number generated from `data/` | RESULT | `paper/README.md`, `main.pdf` | false "done" = 29/51 failures (57 %) |
| `constraint_drop/` | yes | Does the agent know? Blind annotation of whether Holo names an unmet requirement in its last 3 steps before answering | NEGATIVE (pre-registered) | `constraint_drop/REPORT.md`, `PROTOCOL.md` | 9/56 false successes vs 10/133 true successes, +8.6 pts [−0.8, +20.8], not significant |
| `text_signal/` | yes | CPU test of text and sampling-consistency detectors of false success | RESULT (negative for detection) | `text_signal/REPORT.md` | best text AUROC 0.66 vs step index 0.72 |
| `proof_anchor/` | partial | Teacher-forced ablation of the note/thought before the tool call, 39 tasks | RESULT | `proof_anchor/REPORT.md` | removing note + thought shifts the answer margin by 14.0 logits [12.9, 15.1] |
| `diagnostic.md` | yes | First diagnostic on MiniWoB with the 0.8B model (pilot) | RESULT (pilot) | `diagnostic.md` | 23/70 failures are false success (32.9 %) |
| `diagnostic_examples/` | partial | Screenshots of failure categories | DATA | `diagnostic.md` | |

## Weight and activation edits (the surgery that did not work)
| Folder | In git | What | Status | Source of truth | Headline |
|---|---|---|---|---|---|
| `astra-merge/` | yes | Weight merges Holo + (CUA − Qwen); checkpoints and static screens | NEGATIVE online | `astra-merge/REPORT.md`; online: `jury_kit/verify_results.py` | merge vs original +1.94 [−4.3, +8.0], n=165 |
| `astra-regmean/` | yes | Selective RegMean closed-form edit, two precisions | NEGATIVE | `astra-regmean/REPORT.md` | false-success answers 15/16 → 13/16; gate ≤ 11/16 fails |
| `moon-leak/` | yes | Attenuating the heads that carry the note into the tool choice | NEGATIVE | `moon-leak/REPORT.md` | 56/76 false answers vs 55/76 original |
| `moon-vision/` | yes | Vision-tower-only merge and extrapolation | NEGATIVE | `moon-vision/REPORT.md` | 54–57/76 vs 55/76; needed ≤ 43/76 |
| `astra-broad/` | summaries only | Static edit spread over many writers, dose grid (AlphaEdit family) | NEGATIVE | `astra-broad/REPORT.md` | false answers 15/16 → 8/16 but true finishes 15/16 → 3/16 |
| `astra-power/` | summaries only | Larger feasible false-success cohort, candidate vs control | RESULT (offline lever, no selectivity) | `astra-power/REPORT.md` | false answers −17.1 pp [−28.9, −6.6]; selectivity not shown |
| `astra-evo/` | summaries only | Evolutionary search of merge coefficients | NEGATIVE | `astra-evo/REPORT.md` | 45 candidates; no selectivity, no online gain |
| `astra-mit1/` | summaries only | Fixed-weight edit families (conclusion tokens, heads, MLP interpolation) | NEGATIVE | `astra-mit1/REPORT.md` | 0/8 useful actions at every dose |
| `astra-mit2/` | summaries only | Conditional circuit edit (two SwiGLU neurons) | NEGATIVE | `astra-mit2/REPORT.md` | 7 edits, each leaves 5/5 false successes |
| `astra-preamble/` | summaries only | Learned "verify first" preamble written into the weights | NEGATIVE | `astra-preamble/REPORT.md` | 0/8 preambles (needed ≥ 6/8) |
| `astra-ratio/` | summaries only | Rationalisation direction and narrow MLP edit | NEGATIVE | `astra-ratio/REPORT.md` | no admissible candidate; 0/8 useful at every dose |
| `astra-short/` | summaries only | Promoting `</think>` to shorten reasoning | NEGATIVE | `astra-short/REPORT.md` | best −7.0 % thinking (needed −25 %) |
| `astra-tact/` | summaries only | TACT activation-intervention pilot | NEGATIVE | `astra-tact/REPORT.md` | no dose reduced false completion |
| `astra-infeas/` | summaries only | Rewording of infeasibility declarations | NEGATIVE | `astra-infeas/REPORT.md` | max admissible gain 1 task; gate 3 |
| `moon-combo/` | summaries only | Merge plus true-finish protection variants | NEGATIVE | `moon-combo/REPORT.md` | 3 variants rejected |
| `moon-rl/` | summaries only | RL-donor and anti-post-training merges | NEGATIVE | `moon-rl/REPORT.md` | 58/76 false answers vs 55/76 |

## Online evaluation and tooling
| Folder | In git | What | Status | Source of truth |
|---|---|---|---|---|
| `osworld/` | partial | OSWorld runs: Modal serving and manifests, GitHub runner collection, paired comparisons, live duel | TOOLING | `osworld/ONLINE_EVAL.md`, `MODAL.md`, `duel/README.md` |
| `infra/` | yes | GPU infrastructure controller `gpu_ctl.py` (Modal app status, per-account daily cost, budget guard, manifest-based redeploy), written by Devin through the Devin API and reviewed before any run; read-only budget monitor since 11:47 UTC | TOOLING | `infra/DEVIN_SESSION.md`, `infra/README.md` |
| `holo/` | partial | Harness: agent, model loading, diagnostic, directions, rollouts, surgery | TOOLING | module docstrings |
| `scripts/` | partial | Checkpoint builders (patched, ExPO) and checks | TOOLING | script docstrings |
| `runs/` | partial | Raw rollout outputs (acceptance, diagnostic, smoke) | DATA | `diagnostic.md` |
| `report/` | partial | Online Guard test: pre-registration, analysis code, result (false "done" 22.5 % → 10.8 %, −11.7 pts [−19.2, −4.2]; no score gain); ExPO report, sprints | RESULT | `report/ONLINE_GUARD_RESULT.md`, `PREREG_ONLINE_GUARD.md` |
| `dashboard/` | partial | Local "MRI" dashboard of the model's internals | TOOLING | |
| `team_dash/`, `alerts/` | not committed | Agent-team tooling (team status page, phone alerts) | TOOLING | |

## Demo material
| Folder | In git | What | Status |
|---|---|---|---|
| `demo_faux_fini/` | yes | Self-contained replay page of a recorded false "done" (quickstart (c)) | DEMO |
| `osworld/duel/` | yes | Live duel page, two VMs side by side, STOP buttons, replay; screenshots in `shots/` | DEMO |
| `demo_live/` | .md + `repair_calc.html` | Guard repair replay page (quickstart (c)), run-of-show, day-of checklist | DEMO |
| `demo_banc/`, `demo_graphe/`, `video_*` | not committed | Demo pages and video build pipelines (video hosted, linked in the README) | DEMO |

## Top-level files
| File | What |
|---|---|
| `JOURNAL.md` | Chronological log of the mission (French) |
| `HANDOFF.md`, `BRIEF_neurochirurgie_holo_LOCAL.md` | Original mission brief and handover notes |
| `runs_pilot_tasks.txt` | Pilot task list |
