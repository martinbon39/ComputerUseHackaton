"""Feci Guard: three judges on the same 268 episodes of the original (judge_bench), and the guard's registered design.

Reads data/local/judge_bench/RESULT.json (independent recompute: MATCH) and data/local/feci_guard/.
"""
import json
import re

from common import DATA, Macros, load, write_table

SRC = "data/local/judge_bench/RESULT.json"
r = load("local/judge_bench/RESULT.json")
assert r["independent_recompute"]["status"].startswith("MATCH on all four judges") and r["independent_recompute"]["counts_exact"]
m = Macros("guard")
J = [("Holo-3.1-4B", "Holo", "Holo-3.1-4B judging its own episodes"), ("Holo4-27B", "Holofour", "Holo4-27B, same prompt"),
     ("Holo4-27B (Feci Guard verifier)", "Holofourfeci", "Holo4-27B, frozen Feci Guard verifier"),
     ("Claude (Feci Guard verifier)", "Claude", "Claude Sonnet, frozen Feci Guard verifier")]
fs_n = r["corpus"]["labels"]["false_success"]
ts_n = r["corpus"]["labels"]["true_success"]
m.add("gbEpisodes", r["corpus"]["episodes"], SRC + " corpus.episodes")
m.add("gbFs", fs_n, SRC + " corpus.labels.false_success")
m.add("gbTrue", ts_n, SRC + " corpus.labels.true_success")


def pct(x):
    return f"{100 * x:.0f}"


def spts(x):
    return f"{100 * x:+.0f}".replace("-", "$-$")


rows = []
for key, tag, label in J:
    j = r["judges"][key]
    f, t = j["false_success"]["incomplete_rate"], j["true_success"]["incomplete_rate"]
    assert f["denominator"] == fs_n and t["denominator"] == ts_n
    g = j["gap_detection_minus_false_rejection"]
    lo, hi = j["task_cluster_bootstrap"]["ci95"]["detection_minus_false_rejection"]
    m.add(f"gb{tag}Det", pct(f["rate"]), SRC + f" judges.{key}.false_success.incomplete_rate.rate (%)")
    m.add(f"gb{tag}Rej", pct(t["rate"]), SRC + f" judges.{key}.true_success.incomplete_rate.rate (%)")
    m.add(f"gb{tag}Gap", spts(g), SRC + f" judges.{key}.gap_detection_minus_false_rejection (points)")
    m.add(f"gb{tag}GapCi", f"{spts(lo)} to {spts(hi)}", SRC + f" judges.{key}.task_cluster_bootstrap.ci95.detection_minus_false_rejection")
    inv = j["false_success"]["error_or_invalid"]["numerator"] + j["true_success"]["error_or_invalid"]["numerator"]
    m.add(f"gb{tag}NoVerdict", inv, SRC + f" judges.{key}.*.error_or_invalid.numerator (counted as pass)")
    rows.append(f"{label} & {f['numerator']}/{fs_n} ({pct(f['rate'])}\\%) & {t['numerator']}/{ts_n} ({pct(t['rate'])}\\%) & "
                f"{spts(g)} [{spts(lo)}, {spts(hi)}] & {inv} \\\\ % source: {SRC} judges.{key}")
pd = r["paired_gap_difference_vs_Holo-3.1-4B"]["Claude (Feci Guard verifier)"]
m.add("gbClaudeVsHolo", spts(pd["point"]), SRC + " paired_gap_difference_vs_Holo-3.1-4B.Claude.point")
m.add("gbClaudeVsHoloCi", " to ".join(spts(x) for x in pd["ci95"]), SRC + " paired_gap_difference_vs_Holo-3.1-4B.Claude.ci95")
pf = r["paired_gap_difference_vs_Holo-3.1-4B"]["Holo4-27B (Feci Guard verifier)"]
m.add("gbHolofourfeciVsHolo", spts(pf["point"]), SRC + " paired_gap_difference_vs_Holo-3.1-4B.Holo4-27B (Feci Guard verifier).point")
m.add("gbHolofourfeciVsHoloCi", " to ".join(spts(x) for x in pf["ci95"]), SRC + " ...ci95")
pc = r["paired_gap_difference_vs_Claude"]["Holo4-27B (Feci Guard verifier)"]
m.add("gbHolofourfeciVsClaude", spts(pc["point"]), SRC + " paired_gap_difference_vs_Claude.Holo4-27B (Feci Guard verifier).point")
m.add("gbHolofourfeciVsClaudeCi", " to ".join(spts(x) for x in pc["ci95"]), SRC + " paired_gap_difference_vs_Claude...ci95")
vs = r["valid_only_sensitivity_holo4_feci"]
m.add("gbHolofourfeciRejValid", pct(vs["true_success"][0] / vs["true_success"][1]), SRC + " valid_only_sensitivity_holo4_feci.true_success (%)")
m.add("gbHolofourfeciNoVerdictTrue", r["judges"]["Holo4-27B (Feci Guard verifier)"]["true_success"]["error_or_invalid"]["numerator"], SRC + " judges.Holo4-27B (Feci Guard verifier).true_success.error_or_invalid.numerator")
LS = "data/local/online/results_test_gh_orig_modal_test/last_steps.jsonl"
ls = [json.loads(x) for x in (DATA / "local/online/results_test_gh_orig_modal_test/last_steps.jsonl").read_text().splitlines()]
assert len(ls) == 120
fs_done = sum(x["last_tool"] == "answer" and x["score"] == 0 for x in ls)
true_done = sum(x["last_tool"] == "answer" and x["score"] >= 1 for x in ls)
f = fs_done / (fs_done + true_done)
cj = r["judges"]["Claude (Feci Guard verifier)"]
det, rej = cj["false_success"]["incomplete_rate"]["rate"], cj["true_success"]["incomplete_rate"]["rate"]
prec = det * f / (det * f + rej * (1 - f))
m.add("fgBaseFsDone", fs_done, LS + " last_tool == answer and score == 0 (extract_last_steps.py)")
m.add("fgBaseTrueDone", true_done, LS + " last_tool == answer and score == 1")
m.add("fgBasePartialDone", sum(x["last_tool"] == "answer" and 0 < x["score"] < 1 for x in ls), LS + " last_tool == answer and partial score (excluded)")
m.add("fgBaseF", f"{f:.2f}", LS + " false share of answered tasks, partial credit excluded")
m.add("fgPrecision", f"{prec:.2f}", "det*f/(det*f+rej*(1-f)), Claude rates from " + SRC + " and f from " + LS)
m.add("fgRepMaxSteps", re.search(r"max (\d+) new steps", (DATA / "local/feci_guard/PREREG.md").read_text()).group(1), "data/local/feci_guard/PREREG.md Repair measure (max new steps)")
ref = load("local/rescue_bench/HOLO31_REFERENCE.json")
rp = ref["contemporary_live_measure"]
RP = "data/local/rescue_bench/HOLO31_REFERENCE.json contemporary_live_measure (audited by rescue-bench)"
assert rp["measure_complete"] and rp["no_guard"]["branches"] == rp["guard"]["branches"] == rp["primary_branches_per_arm"]
m.add("fgRepEpisodes", rp["primary_complete_valid_episodes"], RP + " primary_complete_valid_episodes")
m.add("fgRepExcluded", len(rp["dropped"]), RP + " dropped (replay_invalid)")
m.add("fgRepBranches", rp["primary_branches_per_arm"], RP + " primary_branches_per_arm")
m.add("fgRepRepairedNog", rp["no_guard"]["repaired_score1"], RP + " no_guard.repaired_score1")
m.add("fgRepRepairedGuard", rp["guard"]["repaired_score1"], RP + " guard.repaired_score1")
m.add("fgRepDiff", f"{rp['paired_diff_mean']:+.2f}", RP + " paired_diff_mean (episode level, mean over K)")
m.add("fgRepDiffCi", " to ".join(f"{x:.2f}" for x in rp["paired_diff_ci95_episode_bootstrap"]), RP + " paired_diff_ci95_episode_bootstrap")
m.add("fgRepRefused", rp["guard_branches_refused"], RP + " guard_branches_refused")
m.add("fgRepRefusedRepaired", rp["guard_refused_then_repaired"], RP + " guard_refused_then_repaired")
m.add("fgRepBetter", rp["episodes_guard_better"], RP + " episodes_guard_better")
m.add("fgRepWorse", rp["episodes_guard_worse"], RP + " episodes_guard_worse")
both = [t for t, v in rp["episode_scores"].items() if not v["excluded"] and min(v["guard_scores"]) == 1 and min(v["no_guard_scores"]) == 1]
assert len(both) == 1
m.add("fgRepBothTask", both[0].split("/")[0].replace("libreoffice_", "") + "/" + both[0].split("/")[1][:8], RP + " episode_scores: solved in every branch of both arms")
pd4 = r["paired_gap_difference_vs_Holo-3.1-4B"]["Holo4-27B"]
m.add("gbHolofourVsHoloCi", " to ".join(spts(x) for x in pd4["ci95"]), SRC + " paired_gap_difference_vs_Holo-3.1-4B.Holo4-27B.ci95")
m.add("gbTasks", re.search(r"resample (\d+) task groups", r["judges"]["Claude (Feci Guard verifier)"]["task_cluster_bootstrap"]["method"]).group(1), SRC + " task_cluster_bootstrap.method (task groups resampled)")
m.add("fgRepairEpisodes", len([l for l in (DATA / "local/feci_guard/repair/episodes.txt").read_text().splitlines() if l.strip()]),
      "data/local/feci_guard/repair/episodes.txt (registered repair measure, not yet run)")
write_table("guard", "\\begin{tabular}{lcccc}\n\\toprule\nJudge & false successes detected & true successes rejected & gap, points [95\\% CI] & no verdict \\\\\n\\midrule\n"
            + "\n".join(rows) + "\n\\bottomrule\n\\end{tabular}\n", "guard")
m.write()
print("guard ok")
