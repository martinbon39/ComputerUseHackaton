"""Where the written note/thought reaches the tool choice (moon-leak, strictly feasible cohort).

Reads data/pod_astra/moonleak/attribution_summary.json (cross-checked by independent_attribution_stats.json).
"""
import numpy as np

from common import FIGS, C, Macros, load, setup_mpl

SRC = "data/pod_astra/moonleak/attribution_summary.json"
r = load("pod_astra/moonleak/attribution_summary.json")
ind = load("pod_astra/moonleak/independent_attribution_stats.json")
assert ind["completeness"]["max_numeric_difference_vs_supplied_summary"] == 0.0
assert ind["completeness"]["max_abs_mask_control_margin_drop"] == 0.0
m = Macros("moonleak")

heads, delta = r["heads"], sorted(r["delta"], key=lambda x: x["layer"])
LAYERS = sorted({h["layer"] for h in heads})
assert len(LAYERS) == 8 and len(heads) == 128
mean2 = lambda x: (x["mean_fs_drop"] + x["mean_true_drop"]) / 2
top = sorted(delta, key=mean2, reverse=True)[:4]
top_drops = [v for x in top for v in (x["mean_fs_drop"], x["mean_true_drop"])]
rest = [x for x in delta if x not in top]
m.add("mlDeltaTopLayers", ", ".join(str(x["layer"]) for x in sorted(top, key=lambda x: x["layer"])[:-1]) + " and " + str(max(x["layer"] for x in top)),
      SRC + " delta: four layers with the largest mean margin loss (zero-based)")
m.add("mlDeltaTopMin", f"{min(top_drops):.1f}", SRC + " delta: min mean drop over those four layers and both strata")
m.add("mlDeltaTopMax", f"{max(top_drops):.1f}", SRC + " delta: max mean drop over those four layers and both strata")
m.add("mlDeltaRestMax", f"{max(abs(v) for x in rest for v in (x['mean_fs_drop'], x['mean_true_drop'])):.2f}", SRC + " delta: max |mean drop| over the other layers")
m.add("mlNDelta", len(delta), SRC + " delta: DeltaNet layers patched")
hmax_fs = max(h["mean_fs_drop"] for h in heads)
hmax_any = max(max(abs(h["mean_fs_drop"]), abs(h["mean_true_drop"])) for h in heads)
m.add("mlHeadMaxFs", f"{hmax_fs:.3f}", SRC + " heads: max mean_fs_drop")
m.add("mlHeadMaxAny", f"{hmax_any:.2f}", SRC + " heads: max |mean drop| over both strata")
sel = ind["neutral"]
m.add("mlNeutralSel", f"{sel['selectivity']:+.2f}".replace("-", "$-$"), "data/pod_astra/moonleak/independent_attribution_stats.json neutral.selectivity")
m.add("mlNeutralSelCi", " to ".join(f"{x:+.2f}".replace("-", "$-$") for x in sel["selectivity_bootstrap_95"]),
      "data/pod_astra/moonleak/independent_attribution_stats.json neutral.selectivity_bootstrap_95 (100,000 task resamples)")
m.write()

plt = setup_mpl()
fig = plt.figure(figsize=(7.0, 3.6))
gs = fig.add_gridspec(2, 2, height_ratios=[1, 1.05], hspace=0.6, wspace=0.12)
v = hmax_any
for j, (key, title) in enumerate([("mean_fs_drop", f"(a) Heads, false ({r['contexts']['fs+']} tasks)"),
                                  ("mean_true_drop", f"(b) Heads, true ({r['contexts']['fs-']} tasks)")]):
    a = np.zeros((8, 16))
    for h in heads:
        a[LAYERS.index(h["layer"]), h["head"]] = h[key]
    ax = fig.add_subplot(gs[0, j])
    im = ax.imshow(a, cmap="RdBu_r", vmin=-v, vmax=v, aspect="auto")
    ax.set_title(title)
    ax.set_yticks(range(8), LAYERS if j == 0 else [])
    ax.set_xticks(range(0, 16, 3))
    ax.set_xlabel("query head")
    if j == 0:
        ax.set_ylabel("attention layer\n(zero-based)")
cb = fig.colorbar(im, ax=fig.axes[:2], shrink=0.9, pad=0.01)
cb.set_label("margin loss (logits)", fontsize=7)
ax = fig.add_subplot(gs[1, :])
x = np.arange(len(delta))
w = 0.4
ax.bar(x - w / 2, [d["mean_fs_drop"] for d in delta], w, color=C["red"], label="false completions")
ax.bar(x + w / 2, [d["mean_true_drop"] for d in delta], w, color=C["blue"], label="true completions")
ax.axhline(0, color="#444444", lw=0.6)
ax.set_xticks(x, [d["layer"] for d in delta])
ax.set_xlabel("DeltaNet layer (zero-based)")
ax.set_ylabel("margin loss (logits)")
ax.set_title("(c) DeltaNet layer outputs, patched from the neutralised note and thought")
ax.legend(frameon=False, loc="upper left")
fig.savefig(FIGS / "moonleak.pdf")
print("moonleak ok", [x["layer"] for x in top], round(hmax_fs, 3), round(hmax_any, 3))
