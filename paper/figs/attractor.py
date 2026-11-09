"""The answer decision as an attractor: weight edits that change the text but not the decision.

Sources (verbatim copies of holo-neurochir/report/agent_reports/, synced from the pod):
  data/pod_astra/free/external/<arm>/summary.json        tool counts per context, vLLM 0.23 on Modal, seeds 4000-4007
  data/pod_astra/free/external_pairwise_token_check.json token identity of each output with the paired original
  data/pod_astra/free/REPORT.md                          edit definitions, H3 full degeneration
  data/pod_astra/mit2/REPORT.md                          two-neuron conditional circuits, input-injection diagnostics
  data/pod_astra/ratio/REPORT.md                         narrow MLP edit after the MIT recipe, alpha=1
"""
import re
from collections import Counter

from common import FIGS, C, DATA, Macros, load, setup_mpl, write_table

m = Macros("attractor")
S = "data/pod_astra/free/"
ARMS = [("orig_modal", "Original (re-served)", None),
        ("free_h2", "DeltaNet gates $\\to$ Qwen (H2, 48 matrices)", "Htwo"),
        ("free_h3_l05", "MLPs halfway to Qwen (H3, 96 matrices)", "Hthreehalf"),
        ("free_h5_l05", "\\texttt{</think>} input row $\\to$ newline (H5, $\\lambda=0.5$)", "Hfivehalf"),
        ("free_h6_s05", "Full-attention temperature $\\times 0.5$ (H6, 8 vectors)$^{\\dagger}$", "Hsix"),
        ("free_h2_l2", "DeltaNet gates, $\\lambda=2$ (H2, 48 matrices)", "Htwotwo"),
        ("free_h9_a020", "Language layers 20\\% toward Qwen (H9, 401 tensors)", "Hnine"),
        ("free_h10_half", "RoPE share of the query gain $\\times 0.5$ (H10, 8 vectors)", "Htenhalf"),
        ("free_h10_zero", "RoPE share of the query gain $= 0$ (H10)$^{\\dagger}$", "Htenzero"),
        ("free_h3_l1", "MLPs $=$ Qwen (H3, $\\lambda=1$)", "Hthreefull")]
AUDITS = ["audit_external_all4.aggregate.json", "audit_external_h6_pair.aggregate.json",
          "audit_external_h2_l2_pair.aggregate.json", "audit_external_h9_pair.aggregate.json",
          "audit_external_h10_half_pair.aggregate.json", "audit_external_h10_zero_pair.aggregate.json"]
audit = {}
for f in AUDITS:
    for r in load("pod_astra/free/" + f)["counts"]:
        if r["group"] == "fs+" and (r["arm"] != "orig_modal" or r["arm"] not in audit):
            audit[r["arm"]] = (r["false_completion_claim"], r["clean_gui_useful"], r["n"], f)
ADJ = "audit_external_h6_pair.fs_text.adjudicated.verdict.json"
akey = load("pod_astra/free/audit_external_h6_pair.key.json")
adj = [x for x in load("pod_astra/free/" + ADJ)["samples"] if x["kind"] == "gui" and akey[x["id"]][0] == "free_h6_s05"]
audit["free_h6_s05"] = (sum(x["false_completion_claim"] for x in adj), sum(x["gui_useful"] for x in adj), len(adj), ADJ + " (+ key.json)")
m.add("attHsixTheme", sum(x["tool"] != "answer" and not x["false_completion_claim"] for x in adj),
      S + ADJ + " H6 fs+ non-answer outputs adjudicated as not claiming completion")
HZ = "audit_external_h10_zero_pair.fs_text.verdict.json"
hz = [x for x in load("pod_astra/free/" + HZ)["samples"] if x["kind"] == "gui" and "480bcfea" in x["context_id"] and x["tool"] != "answer"]
assert all(not x["false_completion_claim"] and not x["gui_useful"] and not x["epistemic_correct_no_gui_progress"] for x in hz)
m.add("attHtenzeroInfClick", sum(x["tool"] == "click" for x in hz), S + HZ + " infeasible fs+ context, click outputs (none useful, none honest)")
m.add("attHtenzeroInfWait", sum(x["tool"] == "wait" for x in hz), S + HZ + " infeasible fs+ context, wait outputs")
m.add("attHtenzeroHealthyLoss", f"{load('pod_astra/free/H10_ZERO_EARLY_REJECTION.json')['minimum_healthy_loss_percentage_points']:.1f}",
      S + "H10_ZERO_EARLY_REJECTION.json minimum_healthy_loss_percentage_points (gate: 10)")
m.add("attHtenzeroHealthyTrunc", load("pod_astra/free/H10_ZERO_EARLY_REJECTION.json")["healthy_unusable_from_raw_metadata"],
      S + "H10_ZERO_EARLY_REJECTION.json healthy_unusable_from_raw_metadata (truncated)")
pair = load("pod_astra/free/external_pairwise_token_check.json")["records"]
ident = {}
for r in pair:
    c = ident.setdefault(r["arm"], Counter())
    c["n"] += r["n"]
    c["full"] += r["full_ids_identical"]
    c["reason"] += r["reasoning_ids_identical"]
    if r["group"] != "text":
        c["gui_n"] += r["n"]
        c["gui_reason"] += r["reasoning_ids_identical"]
for _arm, _key in (("free_h2", "Htwo"), ("free_h3_l05", "Hthreehalf"), ("free_h5_l05", "Hfivehalf")):
    _c = ident[_arm]
    m.add(f"att{_key}GuiReason", f"{_c['gui_reason']}/{_c['gui_n']}", S + f"external_pairwise_token_check.json {_arm} reasoning_ids_identical over fs+, fs-, healthy")
_c = ident["free_h5_l05"]
m.add("attHfivehalfGuiDiffer", _c["gui_n"] - _c["gui_reason"], S + "external_pairwise_token_check.json free_h5_l05 GUI outputs whose reasoning differs")


def counts(arm):
    c = {g: Counter() for g in ("fs+", "fs-", "healthy")}
    for k, v in load(f"pod_astra/free/external/{arm}/summary.json")["per_row"].items():
        c[k.split(" | ")[1]].update(v)
    return c


rows = []
for arm, lab, key in ARMS:
    c = counts(arm)
    inv = sum(c[g]["invalid"] for g in c)
    n = sum(c[g]["n"] for g in c)
    fp, fm, h = c["fs+"], c["fs-"], c["healthy"]
    if arm in ident:
        t = ident[arm]
        tok = f"{t['full']}/{t['n']} & {t['reason']}/{t['n']}"
        m.add(f"att{key}Full", f"{t['full']}/{t['n']}", S + f"external_pairwise_token_check.json {arm} sum full_ids_identical")
        m.add(f"att{key}Reason", f"{t['reason']}/{t['n']}", S + f"external_pairwise_token_check.json {arm} sum reasoning_ids_identical")
    else:
        tok = "-- & --"
    if arm in audit:
        fc, us, na, fa = audit[arm]
        sem = f"{fc}/{na} & {us}/{na}"
        m.add(f"att{key or 'Orig'}AuditFalse", f"{fc}/{na}", S + f"{fa} counts[{arm}, fs+].false_completion_claim")
        m.add(f"att{key or 'Orig'}AuditUseful", f"{us}/{na}", S + f"{fa} counts[{arm}, fs+].clean_gui_useful")
    else:
        sem = "-- & --"
    rows.append(f"{lab} & {fp['answer']}/{fp['n']} & {fm['answer']}/{fm['n']} & {h['valid_nonanswer']}/{h['n']} & {inv}/{n} & {sem} & {tok} \\\\ % source: {S}external/{arm}/summary.json")
    tag = key or "Orig"
    m.add(f"att{tag}Fsp", f"{fp['answer']}/{fp['n']}", S + f"external/{arm}/summary.json fs+ answer")
    m.add(f"att{tag}Fsm", f"{fm['answer']}/{fm['n']}", S + f"external/{arm}/summary.json fs- answer")
    m.add(f"att{tag}Inv", f"{inv}/{n}", S + f"external/{arm}/summary.json invalid over GUI outputs")
write_table("attractor", "\\begin{tabular}{lcccccccc}\n\\toprule\n"
            "& \\multicolumn{4}{c}{tool calls} & \\multicolumn{2}{c}{blind audit, fs+} & \\multicolumn{2}{c}{identical to original} \\\\\n"
            "\\cmidrule(lr){2-5}\\cmidrule(lr){6-7}\\cmidrule(lr){8-9}\n"
            "Weight edit & fs+ \\texttt{answer} & fs$-$ \\texttt{answer} & healthy valid & invalid & false claim & useful & tokens & reasoning \\\\\n\\midrule\n"
            + rows[0] + "\n\\midrule\n" + "\n".join(rows[1:]) + "\n\\bottomrule\n\\end{tabular}\n", "attractor")

rep = (DATA / "pod_astra/free/REPORT.md").read_text()
mm = re.search(r"token(\d+) occurring(\d+) times \(([0-9.]+)%\)", rep)
m.add("attHthreeRepeatPct", f"{float(mm.group(3)):.1f}", S + "REPORT.md H3full pilot: share of the 3072 output tokens that are one repeated token")


def thousands(s):
    return f"{int(re.sub(r'\D', '', s)):,}".replace(",", "{,}")

m2 = (DATA / "pod_astra/mit2/REPORT.md").read_text()
tab = re.findall(r"^\| *(\d+) \| (\S+) \| ([^|]+) \| (\d+) \| (\d+)/(\d+) \|", m2, re.M)
w = [t for t in tab if t[2].strip() == "poids édités"]
inj = [t for t in tab if t[2].strip() == "entrée modifiée"]
m.add("mitTwoArms", len(w), "data/pod_astra/mit2/REPORT.md results table, rows 'poids édités'")
m.add("mitTwoFsp", f"{sum(int(t[4]) for t in w)}/{sum(int(t[5]) for t in w)}", "data/pod_astra/mit2/REPORT.md results table, weight arms fs+ false answers")
m.add("mitTwoInj", " and ".join(f"{t[4]}/{t[5]}" for t in inj), "data/pod_astra/mit2/REPORT.md results table, rows 'entrée modifiée' with outputs")
m.add("mitTwoWeights", thousands(re.search(r"Chaque spec cible ([0-9\u202f ]+) poids", m2).group(1)),
      "data/pod_astra/mit2/REPORT.md 'Chaque spec cible ... poids'")

SR = "data/pod_astra/ratio/semantic_summary.json"
ra = load("pod_astra/ratio/semantic_summary.json")["arms"]
m.add("ratioFsp", f"{ra['v_a1']['fs+']['premature_answer']}/{ra['v_a1']['fs+']['observed']}", SR + " v_a1 fs+ premature_answer")
m.add("ratioUseful", f"{ra['v_a1']['fs+']['useful']}/{ra['v_a1']['fs+']['observed']}", SR + " v_a1 fs+ useful")
m.add("ratioTrue", f"{ra['v_a1']['fs-']['true_finish_preserved']}/{ra['v_a1']['fs-']['observed']}", SR + " v_a1 fs- true_finish_preserved")
m.add("ratioTrueBase", f"{ra['v_baseline_retry']['fs-']['true_finish_preserved']}/{ra['v_baseline_retry']['fs-']['observed']}", SR + " v_baseline_retry fs-")
r = (DATA / "pod_astra/ratio/REPORT.md").read_text()
m.add("ratioWeights", thousands(re.search(r"Deux matrices, ([0-9\u202f ]+) coefficients visés", r).group(1)),
      "data/pod_astra/ratio/REPORT.md 'Construction figée': coefficients targeted")
m.write()

plt = setup_mpl()
fig, ax = plt.subplots(figsize=(7.0, 2.0))
names = [("free_h2", "DeltaNet gates → Qwen"), ("free_h3_l05", "MLPs halfway to Qwen"), ("free_h5_l05", "</think> input row edit")]
bars = [("fs+ outputs that answer (original: 100%)", C["red"], lambda a: counts(a)["fs+"]["answer"] / counts(a)["fs+"]["n"]),
        ("same reasoning tokens", C["sky"], lambda a: ident[a]["reason"] / ident[a]["n"]),
        ("same output tokens", C["blue"], lambda a: ident[a]["full"] / ident[a]["n"])]
hgt = 0.26
for i, (arm, nm) in enumerate(names):
    for j, (lab, col, f) in enumerate(bars):
        v = f(arm)
        y = i + (j - 1) * hgt
        ax.barh(y, v, height=hgt * 0.92, color=col, label=lab if i == 0 else None)
        ax.text(v + 0.01, y, f"{v:.0%}", va="center", fontsize=6.2)
ax.set_yticks(range(len(names)), [n for _, n in names], fontsize=6.8)
ax.invert_yaxis()
ax.set_xlim(0, 1.12), ax.set_xticks([0, 0.5, 1], ["0", "50%", "100%"])
ax.legend(frameon=False, fontsize=6.2, loc="upper center", bbox_to_anchor=(0.45, -0.2), ncol=3)
ax.set_title("The tool call does not change (paired seeds, vs. the re-served original)", fontsize=7.6)
fig.savefig(FIGS / "attractor.pdf")
print("attractor ok", {a: dict(v) for a, v in ident.items()})
