"""Every causal test on Holo-3.1-4B (free generation), and the causal map of the tool choice.

Sources (verbatim copies of pod /workspace/astra/*):
  data/pod_astra/4b/pilot_original_generation_resume.done.json, runtime_status.json   original reference (k=4)
  data/pod_astra/4b/pilot_c1_add_l16_{metrics,job}.json                              residual addition L16 (complete)
  data/pod_astra/4b/pilot_c1_add_l24{.jsonl,_job.json}                               residual addition L24 (in progress)
  data/pod_astra/think/{metrics_active,screen_add_half_job}.json                     addition during reasoning, L31
  data/pod_astra/value/r1_*_L24_a05_prefill.comparison.json, r1_value_L18_a05_prefill.jsonl
  data/pod_astra/value/{BASELINE,LOT1}_VERIFICATION_ANNOTATIONS.json                 verbalised re-evaluation
  data/pod_astra/neurons/final_outcome.json                                          MLP neuron ablations
  data/pod_astra/circuit/{lot04..07_residual,lot13_joint,lot15_behavior}.jsonl, summary.json
  data/pod_astra/stuck/CAMPAIGN_STATUS.json                                          second target (stuck)
"""
import ast
import json
from collections import Counter, defaultdict

import numpy as np

import re

from common import DATA, FIGS, C, Macros, load, setup_mpl, write_table, wilson

m = Macros("causal")
PA = "data/pod_astra/"


def jsonl(rel):
    return [json.loads(l) for l in (DATA / rel).read_text().splitlines() if l.strip()]


def counts_from_jsonl(rel):
    """Generated-output counts per stratum from a raw output file (complete or in progress)."""
    out = defaultdict(Counter)
    for r in jsonl(rel):
        if "tool" not in r or "row" not in r:
            continue
        row = r["row"] if isinstance(r["row"], dict) else ast.literal_eval(r["row"])
        lab = row["label"]
        out[lab]["n"] += 1
        out[lab]["answer"] += bool(r["answer"])
        out[lab]["valid"] += bool(r["valid_nonanswer"])
        out[lab]["invalid"] += bool(r.get("error")) or bool(r.get("truncated"))
    return out


def counts_from_metrics(d):
    out = {}
    for lab in ("fs+", "fs-", "healthy"):
        s = d["strata"][lab]
        out[lab] = {"n": s["n"], "answer": s["candidate"]["answer"]["count"],
                    "valid": s["candidate"]["valid_nonanswer"]["count"], "invalid": s["candidate"]["invalid"]["count"]}
    return out


orig = load("pod_astra/4b/runtime_status.json")["strata"]
ORIG = {k: {"n": v["n"], "answer": v["answer"], "valid": v["valid_nonanswer"], "invalid": v["invalid_or_truncated"]}
        for k, v in orig.items()}
PLANNED = sum(v["n"] for v in ORIG.values())

arms = []  # (who, intervention, where, counts, status, source)
j16 = load("pod_astra/4b/pilot_c1_add_l16_job.json")["intervention"]
arms.append(("4b-x", "residual addition, matched fs direction", f"L{j16['layers'][0]}, last prefill, $\\alpha={j16['alpha']:.2f}$",
             counts_from_metrics(load("pod_astra/4b/pilot_c1_add_l16_metrics.json")), "rejected", PA + "4b/pilot_c1_add_l16_metrics.json"))
j24 = load("pod_astra/4b/pilot_c1_add_l24_job.json")["intervention"]
arms.append(("4b-x", "residual addition, matched fs direction", f"L{j24['layers'][0]}, last prefill, $\\alpha={j24['alpha']:.2f}$",
             counts_from_metrics(load("pod_astra/4b/pilot_c1_add_l24_metrics.json")), "rejected", PA + "4b/pilot_c1_add_l24_metrics.json"))
jt = load("pod_astra/think/screen_add_half_job.json")["intervention"]
arms.append(("think", "addition of the ``conclusion'' direction", f"L{jt['layers'][0]}, every reasoning token, $\\alpha={jt['alpha']}$",
             counts_from_metrics(load("pod_astra/think/metrics_active.json")["screen_add_half"]), "rejected",
             PA + "think/metrics_active.json"))
for ax_, f in [("value", "r1_value_L24_a05_prefill"), ("commitment", "r1_commitment_L24_a05_prefill")]:
    arms.append(("value", f"push toward low {'value' if ax_ == 'value' else 'commitment'} (Value Axis)",
                 "L24, last prefill, $\\alpha=0.5$", counts_from_metrics(load(f"pod_astra/value/{f}.comparison.json")), "rejected",
                 PA + f"value/{f}.comparison.json"))
for ax_, f in [("value", "r1_value_L18_a05_prefill"), ("commitment", "r1_commitment_L18_a05_prefill")]:
    arms.append(("value", f"push toward low {ax_} (Value Axis)", "L18, last prefill, $\\alpha=0.5$",
                 counts_from_metrics(load(f"pod_astra/value/{f}.comparison.json")), "rejected", PA + f"value/{f}.comparison.json"))
no = load("pod_astra/neurons/final_outcome.json")
for c in no["candidate_results"]:
    a, n = (int(x) for x in c["observed_answer"].split("/"))
    arms.append(("neurons", f"zero the top-{c['top_k']} MLP neurons writing \\texttt{{answer}}", "L20--31, whole generation",
                 {"fs+": {"n": n, "answer": a, "valid": 0, "invalid": 0}}, "rejected (bound)", PA + "neurons/final_outcome.json"))
for e in load("pod_astra/circuit/behavior_summary.json")["experiments"]:
    sp = e["spec"]
    c = {k: {"n": v["n"], "answer": v["answer"], "valid": v["valid_nonanswer"], "invalid": v["invalid_or_truncated"]}
         for k, v in e["metrics"].items()}
    what = ("random control: same-norm Gaussian direction removed" if sp["random"] else "scale C1 (3 heads + 10 neurons) by $1-\\alpha$")
    arms.append(("circuit", what, f"L19/23/31 heads, L30--31 neurons, $\\alpha={sp['alpha']}$", c,
                 ("control" if sp["random"] else "rejected") if e["complete"] else "running", PA + "circuit/behavior_summary.json " + sp["name"]))


# Perturbation size relative to the mean residual norm at the intervention layer.
norms = load("pod_astra/perceive/metadata.json")["norms"]["mean_residual_norm_by_layer"]
R31 = float(re.search(r"R31=([0-9.]+)", (DATA / "pod_astra/think/AMENDMENT_RESIDUAL_DOSE.md").read_text()).group(1))
think_dose = abs(jt["alpha"]) * jt["scales"]["31"] / R31
doses = [abs(j16["alpha"]) / norms[j16["layers"][0]], abs(j24["alpha"]) / norms[j24["layers"][0]], think_dose,
         0.5, 0.5, 0.5, 0.5, None, None, None, None, None]
assert len(doses) == len(arms)  # extended below for perceive/verify
S = "data/pod_astra/perceive/metadata.json norms.mean_residual_norm_by_layer"
m.add("doseSixteen", f"{doses[0]:.2f}", PA + "4b/pilot_c1_add_l16_job.json |alpha| / " + S + "[16]")
m.add("doseTwentyFour", f"{doses[1]:.2f}", PA + "4b/pilot_c1_add_l24_job.json |alpha| / " + S + "[24]")
m.add("doseThink", f"{think_dose:.2f}", PA + "think/screen_add_half_job.json |alpha|*scales.31 / R31 (think/AMENDMENT_RESIDUAL_DOSE.md)")
m.add("thinkRThirtyOne", f"{R31:.1f}", PA + "think/AMENDMENT_RESIDUAL_DOSE.md R31")
m.add("thinkScale", f"{jt['scales']['31']:.1f}", PA + "think/screen_add_half_job.json intervention.scales.31")
m.add("normSixteen", f"{norms[16]:.1f}", S + "[16]")
m.add("normTwentyFour", f"{norms[24]:.1f}", S + "[24]")
cal = load("pod_astra/circuit/summary.json")["calibration"]
for lab, key in [("fs+", "Pos"), ("fs-", "Neg")]:
    mg = [c["margin"] for c in cal if c["label"] == lab]
    m.add(f"marg{key}Min", f"{min(mg):.1f}", PA + f"circuit/summary.json calibration[{lab}].margin min")
    m.add(f"marg{key}Max", f"{max(mg):.1f}", PA + f"circuit/summary.json calibration[{lab}].margin max")
lo8, _ = wilson(8, 8)
m.add("wilsonEightLo", f"{100 * lo8:.0f}", "Wilson 95% interval of 8/8 (figs/common.py wilson)")
m.add("gateMaxAnswers", 4, "data/pod_astra/4b/PROTOCOL.md section C: -50% relative from 8/8 leaves at most 4/8")


def ci(c, lab):
    s_ = c.get(lab)
    if not s_ or not s_["n"]:
        return "--"
    lo, hi = wilson(s_["answer"], s_["n"])
    return f"[{100 * lo:.0f}, {100 * hi:.0f}]"


# astra-perceive (own reference contexts) and astra-verify, appended after the dose list is fixed.
pm = load("pod_astra/perceive/metadata.json")
pbest = max(pm["cv"]["layer_ranking"], key=lambda r: r["cv_auc"])
for tag, a_ in [("a0p5", 0.5), ("a1", 1), ("a2", 2), ("a4", 4), ("random_a4", 4)]:
    f = f"completion_l15_{tag}" if not tag.startswith("random") else "completion_random_l15_a4"
    st_ = load(f"pod_astra/perceive/{f}.metrics.json")["stats"]
    c = {k: {"n": st_[k]["n"], "answer": round(st_[k]["candidate"] * st_[k]["n"]) if k != "healthy" else 0,
             "valid": round(st_[k]["candidate"] * st_[k]["n"]) if k == "healthy" else 0,
             "invalid": round(st_[k]["invalid_candidate"] * st_[k]["n"])} for k in ("fs+", "fs-", "healthy")}
    rnd = tag.startswith("random")
    arms.append(("perceive", ("random control, same norm" if rnd else "subtract imminent-completion dir."), f"L15, last prefill, $\\alpha={a_}$", c,
                 "control" if rnd else "rejected", PA + f"perceive/{f}.metrics.json"))
    doses.append(a_ * pbest["delta_norm"] / pbest["mean_residual_norm"])
vm = load("pod_astra/verify/metrics.json")["metrics"]
vrej = load("pod_astra/verify/verify_a2.rejected.json")
for arm, d_, ctl in [("verify_a1", 1, False), ("verify_a2", 2, False), ("random_a1", 1, True), ("random_a2", 2, True)]:
    x = vm[arm]
    c = {k: {"n": x[k]["n"], "answer": x[k]["answer"], "valid": x[k]["valid_nonanswer"], "invalid": x[k]["invalid_truncated"]}
         for k in ("fs+", "fs-", "healthy")}
    status = "control" if ctl else ("rejected (bound)" if arm == "verify_a2" else "rejected")
    arms.append(("verify", ("random control, same norm" if ctl else "add a ``verify'' vs.\\ ``conclude'' direction (CAA)"),
                 f"L18, prefill + 20 first tokens, dose {d_}", c, status, PA + f"verify/metrics.json {arm}"))
    doses.append(float(d_))
for f, what, where in [
        ("lot06_vllm_wait2", "raise the ``Wait'' output row for completion openings (weight edit)",
         "\\texttt{lm\\_head}, 1 row, 2{,}560 weights"),
        ("lot08_decay080", "shorten memory of late linear-attention layers (weight edit)", "\\texttt{A\\_log}, 9 layers, retention $\\times0.8$"),
        ("lot09_decay125", "lengthen memory of late linear-attention layers (weight edit)", "\\texttt{A\\_log}, 9 layers, retention $\\times1.25$")]:
    cn = load(f"pod_astra/mit1/{f}.summary.json")["counts"]
    c = {k: {"n": v["observed"], "answer": v["answer"], "valid": v["valid_nonanswer"], "invalid": v["invalid"]} for k, v in cn.items()}
    arms.append(("mit1", what, where, c, "rejected", PA + f"mit1/{f}.summary.json"))
    doses.append(None)
w2 = load("pod_astra/mit1/lot06_vllm_wait2.summary.json")
m.add("waitFsp", f"{w2['counts']['fs+']['answer']}/{w2['counts']['fs+']['observed']}", PA + "mit1/lot06_vllm_wait2.summary.json counts.fs+")
m.add("waitFsm", f"{w2['counts']['fs-']['answer']}/{w2['counts']['fs-']['observed']}", PA + "mit1/lot06_vllm_wait2.summary.json counts.fs-")
m.add("waitHealthy", f"{w2['counts']['healthy']['valid_nonanswer']}/{w2['counts']['healthy']['observed']}", PA + "mit1/lot06_vllm_wait2.summary.json counts.healthy")
m.add("waitText", f"{sum(t['identical'] for t in w2['text_controls'])}/{len(w2['text_controls'])}", PA + "mit1/lot06_vllm_wait2.summary.json text_controls identical")
m.add("waitWeights", load("pod_astra/mit1/wait2.json")["n_weights_modified"], PA + "mit1/wait2.json n_weights_modified")
m.add("earlyExitWeights", load("pod_astra/mit1/early_exit4.json")["n_weights_modified"], PA + "mit1/early_exit4.json n_weights_modified")
h4c = load("pod_astra/mit1/semantic_lot14.json")["summary"]["fs_plus"]
m.add("hfourInFalse", f"{h4c['false_completion']}/{h4c['outputs']}", PA + "mit1/semantic_lot14.json summary.fs_plus.false_completion")
rb = load("pod_astra/mit1/review_budget_affordance.json")["actions_reclassified"]
m.add("hfourIntentions", sum(a["task_relevant_intention"] for a in rb), PA + "mit1/review_budget_affordance.json actions_reclassified[].task_relevant_intention")
m.add("hfourIntentLots", len({a["lot"] for a in rb}), PA + "mit1/review_budget_affordance.json distinct lots")
m.add("hfourConfirmed", sum(a["confirmed_actual_useful_gui_action"] for a in rb), PA + "mit1/review_budget_affordance.json confirmed_actual_useful_gui_action")
h4o = load("pod_astra/mit1/semantic_lot19.json")["aggregate"]
h4b = load("pod_astra/mit1/SEMANTIC_AUDIT_LOT15_ADDED_BASELINE.json")["aggregate"]
for key, agg, src in [("Out", h4o, "semantic_lot19.json (sha 44a9011b)"), ("Base", h4b, "SEMANTIC_AUDIT_LOT15_ADDED_BASELINE.json")]:
    fp, fm = agg["fs+"], agg["fs-"]
    m.add(f"hfour{key}Useful", f"{fp['actual_useful_gui_action']}/{fp['n']}", PA + f"mit1/{src} aggregate.fs+.actual_useful_gui_action")
    m.add(f"hfour{key}ErrId", f"{fp['correct_error_identification']}/{fp['n']}", PA + f"mit1/{src} aggregate.fs+.correct_error_identification")
    m.add(f"hfour{key}False", f"{fp['false_completion_claimed']}/{fp['n']}", PA + f"mit1/{src} aggregate.fs+.false_completion_claimed")
    m.add(f"hfour{key}True", f"{fm['correct_completion_answer']}/{fm['n']}", PA + f"mit1/{src} aggregate.fs-.correct_completion_answer")
m.add("verifyLayer", load("pod_astra/verify/direction_summary.json")["selected_layer"], PA + "verify/direction_summary.json selected_layer")
m.add("verifyRejCompleted", vrej["completed"], PA + "verify/verify_a2.rejected.json completed")
m.add("perceiveMaxDose", f"{4 * pbest['delta_norm'] / pbest['mean_residual_norm']:.2f}",
      PA + "perceive/metadata.json 4*delta_norm/mean_residual_norm at the best layer")
m.add("doseMax", f"{max(d for d in doses if d is not None):.0f}", "figs/causal.py max dose over all arms (astra-verify dose)")
perc_fs = []
for tag in ("a0p5", "a1", "a2", "a4"):
    st_ = load(f"pod_astra/perceive/completion_l15_{tag}.metrics.json")["stats"]["fs+"]
    perc_fs.append(f"{round(st_['candidate'] * st_['n'])}")
st_r = load("pod_astra/perceive/completion_random_l15_a4.metrics.json")["stats"]["fs+"]
m.add("perceiveFsSeries", "/".join(perc_fs), PA + "perceive/completion_l15_{a0p5,a1,a2,a4}.metrics.json stats.fs+.candidate*n")
m.add("perceiveFsRandom", round(st_r["candidate"] * st_r["n"]), PA + "perceive/completion_random_l15_a4.metrics.json stats.fs+")
m.add("perceiveFsBase", round(st_r["baseline"] * st_r["n"]), PA + "perceive/completion_random_l15_a4.metrics.json stats.fs+.baseline*n")
sel = load("pod_astra/perceive/attention_selection.json")
m.add("perceiveHeadsTested", len(sel["ranked"]), PA + "perceive/attention_selection.json len(ranked)")
m.add("perceiveHeadsEligible", sum(r["eligible"] for r in sel["ranked"]), PA + "perceive/attention_selection.json eligible heads")


def frac(c, lab, key):
    s = c.get(lab)
    return f"{s[key]}/{s['n']}" if s and s["n"] else "--"


rows = [f"Original (reference) & -- & -- & -- & {frac(ORIG, 'fs+', 'answer')} {ci(ORIG, 'fs+')} & {frac(ORIG, 'fs-', 'answer')} & "
        f"{frac(ORIG, 'healthy', 'valid')} & 0/{PLANNED} & -- \\\\ \\midrule"]
n_rejected = 0
for (who, what, where, c, status, src), dose in zip(arms, doses):
    done = sum(v["n"] for v in c.values())
    inv = sum(v["invalid"] for v in c.values())
    verdict = {"rejected": "\\textcolor{fsred}{rejected}", "rejected (bound)": "\\textcolor{fsred}{rejected (bound)}",
               "running": "\\textit{running} " + f"({done}/{PLANNED})", "control": "control"}[status]
    n_rejected += status.startswith("rejected")
    dz = f"{dose:.2f}" if dose is not None else "--"
    rows.append(f"\\texttt{{{who}}}: {what} & {where} & {dz} & {done} & {frac(c, 'fs+', 'answer')} {ci(c, 'fs+')} & {frac(c, 'fs-', 'answer')} & "
                f"{frac(c, 'healthy', 'valid')} & {inv}/{done} & {verdict} \\\\ % source: {src}")
write_table("causal_all", "\\begin{tabular}{p{4.3cm}p{3.4cm}rrcccc l}\n\\toprule\n"
            "Hypothesis \\& intervention & Where & Dose & Out. & fs+ \\texttt{answer} [95\\% CI] $\\downarrow$ & fs$-$ \\texttt{answer} $=$ & "
            "healthy valid $=$ & invalid & Verdict \\\\\n\\midrule\n" + "\n".join(rows) + "\n\\bottomrule\n\\end{tabular}\n", "causal")
m.add("cNArms", sum(a[4] != "control" for a in arms), "figs/causal.py arms excluding random controls")
m.add("cNRejected", n_rejected, "figs/causal.py arms with a rejected verdict")
m.add("cNRunning", sum(a[4] == "running" for a in arms), "figs/causal.py arms still running")
m.add("cOrigFsAns", frac(ORIG, "fs+", "answer"), PA + "4b/runtime_status.json strata.fs+.answer/n")
m.add("cOrigTrueAns", frac(ORIG, "fs-", "answer"), PA + "4b/runtime_status.json strata.fs-.answer/n")
m.add("cOrigHealthy", frac(ORIG, "healthy", "valid"), PA + "4b/runtime_status.json strata.healthy.valid_nonanswer/n")
m.add("cAlphaSixteen", f"{j16['alpha']:.2f}", PA + "4b/pilot_c1_add_l16_job.json intervention.alpha")
m.add("cAlphaTwentyFour", f"{j24['alpha']:.2f}", PA + "4b/pilot_c1_add_l24_job.json intervention.alpha")
m.add("cNeuronBase", no["baseline"]["fs_plus_answer"], PA + "neurons/final_outcome.json baseline.fs_plus_answer")
m.add("cNeuronObs", no["candidate_results"][0]["observed_answer"], PA + "neurons/final_outcome.json candidate_results[0]")
m.add("cNeuronMax", int(no["candidate_results"][0]["maximum_admissible_final_answers"]),
      PA + "neurons/final_outcome.json candidate_results[0].maximum_admissible_final_answers")

# Verbalised doubt (astra-value annotations, independent reader).
for tag, f in [("Base", "BASELINE"), ("Push", "LOT1")]:
    ann = load(f"pod_astra/value/{f}_VERIFICATION_ANNOTATIONS.json")
    fp = [a for a in ann if a["label"] == "fs+"]
    fm = [a for a in ann if a["label"] == "fs-"]
    S = PA + f"value/{f}_VERIFICATION_ANNOTATIONS.json"
    m.add(f"doubt{tag}FsPos", f"{sum(a['secondary'] for a in fp)}/{len(fp)}", S + " fs+ secondary (re-evaluation intent)")
    m.add(f"doubt{tag}FsNeg", f"{sum(a['secondary'] for a in fm)}/{len(fm)}", S + " fs- secondary")
    m.add(f"doubt{tag}Strict", sum(a["strict"] for a in ann), S + " strict verification actions")

# Second target: stuck (escape), protection bound.
st = load("pod_astra/stuck/CAMPAIGN_STATUS.json")
for r in st["results"]:
    key = "stuck" + {"r1_add_16": "Sixteen", "r1_add_24": "TwentyFour"}[r["name"]]
    m.add(key + "Obs", f"{r['observed']}/{r['planned']}", PA + f"stuck/CAMPAIGN_STATUS.json {r['name']} observed/planned")
    m.add(key + "Best", f"{100 * r['bound']['best_possible_rate']:.1f}", PA + f"stuck/CAMPAIGN_STATUS.json {r['name']} bound.best_possible_rate")
    m.add(key + "Req", f"{100 * r['bound']['required_rate']:.0f}", PA + f"stuck/CAMPAIGN_STATUS.json {r['name']} bound.required_rate")

# ---------------------------------------------------------------- causal map (astra-circuit)
probes = []
for i in (4, 5, 6, 7):
    for r in jsonl(f"pod_astra/circuit/lot{i:02d}_residual.jsonl"):
        if r.get("event") == "probe" and r.get("site") == "resid":
            probes.append(r)
anchors = ["prefill", "think_mid", "think_end", "tool_name"]
nL = 1 + max(r["layer"] for r in probes)
grid = {lab: np.zeros((nL, len(anchors))) for lab in ("fs+", "fs-")}
cnt = {lab: np.zeros((nL, len(anchors))) for lab in ("fs+", "fs-")}
flips = Counter()
for r in probes:
    lab = r["pair"]["label"]
    grid[lab][r["layer"], anchors.index(r["anchor"])] += r["delta_margin"]
    cnt[lab][r["layer"], anchors.index(r["anchor"])] += 1
    flips[lab] += not r["predicted_answer"]
for lab in grid:
    grid[lab] /= np.maximum(cnt[lab], 1)
S = PA + "circuit/lot04..07_residual.jsonl"
m.add("cmProbes", len(probes), S + " resid probe events")
m.add("cmFlipsPos", flips["fs+"], S + " fs+ probes with predicted_answer False")
m.add("cmFlipsNeg", flips["fs-"], S + " fs- probes with predicted_answer False")
m.add("cmMinPos", f"{grid['fs+'][:, 3].min():.1f}", S + " min mean delta_margin, fs+, tool_name")
m.add("cmMinNeg", f"{grid['fs-'][:, 3].min():.1f}", S + " min mean delta_margin, fs-, tool_name")
m.add("cmPrefillPos", f"{grid['fs+'][:, 0].min():.2f}", S + " min mean delta_margin, fs+, prefill")
m.add("cmMidPos", f"{grid['fs+'][:, 1].min():.2f}", S + " min mean delta_margin, fs+, think_mid")

comp = [r for i in (8, 9, 10, 11) for r in jsonl(f"pod_astra/circuit/lot{i:02d}_components.jsonl") if r.get("event") == "probe"]
m.add("cmCompProbes", len(comp), PA + "circuit/lot08..11_components.jsonl probe events")
m.add("cmCompFlips", sum(not r["predicted_answer"] for r in comp), PA + "circuit/lot08..11_components.jsonl probes with predicted_answer False")
joint = [r for r in jsonl("pod_astra/circuit/lot13_joint.jsonl") if r.get("event") == "joint_patch"]
m.add("cjAll", len(joint), PA + "circuit/lot13_joint.jsonl joint_patch events")
m.add("cjAllFlips", sum(not r["predicted_answer"] for r in joint), PA + "circuit/lot13_joint.jsonl joint_patch with predicted_answer False")
full = {}
for r in joint:
    t = r["pair"]["target"]
    if r["alpha"] == 1.0 and t not in full:
        full[t] = r
assert all(len(r["components"]) == max(len(x["components"]) for x in joint) for r in full.values())
S = PA + "circuit/lot13_joint.jsonl"
m.add("cjN", len(full), S + " targets with the full alpha=1 joint patch")
m.add("cjFlips", sum(not r["predicted_answer"] for r in full.values()), S + " full patch: predicted_answer False")
m.add("cjDeltaMin", f"{min(-r['delta_margin'] for r in full.values()):.1f}", S + " full patch: min |delta_margin|")
m.add("cjDeltaMax", f"{max(-r['delta_margin'] for r in full.values()):.1f}", S + " full patch: max |delta_margin|")
m.add("cjMarginMin", f"{min(r['margin'] for r in full.values()):.1f}", S + " full patch: min remaining margin")
m.write()

plt = setup_mpl()
from matplotlib.colors import TwoSlopeNorm

hd = defaultdict(lambda: defaultdict(list))
for i in (8, 9, 10, 11):
    for r in jsonl(f"pod_astra/circuit/lot{i:02d}_components.jsonl"):
        if r.get("event") == "probe" and r.get("site") == "head" and r.get("anchor") == "tool_name":
            hd[(r["layer"], r["head"])][r["pair"]["label"]].append(r["delta_margin"])
mean_all = {h: np.mean(v.get("fs+", []) + v.get("fs-", [])) for h, v in hd.items()}
heads = sorted(hd, key=lambda h: mean_all[h])[:6]
fig = plt.figure(figsize=(7.0, 2.65))
gs = fig.add_gridspec(1, 5, width_ratios=[1, 1, 0.07, 0.42, 1.45], wspace=0.28)
vmax = max(abs(grid["fs+"]).max(), abs(grid["fs-"]).max())
norm = TwoSlopeNorm(vmin=-vmax, vcenter=0, vmax=vmax)
labels = ["end of\nprefill", "mid\nthink", "end\nthink", "tool\nname"]
for k, (lab, title) in enumerate([("fs+", "a  false “done”"), ("fs-", "b  true “done”")]):
    ax = fig.add_subplot(gs[k])
    im = ax.imshow(grid[lab], origin="lower", aspect="auto", cmap="RdBu", norm=norm)
    ax.set_xticks(range(4), labels, fontsize=5.8)
    ax.set_yticks(range(0, nL, 4))
    ax.set_ylabel("layer" if k == 0 else "")
    ax.set_title(title, fontsize=7.6)
cax = fig.add_subplot(gs[2])
cb = fig.colorbar(im, cax=cax)
cb.set_label("Δ logit margin, answer vs. best other tool", fontsize=6.2)
cb.ax.tick_params(labelsize=6)
fig.add_subplot(gs[3]).axis("off")
ax = fig.add_subplot(gs[4])
y = np.arange(len(heads))
for off, lab, col in [(-0.18, "fs+", C["red"]), (0.18, "fs-", C["green"])]:
    ax.barh(y + off, [np.mean(hd[h].get(lab, [np.nan])) for h in heads], height=0.34, color=col,
            label="false “done”" if lab == "fs+" else "true “done”")
ax.set_yticks(y, [f"L{l}/H{h}" for l, h in heads], fontsize=6.5)
ax.invert_yaxis()
ax.axvline(0, color="#444444", lw=0.6)
ax.set_xlabel("Δ margin when the head is patched (tool-name position)")
ax.set_title("c  top heads: same effect on true and false", fontsize=7.6)
ax.legend(frameon=False, fontsize=6, loc="lower left")
fig.savefig(FIGS / "causal_map.pdf")
print("causal ok", len(arms), n_rejected, flips, len(full))
