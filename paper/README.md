# Paper — Cogito, Ergo Feci

`./build.sh` regenerates every number, table and figure from `data/`, then compiles `main.pdf` (tectonic,
`arxiv.sty` from kourgeorge/arxiv-style, vendored with a smaller title block so the teaser fits on page 1).

## Two versions, one source
- `main.tex` → `main.pdf`: arXiv preprint (`arxiv.sty`).
- `neurips.tex` → `neurips.pdf`: NeurIPS 2026 submission (`neurips_2026.sty` from the official kit, anonymous mode):
  9-page main text `neurips/body.tex` (condensed), then references, then the full arXiv sections as appendices,
  then the filled checklist `neurips/checklist.tex`.
- Shared: `shared/` (preamble, title, abstract, teaser caption), `sec/*.tex` (one file per arXiv section),
  `fig/*.tex` (each figure/table environment, placed once wherever `\placefig{key}` first occurs), `generated/`.
  Edit a section in `sec/`, a figure in `fig/`; both PDFs follow. `\ifneurips` is available for version-specific text.

## Title

Chosen by Martin (provisional, the subtitle may follow the results): **Cogito, Ergo Feci: False Success and the Limits of Weight Surgery in a Computer-Use Agent** ("I think, therefore I have done", after Descartes; translated in a title footnote).

Two subtitles are prepared in `main.tex` (`\paperSubtitle`, switch when the paired online result is in):
- no lever (current): *False Success and the Limits of Weight Surgery in a Computer-Use Agent*
- intervention works: *Finding and Removing a False-Success Lever in a Computer-Use Agent*

Other candidates (each claim is measured; none claims a repair):
1. It Says "Done" Before It Checks: False Success in a Computer-Use Agent, and Why Detecting It Is Not Causing It *(previous title)*
2. Detecting Is Not Causing: Diagnosing False Success in a Computer-Use Agent Before Editing Its Weights
3. A Marker Is Not a Lever: Three Traps in Weight-Space Surgery on a Computer-Use Agent
4. Done Before It Checks: Why a Linear Probe for False Success Is Not a Repair Handle in Holo-3.1
5. Most Failures Are a False "Done": Diagnosing, Mapping and Failing to Steer a Computer-Use Agent

## Figures (all from `figs/*.py`, sans-serif, Okabe-Ito palette)
| Figure | Script | Data |
|---|---|---|
| 1 teaser (Spotify episode, taxonomy, success-claim token) | `teaser.py` | `data/local/spotify/`, `diagnostic_osw_diag.json`, `pod_astra/think/direction_summary.json` |
| 2 pipeline with stage status | `pipeline.py` | `osw_shared_STATUS.json`, `confirm_tasks.json` |
| 3 outcome by domain, episode length | `osw_diag.py` | `diagnostic_osw_diag.json` |
| 4 traps: position confound (0.8B vs 4B), regression to the mean | `traps.py` | `directions_loop_resid.json`, `demo/dir_provisoire_fs_*.json`, `diagnostic_osw_diag{,2}.json` |
| 5 causal map of the tool choice (replotted from raw patches) | `causal.py` | `pod_astra/circuit/lot04-13*.jsonl` |
| Table 1 every 4B causal arm | `causal.py` | `pod_astra/{4b,think,value,neurons,circuit}/` |
| 6 perceived-completion direction (exploratory) | `perceive.py` | `pod_astra/perceive/{metadata,descriptive_v2}.json` |
| Fig. attractor + Table attractor: edits change tokens, not the decision (H2, H3, H5; mit2, ratio in text) | `attractor.py` | `pod_astra/free/external/*/summary.json`, `free/external_pairwise_token_check.json`, `{free,mit2,ratio}/REPORT.md` |
| Ceiling test (writer swap, layers 12–23) + CUA-Lite merge numbers | `broad.py` | `pod_astra/broad/ceiling.jsonl`, `pod_astra/merge/VERIFY_CUA_B050_BEHAVIOR.json` |
| 7 + appendix: 0.8B MiniWoB++ | `miniwob.py` | `local/diag08b_full.json`, `pod_astra/r3/`, `a2_*` |

## Rules
- No number is typed by hand. Numbers are macros in `generated/num_*.tex` (each line names its source file);
  a number in the prose that is not a macro carries an inline `% source:` comment.
- `data/` holds verbatim copies of result files (pod `/workspace/astra/*`, `/workspace/osw_shared/`,
  `/workspace/osw_analysis/diagnostic_osw_diag*.json`, local `~/osw/results_pilot1/.../94d95f96`). Refresh by
  copying, never by editing. Arms still running are read from their raw `.jsonl`, so recopying updates Table 1.

## What remains [À REMPLIR] (grep `tofill` in main.tex)
1. Authors, affiliations, emails; public URL for raw outputs.
2. Table 1: final counts of the arms still running (4b-x L24, value L18, circuit c1 α=0.5) and the L28 arm:
   recopy `pod_astra/4b/pilot_c1_add_l2{4,8}*.jsonl|metrics.json`, `value/r1_value_L18_a05_prefill*`,
   `circuit/lot15_behavior.jsonl` + `behavior_summary.json`, then add an L28 entry in `figs/causal.py`.
   Completed arms should be read from their `*metrics.json` / `*.comparison.json` (official verdict), not the jsonl.
3. Done: official (exploratory) fs direction analysis, Table 1 + Fig. 4b, from `osw_shared_STATUS.json` auc.fs and `local/directions_osw_explo_fs_*.json`. If pass 2 resumes, recopy them and `diagnostic_osw_diag2.json`.
4. §6.3 compiled edit (% weights, ‖ΔW‖_F, steered-vs-patched equivalence) if a candidate passes.
5. Table 2: paired online validation on `confirm_tasks.json` (then split_test if a gain): replace the placeholder in `figs/b4.py`.
6. Abstract last sentence, contribution 4, §8 "What would change our mind": one sentence each on the outcome.
7. astra-perceive causal screen (L15 subtraction, α 0.5–4, random control): add a row to Table 1 via `figs/causal.py`.
8. Pass 2 refresh: recopy `diagnostic_osw_diag2.json` and `osw_shared_STATUS.json`; regression-to-the-mean numbers update by themselves.

## Practices applied
Layout and writing follow what the cited preprints do: claim titles with a colon, a self-contained Fig. 1 on a
real episode (Arditi et al. 2024; Wu et al. 2026), captions that state the takeaway first, section titles that
are findings, the negative result as a numbered contribution and a dedicated Limitations section (Wu et al. 2026).
