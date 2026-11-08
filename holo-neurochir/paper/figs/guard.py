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
import importlib.util, math
from common import wilson
RD = DATA / "local/feci_guard/repair/final"
RP = "data/local/feci_guard/repair/final/results.json (analyze_repair.py on the final branches.jsonl; RESULTS.md, independently recomputed)"
rp = load("local/feci_guard/repair/final/results.json")
ref = load("local/rescue_bench/HOLO31_REFERENCE.json")["provenance"]
for arm in ("nog", "guard"):
    sha = __import__("hashlib").sha256((RD / arm / "branches.jsonl").read_bytes()).hexdigest()
    assert sha == ref[f"/home/orbit/osw/feci_repair/{arm}/branches.jsonl"]["sha256"], arm
brows = {a: [json.loads(x) for x in (RD / a / "branches.jsonl").read_text().splitlines() if x.strip()] for a in ("nog", "guard")}
assert rp["no_guard"]["branches"] == rp["guard"]["branches"]
m.add("fgRepEpisodes", rp["episodes_kept"], RP + " episodes_kept")
m.add("fgRepExcluded", len(rp["dropped"]), RP + " dropped (replay invalid)")
m.add("fgRepBranches", rp["guard"]["branches"], RP + " guard.branches (= no_guard.branches)")
m.add("fgRepRepairedNog", rp["no_guard"]["repaired"], RP + " no_guard.repaired")
m.add("fgRepRepairedGuard", rp["guard"]["repaired"], RP + " guard.repaired")
m.add("fgRepDiff", f"{100 * rp['paired_diff_mean']:+.1f}", RP + " paired_diff_mean (points)")
m.add("fgRepDiffCi", f"{100 * rp['paired_diff_ci95'][0]:.0f} to {100 * rp['paired_diff_ci95'][1]:+.0f}", RP + " paired_diff_ci95 (episode bootstrap)")
b, w = rp["episodes_guard_better"], rp["episodes_guard_worse"]
m.add("fgRepBetter", b, RP + " episodes_guard_better")
m.add("fgRepWorse", w, RP + " episodes_guard_worse")
m.add("fgRepSignP", f"{min(1.0, 2 * sum(math.comb(b + w, k) for k in range(min(b, w) + 1)) / 2 ** (b + w)):.1f}", RP + " exact two-sided sign test on better/worse episodes")
spec = importlib.util.spec_from_file_location("ar", DATA / "local/feci_guard/analyze_repair.py")
ar = importlib.util.module_from_spec(spec)
spec.loader.exec_module(ar)
d12 = [sum(v["guard"]) / len(v["guard"]) - sum(v["nog"]) / len(v["nog"]) for v in rp["per_episode"].values()]
assert len(d12) == rp["episodes_total"]
d9 = [sum(v["guard"]) / len(v["guard"]) - sum(v["nog"]) / len(v["nog"]) for v in rp["per_episode"].values() if not v["excluded"]]
assert ar.boot(d9) == rp["paired_diff_ci95"]
ups = [ar.boot(d9, seed=sd)[1] for sd in range(20)]
m.add("fgRepDiffHiMin", f"{100 * min(ups):+.0f}", "analyze_repair.boot on the kept episodes, upper bound over seeds 0-19 (min)")
m.add("fgRepDiffHiMax", f"{100 * max(ups):+.0f}", "analyze_repair.boot on the kept episodes, upper bound over seeds 0-19 (max)")
m.add("fgRepDiffAll", f"{100 * sum(d12) / len(d12):+.1f}", RP + " per_episode, all episodes incl. replay-invalid (points)")
m.add("fgRepDiffAllCi", " to ".join(f"{100 * x:+.0f}".replace("+0", "0") for x in ar.boot(d12)), "analyze_repair.boot over all episodes (seed 0, 10,000)")
m.add("fgRepEpisodesAll", rp["episodes_total"], RP + " episodes_total")
nref, nrep = rp["guard_branches_refused"], rp["guard_refused_then_repaired"]
m.add("fgRepRefused", nref, RP + " guard_branches_refused")
m.add("fgRepRefusals", rp["guard_refusals_total"], RP + " guard_refusals_total")
m.add("fgRepRefusedRepaired", nrep, RP + " guard_refused_then_repaired")
m.add("fgRepRefusedRepairedPct", f"{100 * nrep / nref:.0f}", RP + " refused_then_repaired / refused")
m.add("fgRepRefusedRepairedCi", "--".join(f"{100 * x:.0f}" for x in wilson(nrep, nref)), "Wilson 95% of refused_then_repaired / refused")
kept = {t for t, v in rp["per_episode"].items() if not v["excluded"]}
key = lambda t: t.split("/pyautogui/screenshot/Holo-3.1-4B/")[-1]
g = [x for x in brows["guard"] if key(x["task"]) in kept]
assert len(g) == rp["guard"]["branches"]
m.add("fgRepRefusedNoAnswer", sum(x["guard"]["refusals"] > 0 and not x["finished_by_agent"] and x["score"] < 1 for x in g), "final/guard/branches.jsonl kept: refused, no answer within the step limit, not repaired")
m.add("fgRepCapWrong", sum("passed_cap" in x["guard"]["decisions"] and x["score"] < 1 for x in g), "final/guard/branches.jsonl kept: passed at the refusal cap, still wrong")
wrong_ok = {key(x["task"]) for x in g if x["guard"]["decisions"] == ["passed_complete"] and x["score"] < 1}
assert all(all(y["guard"]["decisions"] == ["passed_complete"] and y["score"] < 1 for y in g if key(y["task"]) == t) for t in wrong_ok)
m.add("fgRepWrongComplete", len(wrong_ok), "final/guard/branches.jsonl kept: episodes accepted as COMPLETE in every branch while wrong")
both = [t for t, v in rp["per_episode"].items() if not v["excluded"] and min(v["guard"]) == 1 and min(v["nog"]) == 1]
assert len(both) == 1
m.add("fgRepBothTask", both[0].split("/")[0].replace("libreoffice_", "") + "/" + both[0].split("/")[1][:8], RP + " per_episode: solved in every branch of both arms")
assert rp["guard"]["repaired"] - sum(rp["per_episode"][both[0]]["guard"]) == nrep
m.add("fgRepSpecific", nrep, RP + " repairs specific to the guard: guard repairs minus the episode solved in every branch = refused then repaired")
pd4 = r["paired_gap_difference_vs_Holo-3.1-4B"]["Holo4-27B"]
m.add("gbHolofourVsHoloCi", " to ".join(spts(x) for x in pd4["ci95"]), SRC + " paired_gap_difference_vs_Holo-3.1-4B.Holo4-27B.ci95")
m.add("gbTasks", re.search(r"resample (\d+) task groups", r["judges"]["Claude (Feci Guard verifier)"]["task_cluster_bootstrap"]["method"]).group(1), SRC + " task_cluster_bootstrap.method (task groups resampled)")
m.add("fgRepairEpisodes", len([l for l in (DATA / "local/feci_guard/repair/episodes.txt").read_text().splitlines() if l.strip()]),
      "data/local/feci_guard/repair/episodes.txt (registered repair measure)")
V2 = DATA / "local/feci_guard/v2"
V2S = "data/local/feci_guard/v2/"
man = {e["episode_id"]: e for e in json.loads((DATA / "local/judge_bench/verif_study_manifest.json").read_text())}
assert __import__("hashlib").sha256((DATA / "local/judge_bench/verif_study_manifest.json").read_bytes()).hexdigest() == r["corpus"]["manifest_sha256"]
hold = set(json.loads((V2 / "SPLIT.json").read_text())["holdout"])


def verdicts(path):
    out = {}
    for x in path.read_text().splitlines():
        j = json.loads(x)
        if j["episode_id"] in hold:
            out[j["episode_id"]] = j["result"].get("verdict") == "INCOMPLETE"
    return out


v1 = verdicts(DATA / "local/judge_bench/claude_responses.jsonl")
v2 = verdicts(V2 / "runs/ab_holdout.jsonl")
assert set(v1) == set(v2) == hold
sc = {json.loads(x)["variant"]: json.loads(x) for x in (V2 / "holdout_scores.jsonl").read_text().splitlines()}
lab = lambda e: man[e]["label"]
for name, v, tag in [("v1", v1, "One"), ("ab", v2, "Two")]:
    fsd = sum(v[e] for e in hold if lab(e) == "false_success"); fsn = sum(lab(e) == "false_success" for e in hold)
    trd = sum(v[e] for e in hold if lab(e) == "true_success"); trn = sum(lab(e) == "true_success" for e in hold)
    assert f"{fsd}/{fsn}" == sc[name]["detection"] and f"{trd}/{trn}" == sc[name]["false_rejection"], name
    m.add(f"gv{tag}Det", f"{fsd}/{fsn}", V2S + f"runs + holdout_scores.jsonl {name} detection")
    m.add(f"gv{tag}DetPct", f"{100 * fsd / fsn:.0f}", V2S + f"{name} detection (%)")
    m.add(f"gv{tag}Rej", f"{trd}/{trn}", V2S + f"{name} false rejection")
    m.add(f"gv{tag}RejPct", f"{100 * trd / trn:.1f}", V2S + f"{name} false rejection (%)")
by = {}
for e in hold:
    by.setdefault((man[e]["domain"], man[e]["task_id"]), []).append(e)
tasks = sorted(by)
rnd = __import__("random").Random(0)
dd, dr = [], []
for _ in range(10000):
    smp = [e for t in (rnd.choice(tasks) for _ in tasks) for e in by[t]]
    f_ = [e for e in smp if lab(e) == "false_success"]; t_ = [e for e in smp if lab(e) == "true_success"]
    if f_ and t_:
        dd.append((sum(v2[e] for e in f_) - sum(v1[e] for e in f_)) / len(f_))
        dr.append((sum(v2[e] for e in t_) - sum(v1[e] for e in t_)) / len(t_))
dd.sort(); dr.sort()
q = lambda xs: [xs[int(.025 * len(xs))], xs[int(.975 * len(xs)) - 1]]
F = [e for e in hold if lab(e) == "false_success"]; T = [e for e in hold if lab(e) == "true_success"]
m.add("gvTasks", len(tasks), V2S + "SPLIT.json holdout: distinct (domain, task_id)")
m.add("gvDetDiff", f"{100 * (sum(v2[e] for e in F) - sum(v1[e] for e in F)) / len(F):+.1f}", "paired ab - v1 detection on the held-out half (points)")
m.add("gvDetDiffCi", " to ".join(f"{100 * x:+.0f}" for x in q(dd)).replace("-", "$-$"), "task-cluster bootstrap, 10,000, seed 0 (figs/guard.py)")
m.add("gvRejDiff", f"{100 * (sum(v2[e] for e in T) - sum(v1[e] for e in T)) / len(T):+.1f}", "paired ab - v1 false rejection on the held-out half (points)")
m.add("gvRejDiffCi", " to ".join(f"{100 * x:+.0f}" for x in q(dr)).replace("-", "$-$"), "task-cluster bootstrap, 10,000, seed 0 (figs/guard.py)")
pr = (V2 / "PROTOCOL.md").read_text()
cm = __import__("re").search(r"c (\d+)/(\d+), (\d+)/(\d+)\.", pr)
m.add("gvStrictDet", f"{cm.group(1)}/{cm.group(2)}", V2S + "PROTOCOL.md dev results, variant c (strict prompt) detection")
m.add("gvStrictRej", f"{cm.group(3)}/{cm.group(4)}", V2S + "PROTOCOL.md dev results, variant c false rejection")
write_table("guard", "\\begin{tabular}{lcccc}\n\\toprule\nJudge & false successes detected & true successes rejected & gap, points [95\\% CI] & no verdict \\\\\n\\midrule\n"
            + "\n".join(rows) + "\n\\bottomrule\n\\end{tabular}\n", "guard")
m.write()
print("guard ok")
