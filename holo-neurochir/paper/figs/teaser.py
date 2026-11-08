"""Figure 1 (teaser): one real false-success episode, the failure taxonomy, and where the success claim appears.

Sources:
  data/local/spotify/{traj.jsonl,meta.json,result.txt,task.json,step_*.png}  pilot episode os/94d95f96 (outside both splits)
  data/local/diagnostic_osw_diag.json                                        failure taxonomy, diagnostic split pass 1
  data/pod_astra/think/direction_summary.json                                regenerated reflections, first success claim
"""
import json
import textwrap
from collections import Counter

import numpy as np
from PIL import Image

from common import DATA, FIGS, C, Macros, load, setup_mpl, pct, tex_escape as tx

m = Macros("teaser")
SP = DATA / "local/spotify"
traj = [json.loads(l) for l in (SP / "traj.jsonl").read_text().splitlines() if l.strip()]
meta = json.loads((SP / "meta.json").read_text())
task = json.loads((SP / "task.json").read_text())
score = float((SP / "result.txt").read_text().strip())
step = {int(s["step_num"]): s for s in traj}
last = max(step)
ans = step[last]["tool_call"]
ans = ans if isinstance(ans, dict) else eval(ans)  # recorded as a Python-literal dict
assert ans["tool_name"] == "answer" and score == 0.0
quote_know = "I cannot complete the installation without the password."
assert quote_know in step[last]["reasoning"], "quoted reasoning must exist verbatim"
claim = ans["content"].split(". ")[0] + "."
assert claim in ans["content"]
ev = task["evaluator"]
S = "data/local/spotify/"
m.add("spInstruction", tx(task["instruction"]), S + "task.json instruction")
m.add("spSteps", last, S + "traj.jsonl max step_num")
m.add("spScore", f"{score:.0f}", S + "result.txt")
m.add("spClaim", tx(claim), S + "traj.jsonl last step tool_call.content (first sentence)")
m.add("spKnow", tx(quote_know), S + "traj.jsonl last step reasoning (verbatim substring)")
m.add("spCheck", ev["result"]["command"], S + "task.json evaluator.result.command")

# Failure taxonomy (diagnostic split, pass 1).
d = load("local/diagnostic_osw_diag.json")
cat = Counter(d["categories"])
n_fail = d["n_fail"]
removable = cat["false_success"] + cat["step_limit"] + cat["loop"]

# Regenerated reflections: token index of the first success claim.
ds = load("pod_astra/think/direction_summary.json")
evs = [e for e in ds["events"] if e["event"]]
tok = {"fs+": [e["event"]["token_index"] for e in evs if e["label"] == "fs+"],
       "fs-": [e["event"]["token_index"] for e in evs if e["label"] == "fs-"]}
n_verif = sum(len(e["event"]["verification_window"]) > 0 for e in evs)
T = "data/pod_astra/think/direction_summary.json"
m.add("thN", len(evs), T + " events with a conclusion event")
m.add("thNAll", len(ds["events"]), T + " len(events)")
m.add("thNTasks", ds["n_train_tasks"], T + " n_train_tasks")
m.add("thTokMin", min(min(v) for v in tok.values()), T + " min token_index (0-based generated-token index)")
m.add("thTokMax", max(max(v) for v in tok.values()), T + " max token_index (0-based generated-token index)")
m.add("thNVerif", n_verif, T + " events with non-empty verification_window before the claim")
m.add("thMedLen", int(np.median([e["event"]["n_reflection_tokens"] for e in evs])), T + " median n_reflection_tokens")
m.add("thFsPosAnswer", sum(e["answer"] for e in ds["events"] if e["label"] == "fs+"), T + " fs+ events with answer=True")
m.add("thFsPosN", sum(1 for e in ds["events"] if e["label"] == "fs+"), T + " fs+ events")
m.add("thFsNegAnswer", sum(e["answer"] for e in ds["events"] if e["label"] == "fs-"), T + " fs- events with answer=True")
m.add("thFsNegN", sum(1 for e in ds["events"] if e["label"] == "fs-"), T + " fs- events")
m.write()

# ---------------------------------------------------------------- figure
plt = setup_mpl()
from matplotlib.patches import FancyBboxPatch, Rectangle

W, H = 7.0, 3.34
fig = plt.figure(figsize=(W, H))


def ax_in(x, y, w, h, **kw):
    return fig.add_axes([x / W, y / H, w / W, h / H], **kw)


def label(x, y, s):
    fig.text(x / W, y / H, s, fontsize=11, fontweight="bold", va="top")


label(0.0, H - 0.02, "a")
fig.text(0.2 / W, (H - 0.05) / H, f"A real false success (OSWorld os/94d95f96, {last} steps).  "
         f"Task: “{task['instruction']}”", fontsize=7.4, va="top")

# (step, caption, crop box as fractions (x0, y0, x1, y1) of the screen)
shots = [(1, "Step 1: click “Activities”", (0, 0, 1, 1)),
         (8, "Step 8: open the Spotify entry", (0, 0, 1, 1)),
         (10, "Step 10: password dialog (zoom)", (0.3, 0.27, 0.7, 0.73)),
         (last, f"Step {last}: unchanged → answer (zoom)", (0.3, 0.27, 0.7, 0.73))]
sw, gap, x0 = 1.70, 0.067, 0.0
sh = sw * 9 / 16
ytop = H - 0.42
for i, (s, lab, (cx0, cy0, cx1, cy1)) in enumerate(shots):
    x = x0 + i * (sw + gap)
    ax = ax_in(x, ytop - sh, sw, sh)
    im = Image.open(SP / f"step_{s}.png").convert("RGB")
    Wf, Hf = im.size
    im = im.crop((int(cx0 * Wf), int(cy0 * Hf), int(cx1 * Wf), int(cy1 * Hf)))
    im.thumbnail((900, 506))
    ax.imshow(np.asarray(im), aspect="auto")
    ax.set_xticks([]), ax.set_yticks([])
    col = C["red"] if s == last else "#888888"
    for sp_ in ax.spines.values():
        sp_.set_visible(True), sp_.set_color(col), sp_.set_linewidth(1.6 if s == last else 0.6)
    tc = step[s]["tool_call"]
    tc = tc if isinstance(tc, dict) else eval(tc)
    if "x" in tc and s != last:
        px = (tc["x"] / 1000 - cx0) / (cx1 - cx0) * im.width
        py = (tc["y"] / 1000 - cy0) / (cy1 - cy0) * im.height
        ax.plot(px, py, "o", ms=10, mfc="none", mec=C["orange"], mew=1.8)
    ax.set_title(lab, fontsize=6.8, fontweight="bold" if s == last else "normal", loc="left", pad=2,
                 color=col if s == last else "#222222")

# Reasoning -> action -> checker strip.
by, bh = ytop - sh - 0.62, 0.50
boxes = [(0.0, 2.15, "What it reasons at the last step", f"“… {quote_know} …”", "#F1F1F1", "#222222", "italic"),
         (2.40, 2.45, "What it then does", "answer(“" + claim + "”)", "#FBE5DC", C["red"], "normal"),
         (5.10, 1.90, "What the checker sees", f"{ev['result']['command']}  →  not found\nscore = {score:.0f}",
          "#F1F1F1", "#222222", "normal")]
axb = ax_in(0, by, W, bh)
axb.axis("off")
axb.set_xlim(0, W), axb.set_ylim(0, bh)
for xx, ww, head, body, fc, tcol, sty in boxes:
    axb.add_patch(FancyBboxPatch((xx, 0.0), ww, bh, boxstyle="round,pad=0,rounding_size=0.06", fc=fc, ec="none"))
    axb.text(xx + 0.08, bh - 0.07, head, fontsize=6.6, fontweight="bold", va="top", color="#555555")
    wrapped = body if "\n" in body else "\n".join(textwrap.wrap(body, int(ww * 19.5)))
    axb.text(xx + 0.08, bh - 0.21, wrapped, fontsize=7.0, va="top", color=tcol, style=sty, linespacing=1.15)
for xa in (2.17, 4.87):
    axb.annotate("", xy=(xa + 0.21, bh / 2), xytext=(xa + 0.02, bh / 2),
                 arrowprops=dict(arrowstyle="-|>", color="#555555", lw=1.1))

# (b) failure composition.
yb = by - 0.12
label(0.0, yb, "b")
axf = ax_in(0.25, 0.40, 3.05, 0.40)
order = [("false_success", "False success", C["red"]), ("step_limit", "Step limit", C["orange"]),
         ("loop", "Loop", C["purple"]), ("other", "Other", C["grey"])]
left = 0
for k, lab, col in order:
    v = cat.get(k, 0)
    axf.barh([0], [v], left=left, color=col, edgecolor="white", height=0.8)
    if v >= 5:
        axf.text(left + v / 2, 0, f"{lab}\n{v}", ha="center", va="center", color="white", fontsize=6.8,
                 fontweight="bold", linespacing=1.0)
    left += v
axf.set_xlim(0, n_fail), axf.set_ylim(-0.45, 0.45)
axf.set_yticks([]), axf.set_xticks([0, n_fail], ["0", f"{n_fail} failed tasks"])
axf.spines["left"].set_visible(False)
axf.tick_params(axis="x", labelsize=6.5, length=2)
axf.set_title(f"{pct(removable / n_fail, 0)}% of failures are a false “done”, the step limit or a loop\n"
              f"(diagnostic split: {d['n_tasks']} tasks, {n_fail} failures; {cat.get('other', 0)} other)",
              fontsize=7.0, loc="left", pad=3)

# (c) original model: P(answer) by stratum, free generation (data/pod_astra/4b/runtime_status.json).
from common import wilson
st = load("pod_astra/4b/runtime_status.json")["strata"]
label(3.65, yb, "c")
axt = ax_in(4.75, 0.36, 2.15, 0.56)
strata = [("fs+", "false “done”", C["red"]), ("fs-", "true “done”", C["green"]),
          ("healthy", "mid-episode", C["grey"])]
for j, (k, lab, col) in enumerate(strata):
    a_, n_ = st[k]["answer"], st[k]["n"]
    lo, hi = wilson(a_, n_)
    axt.barh(j, a_ / n_, color=col, height=0.6)
    axt.plot([lo, hi], [j, j], color="#222222", lw=1)
    axt.text(1.03, j, f"{a_}/{n_}", va="center", fontsize=6.5)
axt.set_yticks(range(3), [s_[1] for s_ in strata], fontsize=6.5)
axt.invert_yaxis()
axt.set_xlim(0, 1), axt.set_xticks([0, 0.5, 1], ["0", "50%", "100%"])
axt.tick_params(axis="x", labelsize=6.5)
axt.set_xlabel("re-sampled steps that call answer (95% CI)", fontsize=6.4, labelpad=1)
fig.text(3.95 / W, (yb - 0.02) / H, "Re-sampled from the same contexts, the model\nanswers “done” on false and true completions alike",
         fontsize=7.0, fontweight="bold", va="top")
fig.savefig(FIGS / "teaser.pdf")
print("teaser ok", len(evs), n_verif, dict(cat))
