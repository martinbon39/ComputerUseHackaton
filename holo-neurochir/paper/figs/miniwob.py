"""Holo-3.1-0.8B on MiniWoB++: diagnostic, loop-direction detection, offline weight-edit screening,
behavioural steering test, replay fidelity.

Sources (all copied verbatim into data/):
  data/local/diag08b_full.json          holo.diagnostic on pod /workspace/runs/diag (2026-11-07)
  data/local/directions_loop_resid.json holo.direction, loop target, residual site, min_t=2
  data/pod_astra/train_analysis.json    Astra round-1 recomputation (152 rollouts, seeds 0-5)
  data/pod_astra/a2_ranking.json        offline screening of all weight-edit candidates (40 fixed contexts)
  data/pod_astra/a2_final_summary.json  frozen candidate on reserved seeds 6-7
  data/pod_astra/a2_dev_summary.json    frozen candidate on full development seeds 0-5
  data/pod_astra/r3/*.json              round-3 free-generation steering arms
  data/pod_astra/fidelity.json          replay fidelity vs recorded residuals
"""
from collections import defaultdict
from common import (Macros, load, wilson, cluster_bootstrap, pct, write_table, setup_mpl, FIGS, C, tex_escape)

m = Macros("miniwob")
plt = setup_mpl()

# ---------------------------------------------------------------- diagnostic
S = "data/local/diag08b_full.json"
d = load("local/diag08b_full.json")
n_norm, n_imp = d["normal"], d["imp"]
n_fail = n_norm - d["cats"]["success"]
m.add("mwNNormal", n_norm, S + " normal")
m.add("mwNImp", n_imp, S + " imp")
m.add("mwNTasks", len(d["per_task"]), S + " len(per_task)")
m.add("mwSuccessPct", pct(d["success"]), S + " success")
lo, hi = wilson(d["cats"]["success"], n_norm)
m.add("mwSuccessLo", pct(lo), S + " Wilson 95% lower on cats.success/normal")
m.add("mwSuccessHi", pct(hi), S + " Wilson 95% upper")
m.add("mwNFail", n_fail, S + " normal - cats.success")
m.add("mwLoopSharePct", pct(d["loop_fail_share"]), S + " loop_fail_share")
m.add("mwFsSharePct", pct(d["fs_fail_share"]), S + " fs_fail_share")
m.add("mwLoopPos", d["loop_pos"], S + " loop_pos")
m.add("mwLoopNeg", d["loop_neg"], S + " loop_neg")
m.add("mwFsPos", d["fs_pos"], S + " fs_pos")
m.add("mwFsNeg", d["done_correct"], S + " done_correct")
m.add("mwFsAnswer", d["fs_answer"], S + " fs_answer")
m.add("mwFsSubmit", d["fs_submit"], S + " fs_submit")
m.add("mwImpFs", d["imp_cats"].get("false_success", 0), S + " imp_cats.false_success")
rows = []
for k, lab in [("false_success", "False success"), ("loop", "Loop"), ("grounding", "Grounding miss"),
               ("abandon_or_budget", "Abandon / budget"), ("wrong_final_action", "Wrong final action")]:
    v = d["cats"].get(k, 0)
    rows.append(f"{lab} & {v} & {pct(v / n_fail)} \\\\")
    m.add("mwCat" + k.title().replace("_", ""), v, S + f" cats.{k}")
write_table("mw_diag", f"% source: {S}\n\\begin{{tabular}}{{lrr}}\n\\toprule\nPrimary category & Rollouts & \\% of failures \\\\\n\\midrule\n"
            + "\n".join(rows) + f"\n\\midrule\nTotal failures & {n_fail} & 100.0 \\\\\n\\bottomrule\n\\end{{tabular}}\n", "miniwob")

# ---------------------------------------------------------------- detection
S1 = "data/local/directions_loop_resid.json"
dl = load("local/directions_loop_resid.json")
best = max(range(len(dl["auc_dom"])), key=lambda i: dl["auc_dom"][i])
m.add("mwAucN", dl["n"], S1 + " n")
m.add("mwAucPos", dl["pos"], S1 + " pos")
m.add("mwAucNeg", dl["neg"], S1 + " neg")
m.add("mwAucNTasks", len(dl["tasks"]), S1 + " len(tasks)")
m.add("mwAucBest", f"{dl['auc_dom'][best]:.2f}", S1 + f" max(auc_dom) at layer {best}")
m.add("mwAucBestExact", f"{dl['auc_dom'][best]:.3f}", S1 + " max(auc_dom)")
m.add("mwAucBestLayer", best, S1 + " argmax(auc_dom)")
m.add("mwAucLr", f"{max(dl['auc_lr']):.2f}", S1 + " max(auc_lr)")
m.add("mwAucLrLayer", max(range(len(dl['auc_lr'])), key=lambda i: dl['auc_lr'][i]), S1 + " argmax(auc_lr)")
m.add("mwAucStep", f"{dl['baseline_auc_step_index']:.2f}", S1 + " baseline_auc_step_index")
m.add("mwAucCtx", f"{dl['baseline_auc_context_len']:.2f}", S1 + " baseline_auc_context_len")
m.add("mwAucMinT", dl["min_t"], S1 + " min_t")
S2 = "data/pod_astra/train_analysis.json"
ta = load("pod_astra/train_analysis.json")
b2 = max(range(len(ta["auc_cv_by_task"])), key=lambda i: ta["auc_cv_by_task"][i])
m.add("mwAstraAuc", f"{ta['auc_cv_by_task'][b2]:.3f}", S2 + f" max(auc_cv_by_task) at layer {b2}")
m.add("mwAstraLayer", b2, S2 + " argmax(auc_cv_by_task)")
m.add("mwAstraPos", f"{ta['position_auc']:.3f}", S2 + " position_auc")
m.add("mwAstraCtx", f"{ta['context_auc']:.3f}", S2 + " context_auc")
m.add("mwAstraFitN", ta["fit_n"], S2 + " fit_n")
m.add("mwAstraFitPos", ta["fit_positive"], S2 + " fit_positive")
m.add("mwAstraRuns", len(ta["runs"]), S2 + " len(runs)")

fig, ax = plt.subplots(figsize=(3.3, 2.15))
L = range(len(dl["auc_dom"]))
ax.plot(L, dl["auc_dom"], "-o", ms=2.5, color=C["blue"], label="diff-of-means (task-grouped CV)")
ax.plot(L, dl["auc_lr"], "-s", ms=2.2, color=C["sky"], label="logistic probe")
ax.plot(range(len(ta["auc_cv_by_task"])), ta["auc_cv_by_task"], "--", lw=1, color=C["purple"],
        label="diff-of-means, independent refit")
ax.axhline(dl["baseline_auc_context_len"], color=C["orange"], lw=1, ls=":", label="context-length baseline")
ax.axhline(dl["baseline_auc_step_index"], color=C["red"], lw=1, ls=":", label="step-index baseline")
ax.axhline(0.5, color=C["grey"], lw=0.6)
ax.set_xlabel("Layer")
ax.set_ylabel("AUROC (loop+ vs loop-)")
ax.set_ylim(0.4, 1.0)
ax.legend(frameon=False, loc="lower right", fontsize=6.3)
fig.savefig(FIGS / "loop_auroc.pdf")

# ---------------------------------------------------------------- offline weight-edit screening
S3 = "data/pod_astra/a2_ranking.json"
rk = [r for r in load("pod_astra/a2_ranking.json") if r["name"] != "r2_identity"]
m.add("mwOffNCand", len(rk), S3 + " candidates excluding r2_identity")
m.add("mwOffNQualify", sum(r["qualifies"] for r in rk), S3 + " qualifies == true (screening criterion)")
fig, ax = plt.subplots(figsize=(3.3, 2.3))
for r in rk:
    x, y = r["deltas"]["healthy"], r["deltas"]["loop+"]
    col = C["green"] if r["qualifies"] else C["grey"]
    ax.scatter(x, y, s=10 + 3 * (r["weights"] ** 0.25) / 4, color=col, alpha=0.8, edgecolor="none")
xs = [r["deltas"]["healthy"] for r in rk]
lim = max(abs(min(xs)), abs(max(xs)), max(abs(r["deltas"]["loop+"]) for r in rk)) * 1.05
import numpy as np
g = np.linspace(-lim, lim, 10)
ax.plot(g, g, color=C["grey"], lw=0.7, ls="--", label="equal decrease")
ax.plot(g, 3 * np.clip(g, 0, None), color=C["red"], lw=0.8, label="3x selectivity bound")
ax.axhline(0, color="black", lw=0.4)
ax.axvline(0, color="black", lw=0.4)
ax.set_xscale("symlog", linthresh=0.003)
ax.set_yscale("symlog", linthresh=0.003)
ax.set_xticks([-0.1, -0.01, 0, 0.01, 0.1])
ax.set_yticks([0, 0.01, 0.1])
ax.set_ylim(-0.0015, 0.6)
ax.set_xlabel("Decrease on healthy steps (nat/token)")
ax.set_ylabel("Decrease on loop+ steps (nat/token)")
ax.scatter([], [], color=C["green"], s=10, label="passes screening")
ax.scatter([], [], color=C["grey"], s=10, label="fails screening")
ax.legend(frameon=False, fontsize=6.2, loc="upper left")
fig.savefig(FIGS / "offline_selectivity.pdf")

S4 = "data/pod_astra/a2_final_summary.json"
S5 = "data/pod_astra/a2_dev_summary.json"
fin = load("pod_astra/a2_final_summary.json")
dev = load("pod_astra/a2_dev_summary.json")
st = fin["patch"]["stats"]
m.add("mwPatchTargeted", f"{st['n_modified']:,}".replace(",", "{,}"), S4 + " patch.stats.n_modified")
m.add("mwPatchChanged", f"{st['actual_changed']:,}".replace(",", "{,}"), S4 + " patch.stats.actual_changed")
m.add("mwPatchPct", f"{st['actual_pct']:.3f}", S4 + " patch.stats.actual_pct (percent of all params)")
m.add("mwPatchFro", f"{st['actual_delta_fro']:.2f}", S4 + " patch.stats.actual_delta_fro")
m.add("mwRandFro", f"{fin['random']['stats']['actual_delta_fro']:.2f}", S4 + " random.stats.actual_delta_fro")
m.add("mwTotalParams", f"{st['total_params']:,}".replace(",", "{,}"), S4 + " patch.stats.total_params")
rows = []
for split, src, summ in [("Dev (seeds 0--5)", S5, dev), ("Reserved (seeds 6--7)", S4, fin)]:
    for gname, lab in [("loop+", "loop+"), ("healthy", "healthy"), ("loop-", "loop$-$"), ("success", "success")]:
        g = summ["patch"]["groups"][gname]
        o = summ["original"]["groups"][gname]
        rnd = summ.get("random", {}).get("groups", {}).get(gname)
        rdec = f"{(o['mean_lp'] - rnd['mean_lp']) * 1000:.2f}" if rnd else "--"
        ci = g["decrease_task_bootstrap_ci95"]
        rows.append(f"{split if gname == 'loop+' else ''} & {lab} & {g['n']} & {g['decrease'] * 1000:.2f} & "
                    f"[{ci[0] * 1000:.2f}, {ci[1] * 1000:.2f}] & {rdec} \\\\")
    rows.append("\\midrule")
rows = rows[:-1]
write_table("mw_offline", f"% sources: {S5}, {S4}\n\\begin{{tabular}}{{llrrcr}}\n\\toprule\nSplit & Steps & $n$ & Decrease & 95\\% CI (task bootstrap) & Random dir. \\\\\n\\midrule\n"
            + "\n".join(rows) + "\n\\bottomrule\n\\end{tabular}\n", "miniwob")
g = fin["patch"]["groups"]
m.add("mwFinLoopDec", f"{g['loop+']['decrease'] * 1000:.2f}", S4 + " patch.groups.loop+.decrease x1000")
m.add("mwFinHealthyDec", f"{g['healthy']['decrease'] * 1000:.2f}", S4 + " patch.groups.healthy.decrease x1000")
m.add("mwFinRatio", f"{g['loop+']['decrease'] / g['healthy']['decrease']:.2f}", S4 + " loop+.decrease / healthy.decrease")
m.add("mwFinRatioRand", f"{(fin['original']['groups']['loop+']['mean_lp'] - fin['random']['groups']['loop+']['mean_lp']) / (fin['original']['groups']['healthy']['mean_lp'] - fin['random']['groups']['healthy']['mean_lp']):.2f}",
      S4 + " random loop+ decrease / random healthy decrease")
m.add("mwFinLoopN", g["loop+"]["n"], S4 + " patch.groups.loop+.n")
m.add("mwFinHealthyN", g["healthy"]["n"], S4 + " patch.groups.healthy.n")

# ---------------------------------------------------------------- behavioural steering (round 3)
SR = "data/pod_astra/r3/<arm>.json"
arms = [("baseline", "Original (no hook)"), ("baseline_repeat", "Original, re-run"), ("identity", r"Hook, $\alpha=0$"),
        ("random_all", "Random dir., all layers"), ("u10_L10", r"$u_{10}$ at L10"), ("u10_L9_13", r"$u_{10}$ at L9--13"),
        ("u10_all", r"$u_{10}$, all layers"), ("u10_all_a2", r"$u_{10}$, all layers, $\alpha=2$"),
        ("native_all", r"per-layer $u_\ell$, all layers"),
        ("paired_all", "matched-pair dir."), ("paired_pca_all", "matched-pair PCA"), ("mlp_all", "MLP-site dir."),
        ("mlp_pca_all", "MLP-site PCA"), ("mean_all", "mean of layer dirs."), ("strict_paired", "strict pairs"),
        ("strict_paired_pca", "strict pairs PCA"), ("strict_mlp", "strict MLP"), ("strict_mlp_pca", "strict MLP PCA")]


def rates(res):
    rep = [r for r in res if r["row"]["label"] == "loop+"]
    hl = [r for r in res if r["row"]["label"] != "loop+"]
    return rep, hl


def ctx(r):
    return (r["row"]["run"], r["row"]["t"])


rows, pts = [], []
base = load("pod_astra/r3/baseline.json")
for name, lab in arms:
    a = load(f"pod_astra/r3/{name}.json")
    rep, hl = rates(a["results"])
    complete = a.get("complete", True) is not False
    R = sum(r["repeat"] for r in rep) / len(rep) if rep else None
    H = sum(r["healthy_match"] for r in hl) / len(hl) if hl else None
    if a.get("repeat") is not None:
        assert abs(R - a["repeat"]) < 1e-9, (name, R, a["repeat"])
    if complete:
        assert abs(H - a["health"]) < 1e-9, (name, H, a["health"])
    gR = defaultdict(list)
    for r in rep:
        gR[ctx(r)].append(r["repeat"])
    gH = defaultdict(list)
    for r in hl:
        gH[ctx(r)].append(r["healthy_match"])
    f = lambda xs: sum(xs) / len(xs)
    if complete:
        rlo, rhi = cluster_bootstrap(gR, f)
        hlo, hhi = cluster_bootstrap(gH, f)
        rows.append(f"{lab} & {pct(R)} [{pct(rlo, 0)}, {pct(rhi, 0)}] & {pct(H)} [{pct(hlo, 0)}, {pct(hhi, 0)}] & "
                    f"{len(rep) + len(hl)} & complete \\\\")
        pts.append((name, lab, R, H, rlo, rhi, hlo, hhi))
    else:
        rows.append(f"{lab} & n/m & $\\le$ {pct(a['health_upper'])} & {len(rep) + len(hl)} & rejected early \\\\")
    KEYS = {"baseline": "Base", "baseline_repeat": "BaseRe", "identity": "Ident", "random_all": "Rand",
            "u10_L10": "UTen", "u10_L9_13": "UNineThirteen", "u10_all": "UAll", "u10_all_a2": "UAllTwo",
            "native_all": "Native"}
    key = "mwSt" + KEYS.get(name, "X")
    if complete:
        m.add(key + "Repeat", pct(R), f"data/pod_astra/r3/{name}.json repeat (recomputed from results)")
        m.add(key + "Health", pct(H), f"data/pod_astra/r3/{name}.json health (recomputed from results)")
for name in ["u10_all_am1_aborted", "u10_add025_aborted"]:
    a = load(f"pod_astra/r3/{name}.json")
    lab = r"$u_{10}$ amplification $\alpha=-1$" if "am1" in name else r"constant addition $-0.25\,u_{10}$"
    rows.append(f"{lab} & n/m & n/m & {a['saved_generations']} & aborted (invalid) \\\\")
write_table("mw_steering", "% sources: data/pod_astra/r3/<arm>.json (95% CI: bootstrap over contexts, 2000 reps)\n"
            "\\begin{tabular}{lccrl}\n\\toprule\nArm & REPEAT \\% [95\\% CI] & HEALTH \\% [95\\% CI] & Gens & Status \\\\\n\\midrule\n"
            + "\n".join(rows) + "\n\\bottomrule\n\\end{tabular}\n", "miniwob")
nloop = len({ctx(r) for r in rates(base["results"])[0]})
nh = len({ctx(r) for r in rates(base["results"])[1]})
m.add("mwStNLoopCtx", nloop, "data/pod_astra/r3/baseline.json distinct loop+ contexts")
m.add("mwStNHealthCtx", nh, "data/pod_astra/r3/baseline.json distinct healthy contexts")
m.add("mwStK", len(base["results"]) // (nloop + nh), "data/pod_astra/r3/baseline.json generations per context")
m.add("mwStTargetRepeat", pct(base["repeat"] * 0.5), "data/pod_astra/r3/PROTOCOL.md: REPEAT <= 50% of baseline")
m.add("mwStTargetHealth", pct(base["health"] - 0.05), "data/pod_astra/r3/PROTOCOL.md: HEALTH >= baseline - 5 pts")
sel = load("pod_astra/r3/selection.json")
m.add("mwStBudget", sel["budget_used"], "data/pod_astra/r3/selection.json budget_used")
m.add("mwStBudgetMax", sel["budget_limit"], "data/pod_astra/r3/selection.json budget_limit")

fig, ax = plt.subplots(figsize=(3.3, 2.4))
ax.add_patch(plt.Rectangle((base["health"] - 0.05, 0), 1, base["repeat"] * 0.5, color=C["green"], alpha=0.12, lw=0))
ax.text(0.99, 0.02, "target region", ha="right", va="bottom", fontsize=6.5, color=C["green"], transform=ax.transAxes)
colors = {"baseline": C["black"], "baseline_repeat": C["black"], "identity": C["grey"], "random_all": C["orange"]}
for name, lab, R, H, rlo, rhi, hlo, hhi in pts:
    col = colors.get(name, C["blue"])
    ax.errorbar(H, R, xerr=[[H - hlo], [hhi - H]], yerr=[[R - rlo], [rhi - R]], fmt="o", ms=3.2, color=col,
                elinewidth=0.6, capsize=1.2, alpha=0.9)
    short = {"baseline": ("original", (-4, 5)), "random_all": ("random dir.", (4, 4)),
             "native_all": ("per-layer $u_\\ell$", (4, -9)), "u10_L9_13": ("$u_{10}$, L9-13", (-4, -10)),
             "u10_all_a2": ("$u_{10}$ all, $\\alpha$=2", (-4, 5))}
    if name in short:
        t, off = short[name]
        ax.annotate(t, (H, R), textcoords="offset points", xytext=off, fontsize=6.2,
                    ha="right" if off[0] < 0 else "left", color=col)
ax.set_xlabel("HEALTH (healthy contexts, %)")
ax.set_ylabel("REPEAT (loop+ contexts, %)")
ax.set_xlim(0.3, 1.0)
ax.set_ylim(0.0, 1.05)
ax.xaxis.set_major_formatter(plt.FuncFormatter(lambda v, _: f"{100 * v:.0f}"))
ax.yaxis.set_major_formatter(plt.FuncFormatter(lambda v, _: f"{100 * v:.0f}"))
fig.savefig(FIGS / "steering_pareto.pdf")

# ---------------------------------------------------------------- replay fidelity
SF = "data/pod_astra/fidelity.json"
fi = load("pod_astra/fidelity.json")
byl = defaultdict(list)
for e in fi:
    byl[e["layer"]].append(e)
rows = []
for l in sorted(byl):
    v = byl[l]
    rows.append(f"{l} & {len(v)} & {min(e['cos'] for e in v):.5f} & {max(e['relative_error'] for e in v):.4f} \\\\")
write_table("mw_fidelity", f"% source: {SF}\n\\begin{{tabular}}{{rrrr}}\n\\toprule\nLayer & Contexts & min cosine & max rel. error \\\\\n\\midrule\n"
            + "\n".join(rows) + "\n\\bottomrule\n\\end{tabular}\n", "miniwob")
m.add("mwFidMinCos", f"{min(e['cos'] for e in fi):.4f}", SF + " min cos over all layers")
m.add("mwFidN", len({(e['run'], e['t']) for e in fi}), SF + " distinct contexts")
m.write()
print("miniwob ok")

# ---------------------------------------------------------------- appendix tables
pt = sorted(d["per_task"].items(), key=lambda kv: (-int(kv[1].split("/")[0]) / int(kv[1].split("/")[1]), kv[0]))
half = (len(pt) + 1) // 2
lines = []
for i in range(half):
    a = pt[i]
    b = pt[i + half] if i + half < len(pt) else ("", "")
    lines.append(f"\\texttt{{{a[0]}}} & {a[1]} & " + (f"\\texttt{{{b[0]}}} & {b[1]}" if b[0] else " & ") + " \\\\")
write_table("mw_pertask", f"% source: {S} per_task\n\\begin{{tabular}}{{lrlr}}\n\\toprule\nTask & Success & Task & Success \\\\\n\\midrule\n"
            + "\n".join(lines) + "\n\\bottomrule\n\\end{tabular}\n", "miniwob")

def spec_str(r):
    sp = r.get("spec") or {}
    L = sp.get("layers") or []
    lay = (f"{L[0]}--{L[-1]}" if len(L) > 1 and L == list(range(L[0], L[-1] + 1)) else ",".join(map(str, L))) if L else "--"
    return lay, sp.get("alpha", "--"), sp.get("topk") or "all", "+".join(sp.get("writers") or [])

lines = []
for r in sorted(rk, key=lambda r: -r["deltas"]["loop+"]):
    lay, al, k, w = spec_str(r)
    dd = r["deltas"]
    lines.append(f"\\texttt{{{tex_escape(r['name'])}}} & {lay} & {al} & {k} & {w} & {r['weights']:,} & "
                 f"{1000 * dd['loop+']:.2f} & {1000 * dd['healthy']:.2f} & {1000 * dd['loop-']:.2f} & {1000 * dd['success']:.2f} & "
                 f"{'yes' if r['qualifies'] else 'no'} \\\\")
write_table("mw_candidates", f"% source: {S3}\n\\begin{{tabular}}{{lllllrrrrrl}}\n\\toprule\nCandidate & Layers & $\\alpha$ & top-$k$ & Writers & Weights & $D_{{\\text{{loop+}}}}$ & $D_{{\\text{{healthy}}}}$ & $D_{{\\text{{loop}}-}}$ & $D_{{\\text{{succ}}}}$ & Pass \\\\\n\\midrule\n"
            + "\n".join(lines) + "\n\\bottomrule\n\\end{tabular}\n", "miniwob")
print("appendix tables ok")
