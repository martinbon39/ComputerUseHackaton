"""Figure: two measurement traps. (a,b) position confounds of a detection direction; (c) regression to the mean.

Sources:
  data/local/directions_loop_resid.json            0.8B loop direction (MiniWoB++), task-grouped CV AUROC by layer
  data/local/demo/dir_provisoire_fs_resid_post.json 4B provisional false-success direction, before the action JSON
  data/local/demo/dir_provisoire_fs_resid.json      same, last prefill token
  data/local/diagnostic_osw_diag.json               OSWorld diagnostic split, pass 1 (category per task)
  data/local/diagnostic_osw_diag2.json              same tasks, pass 2 (fresh trajectories, unmodified model)
"""
from collections import Counter

from common import FIGS, C, Macros, load, setup_mpl, pct, wilson, write_table

m = Macros("traps")
SL = "data/local/directions_loop_resid.json"
SP = "data/local/demo/dir_provisoire_fs_resid_post.json"
SR = "data/local/demo/dir_provisoire_fs_resid.json"
loop = load("local/directions_loop_resid.json")
fsp = load("local/demo/dir_provisoire_fs_resid_post.json")
fsr = load("local/demo/dir_provisoire_fs_resid.json")

bp = max(range(len(fsp["auc_dom"])), key=lambda i: fsp["auc_dom"][i])
br = max(range(len(fsr["auc_dom"])), key=lambda i: fsr["auc_dom"][i])
m.add("prvN", fsp["n"], SP + " n")
m.add("prvPos", fsp["pos"], SP + " pos")
m.add("prvNeg", fsp["neg"], SP + " neg")
m.add("prvNTasks", len(fsp["tasks"]), SP + " len(tasks)")
m.add("prvAucPost", f"{fsp['auc_dom'][bp]:.3f}", SP + " max auc_dom")
m.add("prvAucPostLayer", bp, SP + " argmax auc_dom")
m.add("prvAucPre", f"{fsr['auc_dom'][br]:.3f}", SR + " max auc_dom")
m.add("prvAucPreLayer", br, SR + " argmax auc_dom")
m.add("prvBaseStep", f"{fsp['baseline_auc_step_index']:.3f}", SP + " baseline_auc_step_index")
m.add("prvBaseCtx", f"{fsp['baseline_auc_context_len']:.3f}", SP + " baseline_auc_context_len")

# Official (exploratory) false-success direction analysis, both passes (osw-analysis).
SS = "data/pod_astra/osw_shared_STATUS.json auc.fs"
af = load("pod_astra/osw_shared_STATUS.json")["auc"]["fs"]
ofr = load("local/directions_osw_explo_fs_resid.json")
ofp = load("local/directions_osw_explo_fs_resid_post.json")
pc = af["position_controlled"]
m.add("ofN", af["resid"]["n"], SS + ".resid.n")
m.add("ofPos", af["resid"]["pos"], SS + ".resid.pos")
m.add("ofNeg", af["resid"]["neg"], SS + ".resid.neg")
m.add("ofTasks", af["resid"]["n_tasks"], SS + ".resid.n_tasks")
m.add("ofResidAuc", f"{af['resid']['auc_dom_best']:.2f}", SS + ".resid.auc_dom_best")
m.add("ofResidLayer", af["resid"]["best_layer"], SS + ".resid.best_layer")
m.add("ofResidLr", f"{af['resid']['auc_lr_at_best']:.2f}", SS + ".resid.auc_lr_at_best")
m.add("ofPostAuc", f"{af['resid_post']['auc_dom_best']:.2f}", SS + ".resid_post.auc_dom_best")
m.add("ofBaseStep", f"{af['resid']['baseline_step_index']:.3f}", SS + ".resid.baseline_step_index")
m.add("ofBaseCtx", f"{af['resid']['baseline_context_len']:.3f}", SS + ".resid.baseline_context_len")
m.add("ofPosOnly", f"{pc['position_only_cv_auc']:.3f}", SS + ".position_controlled.position_only_cv_auc")
m.add("ofPosPlus", f"{pc['resid_best']['auc']:.3f}", SS + ".position_controlled.resid_best.auc")
m.add("ofPosPlusLayer", pc["resid_best"]["layer"], SS + ".position_controlled.resid_best.layer")
m.add("ofPosGain", f"{pc['resid_best']['auc'] - pc['position_only_cv_auc']:.2f}", SS + " resid_best.auc - position_only_cv_auc")
m.add("ofPostPosPlus", f"{pc['resid_post_best']['auc']:.3f}", SS + ".position_controlled.resid_post_best.auc")
write_table("fs_auc", f"% source: {SS}\n\\begin{{tabular}}{{lcc}}\n\\toprule\nPredictor (task-grouped 5-fold CV) & Best layer & AUROC \\\\\n\\midrule\n"
            f"Step index alone & -- & {af['resid']['baseline_step_index']:.3f} \\\\\n"
            f"Context length alone & -- & {af['resid']['baseline_context_len']:.3f} \\\\\n"
            f"Direction, last prefill token & {af['resid']['best_layer']} & {af['resid']['auc_dom_best']:.3f} \\\\\n"
            f"Direction, before the action & {af['resid_post']['best_layer']} & {af['resid_post']['auc_dom_best']:.3f} \\\\\n\\midrule\n"
            f"Position (step, $\\log$ length), logistic & -- & {pc['position_only_cv_auc']:.3f} \\\\\n"
            f"\\quad + direction, last prefill token & {pc['resid_best']['layer']}$^\\dagger$ & {pc['resid_best']['auc']:.3f} \\\\\n"
            f"\\quad + direction, before the action & {pc['resid_post_best']['layer']}$^\\dagger$ & {pc['resid_post_best']['auc']:.3f} \\\\\n"
            "\\bottomrule\n\\end{tabular}\n", "traps")

# Regression to the mean: tasks scored in both passes, category in pass 1 -> category in pass 2.
p1 = {t["task"]: t for t in load("local/diagnostic_osw_diag.json")["tasks"] if t["score"] is not None}
d2 = load("local/diagnostic_osw_diag2.json")
p2 = {t["task"]: t for t in d2["tasks"] if t["score"] is not None}
both = sorted(set(p1) & set(p2))
groups = ["false_success", "step_limit", "loop", "success"]
trans = {g: Counter(p2[k]["category"] for k in both if p1[k]["category"] == g) for g in groups}
fs_n = sum(trans["false_success"].values())
fs_again = trans["false_success"]["false_success"]
fs_succ = trans["false_success"]["success"]
lo, hi = wilson(fs_again, fs_n)
S2 = "data/local/diagnostic_osw_diag.json + data/local/diagnostic_osw_diag2.json"
m.add("rtmBoth", len(both), S2 + " tasks scored in both passes")
m.add("rtmFsN", fs_n, S2 + " pass-1 false_success tasks scored in pass 2")
m.add("rtmFsAgain", fs_again, S2 + " ... still false_success in pass 2")
m.add("rtmFsAgainPct", pct(fs_again / fs_n, 0), S2 + " fs_again / fs_n")
m.add("rtmFsAgainLo", pct(lo, 0), S2 + " Wilson 95% lower")
m.add("rtmFsAgainHi", pct(hi, 0), S2 + " Wilson 95% upper")
m.add("rtmFsSucc", fs_succ, S2 + " pass-1 false_success -> pass-2 success")
m.add("rtmFakeEffect", pct(1 - fs_again / fs_n, 0), S2 + " 1 - fs_again/fs_n (apparent effect of a null patch)")
m.add("rtmSuccN", sum(trans["success"].values()), S2 + " pass-1 success tasks scored in pass 2")
m.add("rtmSuccAgain", trans["success"]["success"], S2 + " ... still success in pass 2")
m.add("rtmPassTwoScored", len(p2), "data/local/diagnostic_osw_diag2.json scored tasks")
m.write()

plt = setup_mpl()
fig, axs = plt.subplots(1, 3, figsize=(7.0, 2.2), gridspec_kw={"width_ratios": [1, 1, 1.25], "wspace": 0.30})


def panel(ax, dd, title, ylab, extra=None):
    L = range(len(dd["auc_dom"]))
    ax.fill_between([-1, len(dd["auc_dom"])], 0.4, max(dd["baseline_auc_step_index"], dd["baseline_auc_context_len"]),
                    color="#EEEEEE", lw=0)
    ax.plot(L, dd["auc_dom"], "-o", ms=2.2, color=C["blue"], lw=1.2)
    if extra is not None:
        ax.plot(range(len(extra["auc_dom"])), extra["auc_dom"], "-", color=C["sky"], lw=1)
    ax.axhline(dd["baseline_auc_step_index"], color=C["red"], lw=1, ls=":")
    ax.axhline(dd["baseline_auc_context_len"], color=C["orange"], lw=1, ls=":")
    ax.set_xlim(-0.5, len(dd["auc_dom"]) - 0.5), ax.set_ylim(0.4, 1.0)
    ax.set_xlabel("layer"), ax.set_ylabel(ylab)
    ax.set_title(title, fontsize=7.6)


panel(axs[0], loop, "a  0.8B loops: beats position", "task-grouped AUROC")
i = max(range(len(loop["auc_dom"])), key=lambda k: loop["auc_dom"][k])
axs[0].annotate(f"{loop['auc_dom'][i]:.2f}", (i, loop["auc_dom"][i]), xytext=(4, 3), textcoords="offset points",
                fontsize=6.5, color=C["blue"])
axs[0].text(0.6, 0.43, "grey: at or below the best\nposition baseline", fontsize=5.8, color="#777777")
panel(axs[1], ofr, "b  4B false success: does not", "", extra=ofp)
bp = max(range(len(ofr["auc_dom"])), key=lambda i: ofr["auc_dom"][i])
axs[1].annotate(f"{ofr['auc_dom'][bp]:.2f}", (bp, ofr["auc_dom"][bp]), xytext=(-6, 10), textcoords="offset points",
                fontsize=6.5, color=C["blue"], arrowprops=dict(arrowstyle="-", color=C["blue"], lw=0.5))
axs[1].text(0.5, 0.92, f"position baselines\n{ofr['baseline_auc_step_index']:.3f} (step), {ofr['baseline_auc_context_len']:.3f} (length)",
            fontsize=6, color=C["orange"])
pass
axs[1].plot([], [], "-o", ms=2.2, color=C["blue"], label="last prefill token")
axs[1].plot([], [], "-", color=C["sky"], label="before the action")
axs[1].legend(frameon=False, fontsize=5.8, loc="lower right")

ax = axs[2]
lab = {"false_success": "false success", "step_limit": "step limit", "loop": "loop", "success": "success"}
col2 = {"success": C["green"], "false_success": C["red"], "step_limit": C["orange"], "loop": C["purple"],
        "infeasible_correct": C["sky"], "other": C["grey"]}
for j, g in enumerate(groups):
    n = sum(trans[g].values())
    left = 0
    for k in ["false_success", "step_limit", "loop", "success", "infeasible_correct", "other"]:
        v = trans[g].get(k, 0)
        if v:
            ax.barh(j, v / n, left=left, color=col2[k], edgecolor="white", height=0.7)
            if v / n >= 0.12:
                ax.text(left + v / n / 2, j, str(v), ha="center", va="center", fontsize=6.3, color="white", fontweight="bold")
            left += v / n
    ax.text(1.02, j, f"n={n}", va="center", fontsize=6.2, color="#555555")
ax.set_yticks(range(len(groups)), ["pass 1:\n" + lab[g] for g in groups], fontsize=6.4)
ax.invert_yaxis()
ax.set_xlim(0, 1), ax.set_xticks([0, 0.5, 1], ["0", "50%", "100%"])
ax.set_xlabel("pass 2 outcome, same task, same model")
ax.set_title(f"c  Only {pct(fs_again / fs_n, 0)}% of false successes recur", fontsize=7.6)
from matplotlib.patches import Patch
ax.legend([Patch(color=col2[k]) for k in ["false_success", "step_limit", "loop", "success", "infeasible_correct"]],
          ["false success", "step limit", "loop", "success", "correct refusal"], ncol=5, frameon=False, fontsize=5.6,
          loc="upper left", bbox_to_anchor=(-0.05, -0.27), handlelength=0.8, columnspacing=0.7)
fig.savefig(FIGS / "traps.pdf")
print("traps ok", fs_again, fs_n, len(both))
