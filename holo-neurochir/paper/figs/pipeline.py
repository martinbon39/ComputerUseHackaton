"""Figure 2: the pipeline, with the status of each stage at the time of writing.

Counts are read from data/local/diagnostic_osw_diag.json, data/pod_astra/osw_shared_STATUS.json
and data/pod_astra/confirm_tasks.json.
Stage status is categorical: done / reached with a negative result / not reached.
"""
from common import FIGS, C, load, setup_mpl

d = load("local/diagnostic_osw_diag.json")
st = load("pod_astra/osw_shared_STATUS.json")
conf = load("pod_astra/confirm_tasks.json")
og = load("local/online/ONLINE_GUARD_RESULT.json")["primary_vs_modal"]
rb = load("local/rescue_bench/RESULT.json")["primary"]["paired_difference"]
GATE = 40  # data/pod_astra/4b/PROTOCOL.md: official analysis needs >= 40 admissible fs+
n_tasks = d["n_tasks"]
adm = st["admissible_total"]

stages = [
    ("1  Rollouts", f"vLLM serves Holo-3.1-4B\n{n_tasks} frozen diag tasks, T=0.8", "done"),
    ("2  Real desktops", "OSWorld VMs (Docker+KVM)\nexecution-based checker", "done"),
    ("3  Taxonomy", "hashed rules: false success,\nstep limit, loop; step labels", "done"),
    ("4  Exact replay", "rebuild every input, prefill\nin transformers, hook layers", "done"),
    ("5  Direction", f"diff-of-means, {adm['fs+']} fs+ vs {adm['fs-']} fs−\nno gain over position", "negative"),
    ("6  Steering", "free generation, k=4,\npre-registered gate", "negative"),
    ("7  Weight edit", "compile into writers\nW ← (I − αuuᵀ)W", "blocked"),
    ("8  Paired validation", f"{conf['n']} reserve + test tasks, run on\nnon-admitted arms: no gain", "negative"),
    ("9  External verifier", f"false done {og['false_done_diff'] * 100:+.1f} pts online\n({og['n_tasks']} TEST tasks);".replace("-", "\u2212") + f"\nwith Holo4: {rb["mean"] * 100:+.0f} pts repaired (replay)", "positive"),
]
style = {"done": ("#E6F2EC", C["green"], "-"), "partial": ("#FFF4DC", C["orange"], "-"), "positive": ("#E3EEF8", C["blue"], "-"),
         "negative": ("#FBE5DC", C["red"], "-"), "blocked": ("#F4F4F4", "#9A9A9A", "--")}
legend = {"done": "done", "negative": "run: negative, or no selective effect",
          "blocked": "ready, not reached", "positive": "run: positive, false done lowered"}

plt = setup_mpl()
from matplotlib.patches import FancyBboxPatch

W, H = 7.0, 2.75
fig = plt.figure(figsize=(W, H))
ax = fig.add_axes([0, 0, 1, 1])
ax.set_xlim(0, W), ax.set_ylim(0, H), ax.axis("off")
bw, bh, gx = 2.1, 0.62, 0.24
rows = [(H - 0.12 - (r + 1) * bh - r * 0.3, stages[3 * r:3 * r + 3]) for r in range(3)]
centers = []
for r, (y, row) in enumerate(rows):
    for i, (title, body, status) in enumerate(row):
        x = 0.06 + i * (bw + gx)
        fc, ec, ls = style[status]
        ax.add_patch(FancyBboxPatch((x, y), bw, bh, boxstyle="round,pad=0,rounding_size=0.06", fc=fc, ec=ec, lw=1.0, ls=ls))
        ax.text(x + 0.08, y + bh - 0.07, title, fontsize=7.4, fontweight="bold", va="top", color="#222222")
        ax.text(x + 0.08, y + bh - 0.27, body, fontsize=6.2, va="top", color="#333333", linespacing=1.15)
        centers.append((x, y))
for k in range(len(centers) - 1):
    (x1, y1), (x2, y2) = centers[k], centers[k + 1]
    if y1 == y2:
        ax.annotate("", xy=(x2, y2 + bh / 2), xytext=(x1 + bw, y1 + bh / 2),
                    arrowprops=dict(arrowstyle="-|>", color="#555555", lw=1.0))
    else:
        ax.annotate("", xy=(x2 + bw / 2, y2 + bh), xytext=(x1 + bw / 2, y1),
                    arrowprops=dict(arrowstyle="-|>", color="#555555", lw=1.0,
                                    connectionstyle="arc,angleA=-90,angleB=90,armA=12,armB=12,rad=6"))
for lx, (k, lab) in zip([0.06, 0.8, 3.0, 4.6], legend.items()):
    fc, ec, ls = style[k]
    ax.add_patch(FancyBboxPatch((lx, 0.03), 0.16, 0.1, boxstyle="round,pad=0,rounding_size=0.02", fc=fc, ec=ec, lw=0.8, ls=ls))
    ax.text(lx + 0.22, 0.08, lab, fontsize=6.3, va="center", color="#333333")
fig.savefig(FIGS / "pipeline.pdf")
print("pipeline ok")
