# Repository map

One line per folder: what it is, its status, and the file that states its outcome. Status values: **RESULT** (a
finding reported in the paper), **NEGATIVE** (ran to a verdict and found no effect, or was rejected by its gate),
**TOOLING**, **DATA**. "In git" says whether the folder's files are committed: *summaries only* means its reports,
protocols and verification files are committed, while checkpoints, raw logs and images stayed on the machines that
produced them.

The last column gives the folder's path before the repository was restructured. The lab notebook
(`docs/lab_notebook/`), the source comments of the paper and some reports use those paths.

## Paper and verification
| Folder | In git | What | Former path |
|---|---|---|---|
| [`paper/`](../paper/) | yes | LaTeX sources, data copies, figure scripts, generated macros, both PDFs; [`paper/README.md`](../paper/README.md) | `holo-neurochir/paper/` |
| [`reproduce/`](../reproduce/) | yes | CPU checks of the headline numbers, checkpoint rebuild, decision probe, per-task scores | `jury_kit/` |

## The external verifier: Feci Guard
| Folder | In git | What | Status | Source of truth | Former path |
|---|---|---|---|---|---|
| [`src/feci_guard/`](../src/feci_guard/) | yes | Verifier (Claude) that refuses a false "done" with feedback; agent loops; repair and rescue runners | RESULT | [`README.md`](../src/feci_guard/README.md), [`RESULTS.md`](../src/feci_guard/RESULTS.md), [`PREREG.md`](../src/feci_guard/PREREG.md) | `holo-neurochir/feci_guard/` |
| [`src/feci_guard/v2/`](../src/feci_guard/v2/) | yes | Guard v2 variants (history, strict prompt, Opus) on a dev/held-out split | RESULT (offline) | [`v2/PROTOCOL.md`](../src/feci_guard/v2/PROTOCOL.md) | `holo-neurochir/feci_guard/v2/` |
| [`experiments/judge_bench/`](../experiments/judge_bench/) | yes | Three judges on the same 268 labelled final screens | RESULT | [`REPORT.md`](../experiments/judge_bench/REPORT.md), `RESULT.json` | `holo-neurochir/judge_bench/` |
| [`experiments/verif_study/`](../experiments/verif_study/) | yes | Holo-3.1-4B as its own verifier; the 268-episode manifest, screenshots and tasks | RESULT | [`REPORT.md`](../experiments/verif_study/REPORT.md), `manifest.json` | `holo-neurochir/verif_study/` |
| [`experiments/rescue_bench/`](../experiments/rescue_bench/) | yes | Guard refusal then escalation to Holo4-27B vs Holo4-27B alone, replayed false successes | RESULT (replay) | [`REPORT.md`](../experiments/rescue_bench/REPORT.md), [`PREREG.md`](../experiments/rescue_bench/PREREG.md) | `holo-neurochir/rescue_bench/` |
| [`experiments/online_guard/`](../experiments/online_guard/) | yes | Online guard test on the 120-task test split: pre-registration, analysis code, result; registration of the attribution study | RESULT | [`ONLINE_GUARD_RESULT.md`](../experiments/online_guard/ONLINE_GUARD_RESULT.md), [`PREREG_ONLINE_GUARD.md`](../experiments/online_guard/PREREG_ONLINE_GUARD.md) | `holo-neurochir/report/` (online guard files) |

## The diagnosis
| Folder | In git | What | Status | Source of truth | Former path |
|---|---|---|---|---|---|
| [`experiments/miniwob_pilot/`](../experiments/miniwob_pilot/) | partial | First diagnostic on MiniWoB++ with the 0.8B model: report, failure screenshots, raw rollouts, task list | RESULT (pilot) | [`diagnostic.md`](../experiments/miniwob_pilot/diagnostic.md) | `holo-neurochir/{diagnostic.md, diagnostic_examples/, runs/, runs_pilot_tasks.txt}` |
| [`experiments/constraint_drop/`](../experiments/constraint_drop/) | yes | Does the agent name an unmet requirement before answering? Blind annotation | NEGATIVE (pre-registered) | [`REPORT.md`](../experiments/constraint_drop/REPORT.md), [`PROTOCOL.md`](../experiments/constraint_drop/PROTOCOL.md) | `holo-neurochir/constraint_drop/` |
| [`experiments/text_signal/`](../experiments/text_signal/) | yes | CPU test of text and sampling-consistency detectors of false success | RESULT (negative for detection) | [`REPORT.md`](../experiments/text_signal/REPORT.md) | `holo-neurochir/text_signal/` |
| [`experiments/proof_anchor/`](../experiments/proof_anchor/) | partial | Teacher-forced ablation of the note and thought before the tool call, 39 tasks | RESULT | [`REPORT.md`](../experiments/proof_anchor/REPORT.md) | `holo-neurochir/proof_anchor/` |

## Weight and activation edits
Seventeen edit families, mostly negative: [`experiments/weight_edits/README.md`](../experiments/weight_edits/README.md)
gives each folder's status, headline and former name (`astra-*`, `moon-*`, `report/EXPO_REPORT.md`).

## Code
| Folder | In git | What | Former path |
|---|---|---|---|
| [`src/holo/`](../src/holo/) | partial | Harness: agent, model loading, diagnostic, directions, rollouts, surgery | `holo-neurochir/holo/` |
| [`src/osworld/`](../src/osworld/) | partial | OSWorld runs: Modal serving and deploy manifests, runner collection, paired comparisons; [`ONLINE_EVAL.md`](../src/osworld/ONLINE_EVAL.md), [`MODAL.md`](../src/osworld/MODAL.md) | `holo-neurochir/osworld/` |
| [`src/scripts/`](../src/scripts/) | partial | Checkpoint builders (patched, ExPO) and checks | `holo-neurochir/scripts/` |

## Documentation and provenance
| Path | What | Former path |
|---|---|---|
| [`docs/RESEARCH_SYSTEM.md`](RESEARCH_SYSTEM.md) | How the research was run: agents, compute, VMs, statistics, incidents | same |
| [`docs/reviews/`](reviews/) | Adversarial reviews and fresh-eyes rounds of 8 November | `holo-neurochir/report/{REDTEAM_0305, REDTEAM2_0335, IDEATION_ROUNDS}.md` |
| [`docs/lab_notebook/`](lab_notebook/) | Raw working logs (mostly French): orchestrator log, journal, original brief, handover notes | `LOG.md`, `holo-neurochir/{JOURNAL, BRIEF_neurochirurgie_holo_LOCAL, HANDOFF}.md` |
| [`reproduce/EXPECTED_OUTPUT.md`](../reproduce/EXPECTED_OUTPUT.md) | Expected output of the CPU checks | `docs/QUICKSTART_PROOF.md` |

## Removed when the repository became the paper's companion
Demo and presentation material, not used by any number of the paper: replay pages (`demo_live/`, `demo_faux_fini/`),
the live duel page (`osworld/duel/`), videos and their generators (`video_demo/`, `video_wall/`), pitch pages
(`pitch_design/`), the internals dashboard (`dashboard/`), the GPU budget monitor written after the experiments
(`infra/`), the public evaluation endpoint (`osworld/modal_jury_*`), status and sprint notes (`STATUS.md`,
`report/{SPRINTS, CLEANUP, CONTEXT_2026-11-07, ADDENDUM_2026-11-07_2010, PUBLIC_AUDIT}.md`). They remain in the git
history before commit `26565da`.
