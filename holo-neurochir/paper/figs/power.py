"""Strictly feasible cohort (astra-power): answer rates of the original (A) and the CUA-Lite merge (B), k=4.

Reads data/pod_astra/power/RESULT.json; POWER_RESULT overrides the path to dry-run on a provisional file.
"""
import os
from pathlib import Path

from common import DATA, Macros, load

import json

P = Path(os.environ.get("POWER_RESULT", DATA / "pod_astra/power/RESULT.json"))
SRC = "data/pod_astra/power/RESULT.json"
d = json.loads(P.read_text())
m = Macros("power")
for arm in ("A", "B"):
    assert d["completeness"][arm]["status"] == "COMPLETE", (arm, d["completeness"][arm])
fc = d["full_cohort"]
NAMES = {"A": "Orig", "B": "Cua", "C": "Broad", "D": "Rand"}
ARMS = {a: n for a, n in NAMES.items() if d["completeness"][a]["status"] == "COMPLETE"}
assert set(ARMS) <= set(fc["arms"]), (ARMS, list(fc["arms"]))
STRATA = {"fs+": "Fsp", "fs-": "Fsm", "healthy": "Healthy"}


def signed(x):
    return "0.0" if round(100 * x, 1) == 0 else f"{100 * x:+.1f}".replace("-", "$-$")


for arm, A in ARMS.items():
    for s, S in STRATA.items():
        c = fc["arms"][arm][s]
        assert c["invalid"] == 0 and c["transport_error"] == 0
        m.add(f"pw{A}{S}", f"{c['answer']}/{c['n_generations']}", SRC + f" full_cohort.arms.{arm}.{s}.answer/n_generations")
    m.add(f"pw{A}Tasks", fc["arms"][arm]["fs+"]["n_tasks"], SRC + f" full_cohort.arms.{arm}.fs+.n_tasks")
for arm, A in ARMS.items():
    if arm == "A":
        continue
    key = f"{arm}-A"
    ct = fc["contrasts"][key]
    assert ct["treatment"] == arm and ct["reference"] == "A", key
    for s, S in STRATA.items():
        x = ct["strata"][s]
        lo, hi = x["task_bootstrap95"]
        m.add(f"pw{A}Delta{S}", signed(x["delta"]), SRC + f" contrasts.{key}.strata.{s}.delta (points)")
        m.add(f"pw{A}Ci{S}", f"{signed(lo)} to {signed(hi)}", SRC + f" contrasts.{key}.strata.{s}.task_bootstrap95")
    sel = ct["selectivity"]
    m.add(f"pw{A}Sel", signed(sel["delta_fs_minus_delta_true"]), SRC + f" contrasts.{key}.selectivity.delta_fs_minus_delta_true")
    m.add(f"pw{A}SelCi", f"{signed(sel['task_bootstrap95'][0])} to {signed(sel['task_bootstrap95'][1])}", SRC + f" contrasts.{key}.selectivity.task_bootstrap95")
cd = fc["contrasts"]["C-D"]
assert cd["treatment"] == "C" and cd["reference"] == "D"
m.add("pwBroadVsRandDeltaFsp", signed(cd["strata"]["fs+"]["delta"]), SRC + " full_cohort.contrasts.C-D.strata.fs+.delta")
m.add("pwBroadVsRandCiFsp", " to ".join(signed(x) for x in cd["strata"]["fs+"]["task_bootstrap95"]), SRC + " full_cohort.contrasts.C-D.strata.fs+.task_bootstrap95")
ex = d["excluding_C_construction_and_preservation"]
m.add("pwSensFsp", ex["arms"]["A"]["fs+"]["n_tasks"], SRC + " excluding_C_construction_and_preservation.arms.A.fs+.n_tasks")
m.add("pwBroadSensDeltaFsp", signed(ex["contrasts"]["C-A"]["strata"]["fs+"]["delta"]), SRC + " excluding_C_construction_and_preservation.contrasts.C-A.strata.fs+.delta")
m.add("pwBroadSensCiFsp", " to ".join(signed(x) for x in ex["contrasts"]["C-A"]["strata"]["fs+"]["task_bootstrap95"]), SRC + " excluding_C_...contrasts.C-A.strata.fs+.task_bootstrap95")
for arm, A in [("B", "Cua"), ("C", "Broad")]:
    cdl = fc["contrasts"][f"{arm}-A"]["strata"]["fs+"]["context_deltas"]
    m.add(f"pw{A}FspDown", sum(v < 0 for v in cdl.values()), SRC + f" contrasts.{arm}-A.strata.fs+.context_deltas < 0")
v = json.loads((DATA / "pod_astra/power/VERIFY_FINAL.json").read_text())
assert v["phase"] == "final" and v["status"] == "PASS" and all(c["status"] == "PASS" for c in v["checks"].values())
assert d["status"] == "COMPLETE"
sc = load("pod_astra/moonleak/screen_head4_s0.json")
assert sc["arm"] == "head4_s0" and sc["metrics"]["fs+"]["tasks"] == 19 and sc["errors"] == 0
SC = "data/pod_astra/moonleak/screen_head4_s0.json"
m.add("mlZeroFsp", signed(-sc["metrics"]["fs+"]["drop"]), SC + " metrics.fs+.drop, sign flipped to answer change (points)")
m.add("mlZeroFspCi", " to ".join(signed(-x) for x in reversed(sc["metrics"]["fs+"]["drop_ci95"])), SC + " metrics.fs+.drop_ci95, sign flipped")
m.add("mlZeroHealthy", signed(-sc["metrics"]["healthy"]["drop"]), SC + " metrics.healthy.drop (valid non-answer), sign flipped")
rl = load("pod_astra/moonrl/analysis_rl100.json")
RL = "data/pod_astra/moonrl/analysis_rl100.json"
assert rl["arm"] == "rl100" and rl["strata"]["fs+"]["tasks"] == 19
x = rl["strata"]["fs+"]["metrics"]["answer"]
m.add("rlFsp", signed(x["delta"]), RL + " strata.fs+.metrics.answer.delta")
m.add("rlFspCi", " to ".join(signed(v) for v in x["ci95"]), RL + " strata.fs+.metrics.answer.ci95")
h = rl["strata"]["healthy"]["metrics"]["valid_nonanswer"]
m.add("rlHealthy", signed(h["delta"]), RL + " strata.healthy.metrics.valid_nonanswer.delta (REVIEW_RL100.md: healthy gate fails)")
for arm, A in [("A", "Orig")]:
    for s_, S_ in [("fs+", "Fsp"), ("fs-", "Fsm")]:
        c = fc["arms"][arm][s_]
        m.add(f"pw{A}{S_}Pct", f"{100 * c['answer'] / c['n_generations']:.0f}", SRC + f" full_cohort.arms.{arm}.{s_} answer rate (%)")
m.add("pwBootReps", f"{d['method']['bootstrap_replicates']:,}".replace(",", "{,}"), SRC + " method.bootstrap_replicates")
m.add("pwStatus", d["status"], SRC + " status")
m.write()
print("power ok", d["status"], {k: v["status"] for k, v in d["completeness"].items()})
