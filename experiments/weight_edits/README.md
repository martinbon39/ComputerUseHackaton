# Weight and activation edits

Each folder is one edit family: its protocol (when one was written), its report and, for some, the per-generation
outputs. Paper §6 and the appendix on weight edits report them; the paper's numbers come from the copies in
[`paper/data/`](../../paper/data/), not from these folders. Paths are relative to this folder.

The folders were renamed when the repository became the paper's companion. The old names were the code names of the
agents that ran them, and the reports, the lab notebook and the paper's source comments may still use them.

| Folder | Former name | What | Status | Headline |
|---|---|---|---|---|
| [`task_vector_merge/`](task_vector_merge/) | `astra-merge` | Merge Holo + (CUA − Qwen), checkpoints and static screens | NEGATIVE online | merge vs original +1.94 [−4.3, +8.0], n = 165 |
| [`regmean/`](regmean/) | `astra-regmean` | Selective RegMean closed-form edit, two precisions | NEGATIVE | false-success answers 15/16 → 13/16; gate ≤ 11/16 fails |
| [`alphaedit_broad/`](alphaedit_broad/) | `astra-broad` | Static edit spread over many writers, dose grid (AlphaEdit family) | NEGATIVE | false answers 15/16 → 8/16 but true finishes 15/16 → 3/16 |
| [`power_cohort/`](power_cohort/) | `astra-power` | Larger feasible false-success cohort, candidate vs control | offline lever, no selectivity | false answers −17.1 pp [−28.9, −6.6]; selectivity not shown |
| [`expo/`](expo/) | `report/EXPO_REPORT.md` | ExPO extrapolation away from the base model | NEGATIVE online | −1.5 [−8.9, +5.7], n = 120 |
| [`evolutionary_merge/`](evolutionary_merge/) | `astra-evo` | Evolutionary search of merge coefficients | NEGATIVE | 45 candidates; no selectivity, no online gain |
| [`fixed_edit_families/`](fixed_edit_families/) | `astra-mit1` | Fixed-weight edits (conclusion tokens, heads, MLP interpolation) | NEGATIVE | 0/8 useful actions at every dose |
| [`conditional_circuit_edit/`](conditional_circuit_edit/) | `astra-mit2` | Conditional circuit edit (two SwiGLU neurons) | NEGATIVE | 7 edits, each leaves 5/5 false successes |
| [`verify_preamble/`](verify_preamble/) | `astra-preamble` | Learned "verify first" preamble written into the weights | NEGATIVE | 0/8 preambles (needed ≥ 6/8) |
| [`rationalisation_direction/`](rationalisation_direction/) | `astra-ratio` | Rationalisation direction and narrow MLP edit | NEGATIVE | no admissible candidate; 0/8 useful at every dose |
| [`shorter_thinking/`](shorter_thinking/) | `astra-short` | Promoting `</think>` to shorten reasoning | NEGATIVE | best −7.0 % thinking (needed −25 %) |
| [`tact/`](tact/) | `astra-tact` | TACT activation-intervention pilot | NEGATIVE | no dose reduced false completion |
| [`infeasible_rewording/`](infeasible_rewording/) | `astra-infeas` | Rewording of infeasibility declarations | NEGATIVE | max admissible gain 1 task; gate 3 |
| [`head_attenuation/`](head_attenuation/) | `moon-leak` | Attenuating the heads that carry the note into the tool choice | NEGATIVE | 56/76 false answers vs 55/76 original |
| [`vision_tower_merge/`](vision_tower_merge/) | `moon-vision` | Vision-tower-only merge and extrapolation | NEGATIVE | 54–57/76 vs 55/76; needed ≤ 43/76 |
| [`merge_protection_variants/`](merge_protection_variants/) | `moon-combo` | Merge plus true-finish protection variants | NEGATIVE | 3 variants rejected |
| [`rl_donor_merge/`](rl_donor_merge/) | `moon-rl` | RL-donor and anti-post-training merges | NEGATIVE | 58/76 false answers vs 55/76 |

`task_vector_merge`, `regmean`, `head_attenuation` and `vision_tower_merge` are committed with their run outputs; the
other folders hold their summaries only (reports, protocols, verification files), as listed in
[`docs/REPO_MAP.md`](../../docs/REPO_MAP.md). Checkpoints are not in the
repository; the merged checkpoint can be rebuilt bit-for-bit with [`reproduce/rebuild_merge.py`](../../reproduce/rebuild_merge.py).
