"""Anchoring at scale (proof-anchor): note+thought ablations and probes on the strictly feasible cohort.

Reads data/pod_astra/proofanchor/RESULT.json and VERIFY_FINAL.json; PROOF_ANCHOR overrides the directory to dry-run.
"""
import json
import os
from pathlib import Path

from common import DATA, Macros

D = Path(os.environ.get("PROOF_ANCHOR", DATA / "pod_astra/proofanchor"))
SRC = "data/pod_astra/proofanchor/RESULT.json"
r = json.loads((D / "RESULT.json").read_text())
m = Macros("proofanchor")
if not os.environ.get("PROOF_ANCHOR"):
    v = (D / "VERIFY_FINAL.md").read_text()
    assert "PASS" in v and "FAIL" not in v.split("\n")[0], "proof-anchor final audit must pass"
A = r["anchoring"]
S = {"false_finish": "Fs", "true_finish": "True"}
assert r["counts"] == {"false_finish": 19, "true_finish": 20}, r["counts"]


def ci(x, nd=1):
    return "--".join(f"{v:.{nd}f}" for v in x)


for s, T in S.items():
    x = A["strata"][s]
    m.add(f"pa{T}N", x["n_tasks"], SRC + f" anchoring.strata.{s}.n_tasks")
    m.add(f"paOrig{T}", f"{x['conditions']['a']['mean']:.1f}", SRC + f" anchoring.strata.{s}.conditions.a.mean (original margin, logits)")
    for c, name in [("b", "Neutral"), ("c", "Counter"), ("d", "Reason")]:
        m.add(f"pa{name}Left{T}", f"{x['conditions'][c]['mean']:.2f}", SRC + f" anchoring.strata.{s}.conditions.{c}.mean (margin left)")
        dd = x["deltas"][f"a_minus_{c}"]
        m.add(f"pa{name}{T}", f"{dd['mean']:.1f}", SRC + f" anchoring.strata.{s}.deltas.a_minus_{c}.mean")
        m.add(f"pa{name}{T}Ci", ci(dd["ci95"]), SRC + f" anchoring.strata.{s}.deltas.a_minus_{c}.ci95")
    for c, name in [("a", "Orig"), ("b", "Neutral"), ("c", "Counter")]:
        m.add(f"pa{name}Pos{T}", x["conditions"][c]["positive_margin_count"], SRC + f" anchoring.strata.{s}.conditions.{c}.positive_margin_count (answer still preferred)")
    fr = x["fraction_note_and_thought"]["mean_of_ratios"]
    m.add(f"paFrac{T}", f"{100 * fr['mean']:.0f}", SRC + f" anchoring.strata.{s}.fraction_note_and_thought.mean_of_ratios.mean (%)")
    m.add(f"paFrac{T}Ci", "--".join(f"{100 * v:.0f}" for v in fr["ci95"]), SRC + f" ...fraction_note_and_thought.mean_of_ratios.ci95 (%)")
m.add("paNeutralPosAll", sum(A["strata"][s]["conditions"]["b"]["positive_margin_count"] for s in S), SRC + " sum of conditions.b.positive_margin_count")
m.add("paN", sum(A["strata"][s]["n_tasks"] for s in S), SRC + " sum of n_tasks")
it = A["interaction"]
m.add("paInter", f"{it['false_minus_true_delta']:+.2f}".replace("-", "$-$"), SRC + " anchoring.interaction.false_minus_true_delta")
m.add("paInterCi", " to ".join(f"{v:+.2f}".replace("-", "$-$") for v in it["ci95"]), SRC + " anchoring.interaction.ci95")
m.add("paInterP", f"{it['p_two_sided']:.2f}", SRC + " anchoring.interaction.p_two_sided (label permutation)")
m.add("paNullNote", len(A["null_note_contexts"]), SRC + " anchoring.null_note_contexts")
sens = A["nonnull_note_sensitivity_a_minus_b"]["true_finish"]
m.add("paNeutralTrueSens", f"{sens['mean']:.1f}", SRC + " anchoring.nonnull_note_sensitivity_a_minus_b.true_finish.mean")
bp = r["best_probe"]
m.add("paNProbes", len(r["probes"]), SRC + " probes")
m.add("paNLayers", len(r["layer_indices_zero_based"]), SRC + " layer_indices_zero_based")
m.add("paBestAuc", f"{bp['auroc']:.2f}", SRC + " best_probe.auroc (out of fold, selected after the fact)")
m.add("paBestCi", ci(bp["ci95"], 2), SRC + " best_probe.ci95")
base = {b["key"] if "key" in b else b["name"]: b for b in r["baselines"]}
m.add("paStepAuc", f"{base['step_raw_increasing']['auroc']:.2f}", SRC + " baselines step_raw_increasing.auroc")
pm = r["permutation"]
m.add("paPermP", f"{pm['p_unadjusted']:.2f}", SRC + " permutation.p_unadjusted")
m.add("paPermPadj", f"{pm['p_bonferroni_72']:.1f}", SRC + " permutation.p_bonferroni_72")
pw = r["power"]["minimum_auroc_for_80_percent_power"]
m.add("paPowOne", f"{pw['one_sided_05']:.3f}", SRC + " power.minimum_auroc_for_80_percent_power.one_sided_05")
m.add("paPowTwo", f"{pw['two_sided_05']:.3f}", SRC + " power.minimum_auroc_for_80_percent_power.two_sided_05")
m.write()
print("proofanchor ok")
