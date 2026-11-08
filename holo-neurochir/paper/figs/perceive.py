"""Perceived-completion direction (astra-perceive): learned inside successful episodes, then read on fs+/fs-.

Sources (verbatim copies of pod /workspace/astra/astra-perceive/analysis/):
  data/pod_astra/perceive/metadata.json        construction pairs, task-grouped CV AUROC by layer, position baselines
  data/pod_astra/perceive/descriptive_v2.json  14 matched fs+/fs- pairs, cross-fitted z-projections (previous step, terminal)
Exploratory: no causal test has been run on this direction.
"""
import numpy as np

from common import FIGS, C, Macros, load, setup_mpl

m = Macros("perceive")
SM = "data/pod_astra/perceive/metadata.json"
SD = "data/pod_astra/perceive/descriptive_v2.json"
md = load("pod_astra/perceive/metadata.json")
dv = load("pod_astra/perceive/descriptive_v2.json")
cv = md["cv"]
rank = sorted(cv["layer_ranking"], key=lambda r: r["layer"])
auc = np.array([r["cv_auc"] for r in rank])
best = max(cv["layer_ranking"], key=lambda r: r["cv_auc"])
L = best["layer"]
summ = next(s for s in dv["summary"] if s["layer"] == L)
rows = dv["rows"]

m.add("pcPairs", md["counts"]["direction_pairs"], SM + " counts.direction_pairs")
m.add("pcTasks", md["counts"]["direction_unique_tasks"], SM + " counts.direction_unique_tasks")
m.add("pcLayer", L, SM + " argmax cv.layer_ranking[].cv_auc")
m.add("pcAuc", f"{best['cv_auc']:.3f}", SM + " max cv_auc")
m.add("pcBaseStep", f"{cv['baselines']['t']['cv_auc']:.3f}", SM + " cv.baselines.t.cv_auc")
m.add("pcBaseCtx", f"{cv['baselines']['n_in']['cv_auc']:.3f}", SM + " cv.baselines.n_in.cv_auc")
m.add("pcConcord", f"{best['pair_concordance']:.3f}", SM + " best layer pair_concordance")
m.add("pcMatchN", summ["n"], SD + f" summary[layer={L}].n")
m.add("pcFsPosMargin", f"{summ['fs_plus_mean_completion_margin']:.2f}", SD + " fs_plus_mean_completion_margin (z)")
m.add("pcFsNegMargin", f"{summ['fs_minus_mean_completion_margin']:.2f}", SD + " fs_minus_mean_completion_margin (z)")
m.add("pcFsPosPositive", round(summ["fs_plus_positive_margin_fraction"] * summ["n"]), SD + " fs_plus_positive_margin_fraction * n")
m.add("pcFsNegPositive", round(summ["fs_minus_positive_margin_fraction"] * summ["n"]), SD + " fs_minus_positive_margin_fraction * n")
m.add("pcTermDiff", f"{summ['matched_terminal_fs_plus_minus_fs_minus']:.2f}", SD + " matched_terminal_fs_plus_minus_fs_minus (z)")
m.add("pcFsPosGt", round(summ["matched_terminal_fs_plus_gt_fs_minus"] * summ["n"]), SD + " matched_terminal_fs_plus_gt_fs_minus * n")
m.write()

plt = setup_mpl()
fig, ax = plt.subplots(1, 2, figsize=(7.0, 2.15), gridspec_kw={"width_ratios": [1.15, 1], "wspace": 0.32})
a = ax[0]
base = max(cv["baselines"]["t"]["cv_auc"], cv["baselines"]["n_in"]["cv_auc"])
a.fill_between([-1, len(auc)], 0.4, base, color="#EEEEEE", lw=0)
a.plot(range(len(auc)), auc, "-o", ms=2.2, color=C["blue"], lw=1.2)
a.axhline(cv["baselines"]["t"]["cv_auc"], color=C["red"], ls=":", lw=1)
a.axhline(cv["baselines"]["n_in"]["cv_auc"], color=C["orange"], ls=":", lw=1)
a.annotate(f"{best['cv_auc']:.3f} (L{L})", (L, best["cv_auc"]), xytext=(6, 4), textcoords="offset points", fontsize=6.5,
           color=C["blue"])
a.text(0.3, base + 0.02, f"step index {cv['baselines']['t']['cv_auc']:.3f}, context length {cv['baselines']['n_in']['cv_auc']:.3f}",
       fontsize=6, color="#666666")
a.set_xlim(-0.5, len(auc) - 0.5), a.set_ylim(0.4, 1.0)
a.set_xlabel("layer"), a.set_ylabel("task-grouped AUROC")
a.set_title("a  final vs. previous step, successful episodes", fontsize=7.6)

b = ax[1]
for j, (lab, col, name) in enumerate([("fs_plus", C["red"], "false “done”"), ("fs_minus", C["green"], "true “done”")]):
    for r in rows:
        p, t = r[lab]["previous_z"][L], r[lab]["terminal_z"][L]
        x0 = j * 2.4
        b.plot([x0, x0 + 1], [p, t], "-", color=col, alpha=0.45, lw=0.8)
        b.plot([x0, x0 + 1], [p, t], "o", color=col, ms=2.4)
b.set_xticks([0, 1, 2.4, 3.4], ["previous\nstep", "“done”\nstep", "previous\nstep", "“done”\nstep"], fontsize=6.3)
b.text(0.5, 1.02, "false “done”", transform=b.get_xaxis_transform(), ha="center", fontsize=6.8, color=C["red"])
b.text(2.9, 1.02, "true “done”", transform=b.get_xaxis_transform(), ha="center", fontsize=6.8, color=C["green"])
b.set_ylabel(f"projection on L{L} direction (z)")
b.set_title(f"b  {summ['n']} matched pairs: both read as complete", fontsize=7.6, pad=12)
fig.savefig(FIGS / "perceive.pdf")
print("perceive ok", L, best["cv_auc"])
