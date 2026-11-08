# Independent attribution-results verification

**Verdict: PASSED for completeness and arithmetic; exploratory evidence only.** I independently parsed `attribution.jsonl` with Python's standard library and recomputed every head, DeltaNet, neutral-prefix, and zero-mask summary from the raw records. I did not import the summarizer, run the model, use a GPU, or access the network.

## Fixed artifacts

- `attribution.py`: `69844786ac4effbbb85e9faae2f73e18e5b410c32ee39cbf316afb196429ebb2`
- `PROTOCOL.md`: `bd1e7e9db01cc6f72bf764072ae586a575d3e67b6deac0320cadbfad0fe08337`
- `attribution.jsonl`: `b45ef836c40876b701fecf1a7c2b890a87539b9fc5de11185110c7055b56dac3`
- `attribution_summary.json`: `756316504d7c0ffcc8ebe952c8a42a07d55e497939240c2b004fec0f906286ee`

## Completeness and controls

The raw file contains 6,357 records for 39 unique tasks: 19 `fs+` and 20 true finishes. Every context has exactly 1 baseline, 8 mask controls, 128 unique attention heads, 1 neutral-prefix intervention, 24 unique DeltaNet layers, and 1 completion record. All 39 contexts have completion records, the cumulative completion counters are exactly `165, 330, ..., 6435`, and the last is 6,435 forwards.

All 312 zero-mask controls have `margin_drop == 0.0` exactly. The independently recomputed 128-head table, 24-layer DeltaNet table, neutral row, eight control rows, cached/full maxima, and all medians and sign counts match the supplied summary exactly; the maximum numeric difference is `0.0`.

Cached replay is not full-prefill-equivalent: the worst recorded cached/full difference is 0.198738 logits on the legal-tool margin and 0.75 on a vocabulary logit. The within-cached zero controls establish exact branch repeatability, but the head effects must be interpreted on that cached measurement path.

## Neutral-prefix result

Replacing the interior note/thought tokens with the same-length neutral prefix produces a large effect in both classes: mean answer-margin drop 7.548466 for `fs+` and 8.184968 for true finishes. Its selectivity is therefore **-0.636502 logits**, with a task-bootstrap 95% percentile interval of **[-2.133194, 0.799626]**. This is strong nonselective dependence on the serialized content under this intervention; it does not show that an internal discriminator is absent.

The bootstrap used 100,000 replicates with seed `20261108`, resampling the 19 and 20 unique tasks separately with replacement. Each task is one context, and the same resamples were used for every estimand.

## Attention-head ranking

The frozen primary score is mean `fs+` margin drop minus mean true-finish margin drop, with positive mean `fs+` effect required. The independently reproduced top four are:

| Rank | Head | fs+ drop | True-finish drop | Selectivity | Task-bootstrap 95% |
|---:|:---:|---:|---:|---:|:---:|
| 1 | 11h2 | 0.043587 | -0.007394 | 0.050981 | [0.005900, 0.097839] |
| 2 | 7h4 | 0.013869 | -0.035219 | 0.049088 | [0.009714, 0.089939] |
| 3 | 3h3 | 0.011831 | -0.034007 | 0.045838 | [0.005939, 0.086379] |
| 4 | 15h4 | 0.015125 | -0.027486 | 0.042611 | [0.005849, 0.082096] |

These intervals are **selection-biased descriptive intervals**, because these same 39 tasks selected the heads and estimated their effects. They are not confirmatory confidence intervals. The maximum selected score is only about 0.051 logit, smaller than the observed cached/full margin sensitivity, so the ranking is appropriate for the frozen screen but is weak evidence for a uniquely isolated channel.

The selected prefixes are exactly `[(11,2),(7,4)]`, then those plus `[(3,3),(15,4)]`, then those plus `[(15,13),(11,0)]`. I reproduced Python seeded sampling with seed `261029609`. The controls are exactly:

- k=2: `[(7,10),(11,15)]`
- k=4: `[(3,5),(7,11),(11,6),(15,0)]`
- k=6: `[(3,5),(7,5),(11,7),(11,9),(15,15),(15,0)]`

Each control has the selected set's per-layer cardinality and excludes all six selected heads. All 12 supplied specifications reproduce the selected/random set, `0.5`/`0` scale, control flag, and seed exactly.

## DeltaNet summary

All 24 independently recomputed layer summaries are in `independent_attribution_stats.json`. The five highest selectivities are layer 17: 0.182434 (`fs+` 0.082048, true -0.100386), layer 21: 0.156254 (0.210715, 0.054461), layer 20: 0.109672 (0.268476, 0.158805), layer 16: 0.104945 (0.327532, 0.222586), and layer 26: 0.092349 (-0.112569, -0.204918). These are output substitutions from a neutral-prefix branch, not attention-head link ablations, so their magnitudes are not directly comparable to the proposed `o_proj` head-column edit. Large raw late-layer effects are mostly nonselective: layer 30 drops 1.588653 on `fs+` and 1.564972 on true finishes.

## Meaning of “strongest channel”

If “strongest” literally means the largest mean answer-margin drop on `fs+` alone, the top four are 7h13, 11h2, 7h8, and 15h5; only 11h2 overlaps the selectivity top four. That interpretation would materially change three of four heads, but it optimizes raw suppression and tolerates comparable damage to true finishes. For the stated channel-isolation and selective-repair objective, the frozen selectivity ranking is the honest primary choice. The raw-effect ranking should remain reported as a secondary reading rather than replace the prescribed candidate after observing results.

The results support carrying 11h2, 7h4, 3h3, and 15h4 into the already defined screening step. They do not by themselves establish a causal discriminator, a generalizable selective effect, or absence of such a discriminator elsewhere in the model.
