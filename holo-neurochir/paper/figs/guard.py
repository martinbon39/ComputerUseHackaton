"""Feci Guard: three judges on the same 268 episodes of the original (judge_bench), and the guard's registered design.

Reads data/local/judge_bench/RESULT.json (independent recompute: MATCH) and data/local/feci_guard/.
"""
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
rp = load("local/feci_guard/repair/snapshot/results.json")
RP = "data/local/feci_guard/repair/snapshot/results.json (analyze_repair.py on a copy of the live branches, taken at TAKEN_UTC)"
assert rp["no_guard"]["branches"] == rp["guard"]["branches"]
vs = r["valid_only_sensitivity_holo4_feci"]
m.add("gbHolofourfeciRejValid", pct(vs["true_success"][0] / vs["true_success"][1]), SRC + " valid_only_sensitivity_holo4_feci.true_success (%)")
m.add("gbHolofourfeciNoVerdictTrue", r["judges"]["Holo4-27B (Feci Guard verifier)"]["true_success"]["error_or_invalid"]["numerator"], SRC + " judges.Holo4-27B (Feci Guard verifier).true_success.error_or_invalid.numerator")
m.add("fgRepMaxSteps", re.search(r"max (\d+) new steps", (DATA / "local/feci_guard/PREREG.md").read_text()).group(1), "data/local/feci_guard/PREREG.md Repair measure (max new steps)")
m.add("fgRepTaken", (DATA / "local/feci_guard/repair/snapshot/TAKEN_UTC").read_text().strip(), "data/local/feci_guard/repair/snapshot/TAKEN_UTC")
m.add("fgRepEpisodes", rp["episodes_kept"], RP + " episodes_kept")
m.add("fgRepBranches", rp["guard"]["branches"], RP + " guard.branches (= no_guard.branches)")
m.add("fgRepRepairedNog", rp["no_guard"]["repaired"], RP + " no_guard.repaired")
m.add("fgRepRepairedGuard", rp["guard"]["repaired"], RP + " guard.repaired")
m.add("fgRepRefused", rp["guard_branches_refused"], RP + " guard_branches_refused")
m.add("fgRepPassedFalse", rp["guard_passed_without_refusal_still_false"], RP + " guard_passed_without_refusal_still_false")
pd4 = r["paired_gap_difference_vs_Holo-3.1-4B"]["Holo4-27B"]
m.add("gbHolofourVsHoloCi", " to ".join(spts(x) for x in pd4["ci95"]), SRC + " paired_gap_difference_vs_Holo-3.1-4B.Holo4-27B.ci95")
m.add("gbTasks", re.search(r"resample (\d+) task groups", r["judges"]["Claude (Feci Guard verifier)"]["task_cluster_bootstrap"]["method"]).group(1), SRC + " task_cluster_bootstrap.method (task groups resampled)")
m.add("fgRepairEpisodes", len([l for l in (DATA / "local/feci_guard/repair/episodes.txt").read_text().splitlines() if l.strip()]),
      "data/local/feci_guard/repair/episodes.txt (registered repair measure, not yet run)")
write_table("guard", "\\begin{tabular}{lcccc}\n\\toprule\nJudge & false successes detected & true successes rejected & gap, points [95\\% CI] & no verdict \\\\\n\\midrule\n"
            + "\n".join(rows) + "\n\\bottomrule\n\\end{tabular}\n", "guard")
m.write()
print("guard ok")
