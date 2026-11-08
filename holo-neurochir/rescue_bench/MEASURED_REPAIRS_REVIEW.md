# Two completed repair episodes — independent evidence review

Reviewed read-only on 2026-11-08. Scope is limited to the two episodes below, each now complete at K=2. No endpoint or VM was called, and no runner, journal, or result was modified.

## Bounded verdict

Two registered episodes have independently verified patterns `Guard=[1,1]` and `control=[0,0]` under official OSWorld scoring:

| Episode | Guard K0/K1 | Control K0/K1 |
|---|---:|---:|
| Calc `37608790…` | 1 / 1 | 0 / 0 |
| Impress `70bca0cc…` | 1 / 1 | 0 / 0 |

For all four Guard successes, the frozen verifier first refused the replayed false answer, Holo4 then executed real corrective desktop actions, and the official evaluator returned 1 after successfully saving and loading the result artifact. Both controls per episode made no corrective action after replay: each produced an immediate answer and received official score 0. Replay and boundary validity pass for all eight branches.

These are two measured episode-level repair patterns. They do not establish online gain, cohort repair rate, statistical significance, or generalization.

## Calc 37608790 — preserve A, populate B/C/D

The official task uses `compare_table` with a `sheet_data` rule comparing result sheet 0 to the gold workbook. The evaluator implements this as rounded DataFrame equality. See the [task config](/home/orbit/osw/rtg/Env/OSWorld/evaluation_examples/examples/libreoffice_calc/37608790-6147-45d0-9f20-1137bb35703d.json) and [table evaluator](/home/orbit/osw/rtg/Env/OSWorld/desktop_env/evaluators/metrics/table.py:328).

- Guard K0: [result](/home/orbit/osw/rescue_bench/guard/libreoffice_calc_37608790-6147-45d0-9f20-1137bb35703d_k0/attempt_1/result.json), SHA-256 `711bd15c06f7babfa5e9200f4476787eb4006f3dc94c1909859203d683f30eef`. Guard refused because A was overwritten and outputs were shifted left. The continuation undid, wrote formulas into B2/C2/D2, filled B3:D22, saved, and scored 1. This branch is documented in detail in [FIRST_REPAIR_REVIEW.md](/home/orbit/projects/ComputerUseHackaton/holo-neurochir/rescue_bench/FIRST_REPAIR_REVIEW.md).
- Guard K1: [result](/home/orbit/osw/rescue_bench/guard/libreoffice_calc_37608790-6147-45d0-9f20-1137bb35703d_k1/attempt_1/result.json), SHA-256 `f6c99e2d6874d4160c6e549c526e31359c44db793b4ef3427ca35a15df6d43c9`. The independent refusal identifies the same shifted/overwritten state with no verifier error. The continuation again executes `Ctrl+Z`, writes formulas in B2/C2/D2, copies/fills B3:D22, and saves; [calls](/home/orbit/osw/rescue_bench/guard/libreoffice_calc_37608790-6147-45d0-9f20-1137bb35703d_k1/attempt_1/frames/calls.jsonl) records 15 valid outputs and 14 nonterminal new steps.
- Controls K0/K1: [K0 result](/home/orbit/osw/rescue_bench/control/libreoffice_calc_37608790-6147-45d0-9f20-1137bb35703d_k0/attempt_1/result.json) and [K1 result](/home/orbit/osw/rescue_bench/control/libreoffice_calc_37608790-6147-45d0-9f20-1137bb35703d_k1/attempt_1/result.json), SHA-256 `06be56492a241a266b46a54e0f8ebcb7b266cf6e17246ef1683c9b55e60aa4a5` and `338f7ecc514433e800f9f810d80a4c11f34ebf0eadfec5ebc1626dc836ddc0a4`. Both have `gate=null`, one valid call, `new_steps=0`, tools `['answer']`, and official score 0.

[full0.log](/home/orbit/osw/rescue_bench/full0.log) shows successful postconfig/save/getter/evaluator loading and score 1 for Guard K0. [full0_resume1.log](/home/orbit/osw/rescue_bench/full0_resume1.log) shows the same chain for Guard K1: saved result 7167 bytes, workbook sheet loaded successfully, then score 1/error null. It also shows normal evaluation and score 0 for control K1. No evaluator, setup, getter, or model error appears in these result chains.

Within Calc, all four branches use prompt SHA-256 `620c878939bb4205638c48ff14ab29318f43a44faddbe75f950657ecc348ec3b`, the same model/settings/boundary, and valid replay. Replay maxima span `0.0020692–0.0020769`; boundary differences span `0.00001618–0.00002206`, all below `0.05`.

## Impress 70bca0cc — background exactly matches title color

The official task uses `compare_pptx_files` against `71_6_Gold.pptx`, with the default comparison options, including background color. See the [task config](/home/orbit/osw/rtg/Env/OSWorld/evaluation_examples/examples/libreoffice_impress/70bca0cc-c117-427e-b0be-4df7299ebeb6.json) and [slides evaluator](/home/orbit/osw/rtg/Env/OSWorld/desktop_env/evaluators/metrics/slides.py:190).

- Guard K0: [result](/home/orbit/osw/rescue_bench/guard/libreoffice_impress_70bca0cc-c117-427e-b0be-4df7299ebeb6_k0/attempt_1/result.json), SHA-256 `499172308d089ce6a436d3429c6de02ec1517643b5daeb1c138b827417355078`. Guard refused because the Brick background did not exactly match the red title. The continuation inspected formatting controls, opened the custom background picker, entered `FF0000`, saved, and scored 1; [calls](/home/orbit/osw/rescue_bench/guard/libreoffice_impress_70bca0cc-c117-427e-b0be-4df7299ebeb6_k0/attempt_1/frames/calls.jsonl) records 18 valid outputs.
- Guard K1: [result](/home/orbit/osw/rescue_bench/guard/libreoffice_impress_70bca0cc-c117-427e-b0be-4df7299ebeb6_k1/attempt_1/result.json), SHA-256 `b11d8747ead8b8d60b4abb63c472c130b45082b1c6a17b1d9255b42de1191ade`. The independent refusal identifies the same exact-color defect with no verifier error. The continuation again opens the custom background picker, enters `ff0000`, saves, and scores 1; [calls](/home/orbit/osw/rescue_bench/guard/libreoffice_impress_70bca0cc-c117-427e-b0be-4df7299ebeb6_k1/attempt_1/frames/calls.jsonl) records 16 valid outputs.
- Controls K0/K1: [K0 result](/home/orbit/osw/rescue_bench/control/libreoffice_impress_70bca0cc-c117-427e-b0be-4df7299ebeb6_k0/attempt_1/result.json) and [K1 result](/home/orbit/osw/rescue_bench/control/libreoffice_impress_70bca0cc-c117-427e-b0be-4df7299ebeb6_k1/attempt_1/result.json), SHA-256 `a4b99ff924963fbf712a0cbfb107eb72808c02986c019ad371e008432aa2507f` and `725f0828b58edc7728e4669d52f9ade3b17da64d44815dfda308400cd0a7b99e`. Both have no Guard/feedback, one immediate answer, zero new steps, and official score 0.

[full1.log](/home/orbit/osw/rescue_bench/full1.log) records, for both Guard runs, successful setup, postconfig save, result retrieval (318764 and 318766 bytes), comparison against the official gold PPTX, then score 1/error null. The same log records both controls' successful artifact retrieval/comparison followed by score 0/error null. No infrastructure or evaluator failure explains the observed scores.

Within Impress, all four branches use prompt SHA-256 `fbf73de5643e140dd6f75898c405ee9eabafcac055a14514afa789bfae96af95`, the same model/settings/boundary, and valid replay. Replay maxima span `0.0019279–0.0019339`; boundary differences span `0.00001352–0.00002116`, all below `0.05`.

## Provenance and limits

The authoritative branch rows are in [shard 0 journal](/home/orbit/osw/rescue_bench/branches.s0-of-2.jsonl) for Calc and [shard 1 journal](/home/orbit/osw/rescue_bench/branches.s1-of-2.jsonl) for Impress. Each `(task, arm, k)` appears once among successful rows and agrees with its durable `result.json`.

This review verifies artifact integrity, executed correction, official evaluator provenance, and within-task protocol matching. It intentionally excludes aggregate analysis, prevalence projections, implementation review, online-gain claims, and conclusions about tasks outside these two episodes.
