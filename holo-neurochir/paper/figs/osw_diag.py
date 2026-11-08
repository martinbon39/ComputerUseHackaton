"""Holo-3.1-4B on OSWorld (split_diag, pass 1): success rate, failure taxonomy, step labels.

Source: data/local/diagnostic_osw_diag.json (holo/osw_taxonomy.py, rules sha1 recorded in the file).
"""
from collections import Counter, defaultdict
from common import Macros, load, wilson, pct, write_table, setup_mpl, FIGS, C

SRC = "data/local/diagnostic_osw_diag.json"
d = load("local/diagnostic_osw_diag.json")
tasks = d["tasks"]
m = Macros("osw_diag")

scored = [t for t in tasks if t["score"] is not None]
n_scored = len(scored)
n_full = sum(1 for t in scored if t["score"] == 1)
mean_score = sum(t["score"] for t in scored) / n_scored
fails = [t for t in scored if t["score"] == 0]
lo, hi = wilson(n_full, n_scored)
cat = Counter(t["category"] for t in tasks)
assert cat == Counter(d["categories"]), "recomputed categories differ from file"
assert len(fails) == d["n_fail"], (len(fails), d["n_fail"])

m.add("oswRulesSha", d["rules_sha1"], SRC + " rules_sha1")
m.add("oswNTasks", len(tasks), SRC + " len(tasks)")
m.add("oswNScored", n_scored, SRC + " tasks with score != null")
m.add("oswNUnscored", len(tasks) - n_scored, SRC + " tasks with score == null")
m.add("oswNSuccess", n_full, SRC + " score == 1")
m.add("oswSuccessPct", pct(n_full / n_scored), SRC + " score == 1 / scored")
m.add("oswSuccessLo", pct(lo), SRC + " Wilson 95% lower")
m.add("oswSuccessHi", pct(hi), SRC + " Wilson 95% upper")
m.add("oswMeanScorePct", pct(mean_score), SRC + " mean(score) over scored")
m.add("oswNPartial", sum(1 for t in scored if 0 < t["score"] < 1), SRC + " 0<score<1")
m.add("oswNFail", len(fails), SRC + " score == 0")
for k in ["false_success", "loop", "step_limit", "other", "infeasible_correct", "success"]:
    m.add("oswCat" + k.title().replace("_", ""), cat.get(k, 0), SRC + f" categories.{k}")
removable = cat["false_success"] + cat["loop"] + cat["step_limit"]
m.add("oswRemovable", removable, SRC + " false_success+loop+step_limit (primary category)")
m.add("oswRemovablePct", pct(removable / len(fails), 0), SRC + " removable / n_fail")
m.add("oswFsPct", pct(cat["false_success"] / len(fails), 0), SRC + " false_success / n_fail")
m.add("oswLoopPct", pct(cat["loop"] / len(fails), 0), SRC + " loop / n_fail")
m.add("oswStepPct", pct(cat["step_limit"] / len(fails), 0), SRC + " step_limit / n_fail")
sl_any = d["fail_flags"]["step_limit_any"]
m.add("oswStepAny", sl_any, SRC + " fail_flags.step_limit_any")
m.add("oswStepAnyPct", pct(sl_any / len(fails), 0), SRC + " step_limit_any / n_fail")
m.add("oswLoopAny", d["fail_flags"]["loop_any"], SRC + " fail_flags.loop_any")
fs_inf = sum(1 for t in tasks if t["category"] == "false_success" and t["infeasible"])
m.add("oswFsInfeasible", fs_inf, SRC + " false_success & infeasible")
m.add("oswFsFeasible", cat["false_success"] - fs_inf, SRC + " false_success & feasible")
for k, v in d["step_labels"].items():
    m.add("oswLab" + {"loop+": "LoopPos", "loop-": "LoopNeg", "fs+": "FsPos", "fs-": "FsNeg"}[k], v,
          SRC + f" step_labels.{k}")
steps_fail_fs = [t["n_steps"] for t in tasks if t["category"] == "false_success"]
m.add("oswFsMedianSteps", sorted(steps_fail_fs)[len(steps_fail_fs) // 2], SRC + " median n_steps of false_success tasks")
m.add("oswFsAtCap", sum(1 for s in steps_fail_fs if s >= 50), SRC + " false_success tasks with n_steps>=50")
m.write()

# Per-domain table.
dom = defaultdict(lambda: Counter())
for t in tasks:
    D = t["task"].split("/")[0]
    dom[D]["n"] += 1
    if t["score"] is not None:
        dom[D]["scored"] += 1
        dom[D]["succ"] += t["score"] == 1
        dom[D]["partial"] += 0 < t["score"] < 1
    dom[D][t["category"]] += 1
rows = []
for D in sorted(dom, key=lambda k: -dom[k]["n"]):
    c = dom[D]
    rows.append(f"{D.replace('libreoffice_', 'lo-').replace('_', '-')} & {c['n']} & {c['succ']}/{c['scored']} & {c['partial']} & "
                f"{c['false_success']} & {c['step_limit']} & {c['loop']} & {c['other'] + c['unscored']} \\\\")
tot = Counter()
for c in dom.values():
    tot.update(c)
body = ("\\begin{tabular}{lrrrrrrr}\n\\toprule\nDomain & Tasks & Success & Partial & FS & Step lim. & Loop & Other + unsc. \\\\\n\\midrule\n"
        + "\n".join(rows) + "\n\\midrule\n"
        + f"Total & {tot['n']} & {tot['succ']}/{tot['scored']} & {tot['partial']} & {tot['false_success']} & {tot['step_limit']} & {tot['loop']} & {tot['other'] + tot['unscored']} \\\\\n"
        + "\\bottomrule\n\\end{tabular}\n")
write_table("osw_domains", f"% source: {SRC}\n" + body, "osw_diag")

# Figure: outcome by domain + episode length by outcome.
plt = setup_mpl()
fig, ax = plt.subplots(1, 2, figsize=(7.0, 2.45), gridspec_kw={"width_ratios": [1.6, 1], "wspace": 0.55})
cats = [("success", "success", C["green"]), ("infeasible_correct", "correct refusal", C["sky"]),
        ("false_success", "false success", C["red"]), ("step_limit", "step limit", C["orange"]),
        ("loop", "loop", C["purple"]), ("other", "other / unscored", C["grey"])]
doms = sorted(dom, key=lambda k: (dom[k]["succ"] / max(dom[k]["scored"], 1)))
nice = lambda D: D.replace("libreoffice_", "").replace("multi_apps", "multi-apps").replace("vs_code", "VS Code") \
    .replace("thunderbird", "Thunderbird").replace("chrome", "Chrome").replace("gimp", "GIMP").replace("vlc", "VLC") \
    .replace("os", "OS").replace("calc", "Calc").replace("impress", "Impress").replace("writer", "Writer")
for j, D in enumerate(doms):
    c = dom[D]
    left = 0
    for k, lab, col in cats:
        v = c[k] + (c["unscored"] if k == "other" else 0)
        if v:
            ax[0].barh(j, v / c["n"], left=left, color=col, edgecolor="white", height=0.72)
            if v / c["n"] >= 0.1:
                ax[0].text(left + v / c["n"] / 2, j, str(v), ha="center", va="center", color="white", fontsize=6.2,
                           fontweight="bold")
            left += v / c["n"]
    ax[0].text(1.015, j, f"{c['succ']}/{c['scored']}", va="center", fontsize=6.2, color="#555555")
ax[0].set_yticks(range(len(doms)), [nice(D) for D in doms], fontsize=6.8)
ax[0].set_xlim(0, 1), ax[0].set_xticks([0, 0.5, 1], ["0", "50%", "100%"])
ax[0].set_xlabel("share of the domain's tasks (success count / scored at right)")
ax[0].set_title(f"a  Outcome by domain ({len(tasks)} tasks)", fontsize=7.6)
from matplotlib.patches import Patch
ax[0].legend([Patch(color=c_) for _, _, c_ in cats], [l for _, l, _ in cats], ncol=6, frameon=False, fontsize=5.8,
             loc="upper left", bbox_to_anchor=(-0.2, -0.2), handlelength=0.8, columnspacing=0.7)
groups = [("success", "success", C["green"]), ("false_success", "false success", C["red"]),
          ("step_limit", "step limit", C["orange"])]
data = [[t["n_steps"] for t in tasks if t["category"] == k] for k, _, _ in groups]
bp = ax[1].boxplot(data, orientation="horizontal", widths=0.55, patch_artist=True, medianprops={"color": "black"},
                   flierprops={"markersize": 2})
for patch, (_, _, col) in zip(bp["boxes"], groups):
    patch.set_facecolor(col)
    patch.set_alpha(0.8)
ax[1].set_yticks(range(1, len(groups) + 1), [g[1] for g in groups], fontsize=6.8)
ax[1].set_xlabel("episode length (steps, cap 50)")
ax[1].set_title("b  False successes are not early quits", fontsize=7.6)
fig.savefig(FIGS / "osw_failures.pdf")
print("osw_diag ok", n_full, n_scored, len(fails), dict(cat))
