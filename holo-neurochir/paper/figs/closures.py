"""Negative closures of the last hypotheses: MIT-recipe replication, end-of-thinking promotion, late mit1 edits, TACT.

Sources (verbatim copies from the pod):
  data/pod_astra/ratio/semantic_summary.json   blind semantic audit per arm (alpha 0.5/1/1.5/6, random 1 and 6)
  data/pod_astra/short/REPORT.md               generation table (end-of-thinking promotion, doses 12/16/20)
  data/pod_astra/mit1/REPORT.md                H7-H9 closures (0/8 useful), H10 construction gate
  data/pod_astra/tact/REPORT.md                TACT dual-axis construction (OT and OA axes) after label audit
"""
import re

from common import DATA, Macros, load

m = Macros("closures")
SR = "data/pod_astra/ratio/semantic_summary.json"
arms = load("pod_astra/ratio/semantic_summary.json")["arms"]
learned = ["v_a05", "v_a1", "v_a15", "v_a6"]
m.add("ratioSeries", "/8, ".join(str(arms[a]["fs+"]["premature_answer"]) for a in learned) + "/8",
      SR + " fs+ premature_answer for alpha 0.5, 1, 1.5, 6")
m.add("ratioUsefulAll", sum(arms[a]["fs+"]["useful"] for a in arms), SR + " fs+ useful summed over all arms")
m.add("ratioRandSix", f"{arms['v_random6']['fs+']['premature_answer']}/{arms['v_random6']['fs+']['observed']}", SR + " v_random6 fs+")
tf = [arms[a]["fs-"]["true_finish_preserved"] for a in learned]
m.add("ratioTrueRange", f"{min(tf)}--{max(tf)}/12", SR + " fs- true_finish_preserved range over learned arms")
m.add("ratioTrueOrig", f"{arms['v_baseline_retry']['fs-']['true_finish_preserved']}/12", SR + " v_baseline_retry fs-")

SS = "data/pod_astra/short/REPORT.md"
tab = {r[1]: r for r in re.findall(r"^\| (\d+) \| (\S+) \| ([^|]+) \| (\d+)/(\d+) \| [^|]+ \| (\d+) \| ([0-9/]+) \| ([0-9/]+) \|",
                                    (DATA / "pod_astra/short/REPORT.md").read_text(), re.M)}
o, e12, e16, e20 = tab["lot03_original"], tab["lot04_endthink12"], tab["lot05_endthink16"], tab["lot06_endthink20_sentinel"]
m.add("shortOrigFsp", o[6], SS + " lot03_original answer fs+")
m.add("shortTwelveFsp", e12[6], SS + " lot04_endthink12 answer fs+")
m.add("shortOrigFsm", o[7], SS + " lot03_original answer fs-")
m.add("shortTwelveFsm", e12[7], SS + " lot04_endthink12 answer fs-")
m.add("shortSixteenInv", f"{e16[5]}/{e16[3]}", SS + " lot05_endthink16 invalid/truncated JSON over outputs")
m.add("shortTwentyInv", f"{e20[5]}/{e20[3]}", SS + " lot06_endthink20 invalid/truncated JSON over outputs")

SM = "data/pod_astra/mit1/REPORT.md"
rep = (DATA / "pod_astra/mit1/REPORT.md").read_text()
use = {h: re.search(rf"{h} closed[^\n]*?0/8 ?(?:useful|utility)", rep) is not None for h in ("H7", "H8", "H9")}
assert all(use.values()), use
m.add("mitOneLateN", len(use), SM + " H7, H8, H9 closed with 0/8 useful at each dose")

ST = "data/pod_astra/tact/REPORT.md"
t = (DATA / "pod_astra/tact/REPORT.md").read_text()
mt = re.search(r"best pooled([0-9.]+); position\(step,log context\)([0-9.]+); position\+reasoning length([0-9]+\.[0-9]+)", t)
m.add("tactAuc", f"{float(mt.group(1)):.3f}", ST + " final OT grouped out-of-fold AUROC, best pooled")
m.add("tactPos", f"{float(mt.group(2)):.3f}", ST + " position baseline")
m.add("tactPosLen", f"{float(mt.group(3)):.3f}", ST + " position + reasoning length baseline")
mc = re.search(r"Final frozen construction:(\d+) states,(\d+)CAL/(\d+)OT/(\d+)OA", t)
m.add("tactOT", mc.group(3), ST + " final frozen construction OT states")
m.add("tactOA", mc.group(4), ST + " final frozen construction OA states")
SI = "data/pod_astra/infeas/reviewed_inventory.json"
inv = load("pod_astra/infeas/reviewed_inventory.json")
hr, oc = inv["human_review_summary"], inv["observed_and_counterfactual"]
m.add("infAllowed", inv["allowlisted_tasks"], SI + " allowlisted_tasks")
m.add("infEpisodes", inv["infeasible_episode_rows"], SI + " infeasible_episode_rows")
m.add("infTasks", inv["unique_infeasible_tasks"], SI + " unique_infeasible_tasks")
m.add("infAnswered", oc["answered_episodes"], SI + " answered_episodes")
m.add("infClaim", hr["success_or_completion_claim"] + hr["mixed_local_limitation_but_overall_success_claim"], SI + " success claims incl. mixed")
m.add("infInabilityTasks", oc["strict_semantic_admissible_unique_tasks"], SI + " strict_semantic_admissible_unique_tasks")
m.add("infRegexMiss", oc["answered_episodes_missed_by_supplied_regex"], SI + " answered_episodes_missed_by_supplied_regex")
ST2 = "data/local/osworld_tasks/480bcfea-d68f-4aaa-a0a9-2589ef319381.json"
m.add("infTaskInstruction", load("local/osworld_tasks/480bcfea-d68f-4aaa-a0a9-2589ef319381.json")["instruction"].strip(), ST2 + " instruction")
SG = "data/pod_astra/regmean/overlap_summary.json"
og = load("pod_astra/regmean/overlap_summary.json")
ov = load("pod_astra/regmean/overlap.json")
m.add("rmFsp", ov["n_fs_positive"], "data/pod_astra/regmean/overlap.json n_fs_positive")
m.add("rmFsm", ov["n_true_finish"], "data/pod_astra/regmean/overlap.json n_true_finish")
m.add("rmWriters", len({r["writer"] for r in ov["records"]}), "data/pod_astra/regmean/overlap.json distinct writers")
rm_fsp = sorted({r["task_id"] for r in load("pod_astra/regmean/manifest.json")["rows"] if r["label"] == "fs+"})
assert len(rm_fsp) == ov["n_fs_positive"]
rm_inf = [t for t in rm_fsp if load(f"local/osworld_tasks/{t.split('/')[-1]}.json")["evaluator"]["func"] == "infeasible"]
assert len(rm_inf) == 5 and "five of original 19" in load("pod_astra/power/BUILD_AUDIT.json")["shortfall"]
ba = load("pod_astra/power/BUILD_AUDIT.json")
assert ba["all_feasible"] is True
for k, tag in [("fs+", "Fsp"), ("fs-", "Fsm"), ("healthy", "Healthy")]:
    m.add("pw" + tag, ba["counts"][k], f"data/pod_astra/power/BUILD_AUDIT.json counts.{k} (strictly feasible cohort, astra-power)")
m.add("rmFspInfeasible", len(rm_inf), "data/local/osworld_tasks/<id>.json evaluator.func == infeasible over regmean/manifest.json fs+ tasks; agrees with data/pod_astra/power/BUILD_AUDIT.json shortfall")
for pos, P in [("prefill", "Pre"), ("endthink_before_note", "End")]:
    g = og[pos]
    m.add(f"rm{P}Auc", f"{g['auroc_ridge_median']:.3f}", SG + f" {pos}.auroc_ridge_median (over writers)")
    m.add(f"rm{P}Angle", f"{g['median_principal_angle']:.0f}", SG + f" {pos}.median_principal_angle (degrees)")
    m.add(f"rm{P}Energy", f"{100 * g['f_energy_in_t']:.0f}", SG + f" {pos}.f_energy_in_t (%)")
b = og["baselines"]
m.add("rmBaseStep", f"{b['t']['ridge']:.3f}", SG + " baselines.t.ridge")
m.add("rmBaseLen", f"{b['n_in']['ridge']:.3f}", SG + " baselines.n_in.ridge")
m.add("rmBaseBoth", f"{b['step_and_length']['ridge']:.3f}", SG + " baselines.step_and_length.ridge")
pl = load("pod_astra/free/external/free_h6_s025/pilot.json")
assert pl["truncated"] and pl["parsed"] is None
m.add("hsixQuarterTokens", f"{pl['n_out']:,}".replace(",", "{,}"), "data/pod_astra/free/external/free_h6_s025/pilot.json n_out (finish_reason length, unparsed)")
rows = load("pod_astra/regmean/manifest.json")["rows"]
def raw_auc(key):
    pos = [r[key] for r in rows if r["label"] == "fs+"]
    neg = [r[key] for r in rows if r["label"] == "fs-"]
    return sum(1.0 if p > q else 0.5 if p == q else 0.0 for p in pos for q in neg) / (len(pos) * len(neg))
m.add("rmRawStep", f"{raw_auc('t'):.3f}", "data/pod_astra/regmean/manifest.json rows fs+ vs fs-: raw AUROC of t (no fit)")
m.add("rmRawLen", f"{raw_auc('n_in'):.3f}", "data/pod_astra/regmean/manifest.json rows fs+ vs fs-: raw AUROC of n_in (no fit)")
import statistics
for pos, P in [("prefill", "Pre"), ("endthink_before_note", "End")]:
    rs = [r for r in ov["records"] if r["position"] == pos]
    m.add(f"rm{P}Oof", f"{statistics.median(r['cv']['oof_auc']['ridge'] for r in rs):.3f}", "data/pod_astra/regmean/overlap.json records[position].cv.oof_auc.ridge, median over writers")
    lo_, hi_ = og[pos]["auroc_ridge_range"]
    m.add(f"rm{P}Range", f"{lo_:.2f}--{hi_:.2f}", SG + f" {pos}.auroc_ridge_range")
m.add("rmBaseStepOof", f"{ov['baselines']['t']['oof_auc']['ridge']:.3f}", "data/pod_astra/regmean/overlap.json baselines.t.oof_auc.ridge")
m.add("rmPairs", sum(f["pairs"] for f in ov["baselines"]["t"]["folds"]), "data/pod_astra/regmean/overlap.json baselines.t.folds[].pairs summed")
m.write()
print("closures ok")
