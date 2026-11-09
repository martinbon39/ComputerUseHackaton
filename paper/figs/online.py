"""Online OSWorld evaluation: confirmation reserve and TEST split, paired by task.

Source: data/local/online/<run>/pyautogui/screenshot/<model>/<domain>/<task>/{result.txt,meta.json}, verbatim copies of
~/osw/<run>/ (score in result.txt; the model directory names the served checkpoint).
Runs and where the model was served:
  reserve (confirm_tasks.json):
    results_val_orig_eager_m40         original, local harness, served by the pod (H200)
    results_confirm_gh_orig_confirm    original, GitHub Actions harness, served by the pod (H200)
    results_val_patched_eager_m40      ExPO lambda=1.25 (model dir Holo-3.1-4B-expo125), local harness, pod
    results_val_lm40_eager_m40         answer output-row edit lm40, local harness, pod (stopped at 14 tasks)
    results_val_prompt_eager_m40       corrective prompt, local harness, pod (stopped at 20 tasks)
    results_confirm_gh_orig_modal_confirm  original, GitHub harness, served by Modal (H100), model dir Holo-3.1-4B-modal-orig
    results_confirm_gh_merge_cua_b050  CUA-Lite merge beta=0.5, GitHub harness, served by Modal (H100)
    results_confirm_gh_broad_residual_p100  closed-form edit of 24 writers, GitHub harness, Modal
  TEST (120 tasks): results_test_gh_orig (pod), results_test_gh_expo125 (pod), results_test_gh_prompt_PARTIAL (38 tasks),
    results_test_gh_merge_cua_b050 (Modal), results_test_gh_orig_modal_test (original, Modal, model dir Holo-3.1-4B-modal-orig)
Primary verdict (rule fixed in JOURNAL 03:36 UTC): merge vs Modal-served original over reserve + TEST (165 tasks).
Each arm is paired with an original run on the same harness, and the Modal arms on the reserve with the Modal-served
original. SERVER_SENSITIVE names the two reserve tasks that the second red-team review found at 0 under the pod original
and 1 under the Modal arms; they score 0 under the Modal original too (asserted below), so the gap was not the server.
95% CIs by task bootstrap (10,000 resamples, fixed seed).
"""
import math
import random

from common import DATA, Macros, write_table

m = Macros("online")
ROOT = DATA / "local/online"
S = "data/local/online/"
SERVER_SENSITIVE = {"2bd59342", "bf4e9888"}


def load_run(run):
    out, models = {}, set()
    for f in (ROOT / run).rglob("result.txt"):
        if "_jobs" in f.parts:
            continue
        parts = f.relative_to(ROOT / run).parts
        models.add(parts[2])
        out[parts[-2]] = float(f.read_text().strip())
    return out, models


RUNS = {"res_orig": "results_val_orig_eager_m40", "res_orig_gh": "results_confirm_gh_orig_confirm",
        "res_expo": "results_val_patched_eager_m40", "res_lm40": "results_val_lm40_eager_m40",
        "res_prompt": "results_val_prompt_eager_m40", "res_cua": "results_confirm_gh_merge_cua_b050",
        "res_broad": "results_confirm_gh_broad_residual_p100", "res_orig_modal": "results_confirm_gh_orig_modal_confirm",
        "test_orig": "results_test_gh_orig", "test_expo": "results_test_gh_expo125",
        "test_prompt": "results_test_gh_prompt_PARTIAL", "test_cua": "results_test_gh_merge_cua_b050",
        "test_orig_modal": "results_test_gh_orig_modal_test"}
R = {}
for k, run in RUNS.items():
    R[k], models = load_run(run)
    assert len(models) == 1, (run, models)
    if "expo" in k:
        assert models == {"Holo-3.1-4B-expo125"}, (run, models)

sens = {t for t in R["res_orig_gh"] if t[:8] in SERVER_SENSITIVE}
assert len(sens) == 2 and all(R["res_orig_gh"][t] == 0 and R["res_orig"].get(t, 0) == 0 for t in sens), sens
assert all(R["res_cua"][t] == 1 and R["res_broad"][t] == 1 and R["res_orig_modal"][t] == 0 for t in sens)
assert not set(R["res_cua"]) & set(R["test_cua"])
R["all_cua"] = {**R["res_cua"], **R["test_cua"]}
R["all_orig_modal"] = {**R["res_orig_modal"], **R["test_orig_modal"]}
RUNS_ALL = dict(RUNS, all_cua=RUNS["res_cua"] + " + " + RUNS["test_cua"], all_orig_modal=RUNS["res_orig_modal"] + " + " + RUNS["test_orig_modal"])
assert R["res_orig_modal"] and all("modal" in m for m in load_run(RUNS["res_orig_modal"])[1])


def boot(diffs, n=10000, seed=0):
    rng = random.Random(seed)
    k = len(diffs)
    means = sorted(sum(rng.choice(diffs) for _ in range(k)) / k for _ in range(n))
    return means[int(0.025 * n)], means[int(0.975 * n) - 1]


def frac(x, n):
    return f"{x:.1f}/{n}" if abs(x - round(x)) > 1e-9 else f"{int(round(x))}/{n}"


def compare(arm, base, tag, label, src, exclude=()):
    a, b = R[arm], R[base]
    common = sorted((set(a) & set(b)) - set(exclude))
    d = [a[t] - b[t] for t in common]
    lo, hi = boot(d)
    sa, sb = sum(a[t] for t in common), sum(b[t] for t in common)
    win, loss = sum(x > 0 for x in d), sum(x < 0 for x in d)
    delta = 100 * (sa - sb) / len(common)
    m.add(tag + "N", len(common), src + " tasks scored in both runs")
    m.add(tag + "Arm", frac(sa, len(common)), src + " sum of scores, paired tasks")
    m.add(tag + "Orig", frac(sb, len(common)), S + RUNS_ALL[base] + " same tasks")
    m.add(tag + "Delta", f"{delta:+.1f}".replace("-", "$-$"), "paired mean difference, points")
    m.add(tag + "Ci", f"{100 * lo:+.1f} to {100 * hi:+.1f}".replace("-", "$-$"), "task bootstrap 95% CI, points")
    m.add(tag + "Disc", f"{win} against {loss}", "tasks where the first run scores higher / lower")
    return (f"{label} & {len(common)} & {100 * sa / len(common):.1f} & {100 * sb / len(common):.1f} & "
            + f"{delta:+.1f} [{100 * lo:+.1f}, {100 * hi:+.1f}]".replace("-", "$-$") + f" & {win}/{loss} \\\\ % source: {src}")


miss = sorted(set(R["res_orig_gh"]) - set(R["res_orig"]))
assert len(miss) == 1 and not set(R["res_orig"]) - set(R["res_orig_gh"]), miss
dom = {f.parts[-3] for f in (ROOT / RUNS["res_orig_gh"]).rglob("result.txt") if f.parts[-2] == miss[0]}
assert len(dom) == 1
m.add("onNoiseMissingTask", miss[0][:8], S + RUNS["res_orig_gh"] + " task absent from " + RUNS["res_orig"])
m.add("onNoiseMissingDomain", dom.pop().replace("_", "\\_"), S + RUNS["res_orig_gh"] + " domain directory of that task")
m.add("onNoiseMissingScore", f"{R['res_orig_gh'][miss[0]]:.0f}", S + RUNS["res_orig_gh"] + " its score")
NOISE3 = [("res_orig", "local/H200"), ("res_orig_gh", "GitHub/H200"), ("res_orig_modal", "GitHub/Modal")]
pcts = [100 * sum(R[k].values()) / len(R[k]) for k, _ in NOISE3]
ns = sorted({len(R[k]) for k, _ in NOISE3})
m.add("onReserveOrigRange", f"{max(pcts) - min(pcts):.1f}", S + " max - min mean score of the three reserve runs of the original")
rows = [
    "\\multicolumn{6}{l}{\\emph{Reserve, noise reference: the original against itself}} \\\\",
    ("Original, three runs, harness/server (" + "; ".join(l for _, l in NOISE3) + ") & " + "--".join(map(str, ns)) + " & \\multicolumn{2}{c}{"
     + " / ".join(f"{x:.1f}" for x in pcts) + f"}} & spread {max(pcts) - min(pcts):.1f} points & -- \\\\ % source: "
     + ", ".join(S + RUNS[k] for k, _ in NOISE3)),
    compare("res_orig", "res_orig_gh", "onNoise", "Original, local vs.\\ GitHub harness (both served by our H200)", S + RUNS["res_orig"]),
    compare("res_orig_gh", "res_orig_modal", "onNoiseServer", "Original, H200 vs.\\ Modal (both on the GitHub harness)", S + RUNS["res_orig_gh"]),
    "\\midrule\\multicolumn{6}{l}{\\emph{Reserve, arms served by our H200, vs.\\ the H200 original on the local harness}} \\\\",
    compare("res_expo", "res_orig", "onReserveExpo", "ExPO $\\lambda=1.25$", S + RUNS["res_expo"]),
    compare("res_lm40", "res_orig", "onReserveLmrow", "\\texttt{answer} output-row edit (stopped early)", S + RUNS["res_lm40"]),
    compare("res_prompt", "res_orig", "onReservePrompt", "Corrective prompt (stopped early)", S + RUNS["res_prompt"]),
    "\\midrule\\multicolumn{6}{l}{\\emph{Reserve, arms served by Modal, vs.\\ the Modal original on the GitHub harness}} \\\\",
    compare("res_cua", "res_orig_modal", "onReserveCua", "CUA-Lite merge $\\beta=0.5$", S + RUNS["res_cua"]),
    compare("res_broad", "res_orig_modal", "onReserveBroad", "Closed-form edit of 24 writers (100\\%)", S + RUNS["res_broad"]),
    "\\midrule\\multicolumn{6}{l}{\\emph{\\textsc{test} split (GitHub harness), vs.\\ the H200 original}} \\\\",
    compare("test_expo", "test_orig", "onTestExpo", "ExPO $\\lambda=1.25$ (had not passed the gate)", S + RUNS["test_expo"]),
    compare("test_prompt", "test_orig", "onTestPrompt", "Corrective prompt (partial run)", S + RUNS["test_prompt"]),
    compare("test_orig", "test_orig_modal", "onTestNoiseServer", "Original, H200 vs.\\ Modal (noise reference)", S + RUNS["test_orig"]),
    compare("test_cua", "test_orig_modal", "onTestCua", "CUA-Lite merge $\\beta=0.5$, vs.\\ the Modal original", S + RUNS["test_cua"]),
    "\\midrule\\multicolumn{6}{l}{\\emph{Primary verdict, rule fixed after the merge's reserve scores were seen: reserve and \\textsc{test}, Modal against Modal}} \\\\",
    compare("all_cua", "all_orig_modal", "onAllCua", "CUA-Lite merge $\\beta=0.5$", S + RUNS_ALL["all_cua"]),
]
for k, label in [("res_orig", "Reserve"), ("res_orig_gh", "ReserveGh"), ("res_orig_modal", "ReserveModal"), ("test_orig", "Test"), ("test_orig_modal", "TestModal")]:
    b = R[k]
    m.add(f"on{label}OrigN", len(b), S + RUNS[k] + " tasks scored")
    m.add(f"on{label}OrigScore", frac(sum(b.values()), len(b)).split("/")[0], S + RUNS[k] + " sum of scores")
    m.add(f"on{label}OrigPct", f"{100 * sum(b.values()) / len(b):.1f}", S + RUNS[k] + " mean score %")
m.add("onNRuns", len(RUNS), "online runs in figs/online.py RUNS (originals included)")
m.add("onNTestRuns", sum(k.startswith("test") for k in RUNS), "TEST-split runs in figs/online.py RUNS")
m.add("onNArms", sum("orig" not in k for k in RUNS), "non-original online runs in figs/online.py RUNS")

a, b = R["res_expo"], R["res_orig"]
common = sorted(set(a) & set(b))
d = [a[t] - b[t] for t in common]
mu = sum(d) / len(d)
sd = math.sqrt(sum((x - mu) ** 2 for x in d) / (len(d) - 1))
mde = (1.96 + 0.8416) * sd / math.sqrt(len(d))
m.add("onMde", f"{100 * mde:.0f}", S + "reserve ExPO vs original: (z_.975+z_.80) * SD(paired diff) / sqrt(n)")
m.add("onMdeN", len(d), S + "reserve ExPO vs original paired tasks")
write_table("b4_heldout", "\\begin{tabular}{lccccc}\n\\toprule\n"
            "Comparison & tasks & first \\% & second \\% & $\\Delta$ points [95\\% CI] & better/worse \\\\\n\\midrule\n"
            + "\n".join(rows) + "\n\\bottomrule\n\\end{tabular}\n", "online")
tc = __import__("json").loads((ROOT / "test_compare.json").read_text())["pairs"]["expo125-orig"]["all"]["success"]
m.add("onTestExpoBinDelta", f"{100 * tc['delta']:+.1f}".replace("-", "$-$"), S + "test_compare.json pairs.expo125-orig.all.success.delta (binary success, online-eval)")
m.add("onTestExpoBinCi", f"{100 * tc['ic95'][0]:+.1f} to {100 * tc['ic95'][1]:+.1f}".replace("-", "$-$"), S + "test_compare.json ...success.ic95")
BP = ROOT / "branch_pilot"
br = {a: [__import__("json").loads(l) for l in (BP / a / "branches.jsonl").read_text().splitlines()] for a in ("orig", "cand")}
assert {x["model"] for x in br["orig"]} == {"Holo-3.1-4B-modal-orig"} and {x["model"] for x in br["cand"]} == {"Holo-3.1-4B-merge_cua_b050"}
assert {x["task"] for x in br["orig"]} == {x["task"] for x in br["cand"]}
for a, tag in [("orig", "Orig"), ("cand", "Cand")]:
    m.add(f"br{tag}", f"{sum(x['score'] == 1 for x in br[a])}/{len(br[a])}", S + f"branch_pilot/{a}/branches.jsonl score == 1")
m.add("brEpisodes", len({x["task"] for x in br["orig"]}), S + "branch_pilot/orig/branches.jsonl distinct tasks")
bad = {x["task"] for x in br["orig"] + br["cand"] if x["replay_diff_max"] > 0.05}
assert len(bad) == 1, bad
func = {t: __import__("json").loads((DATA / f"local/osworld_tasks/{t.split('/')[-1]}.json").read_text())["evaluator"]["func"] for t in {x["task"] for x in br["orig"]}}
rep = [x for x in br["orig"] if x["recorded_score"] == 0 and x["score"] > 0]
assert len(rep) == 1 and func[rep[0]["task"]] == "infeasible", rep
m.add("brRepairTask", rep[0]["task"].split("/")[1][:8], S + "branch_pilot/orig/branches.jsonl recorded_score 0, branch score > 0")
m.add("brRepairDomain", rep[0]["task"].split("/")[0], S + "branch_pilot/orig/branches.jsonl task domain")
for a_, tag in [("orig", "Orig"), ("cand", "Cand")]:
    ff = [x for x in br[a_] if x["recorded_score"] == 0 and func[x["task"]] != "infeasible" and x["task"] not in bad]
    m.add(f"brFeasFalse{tag}", f"{sum(x['score'] == 1 for x in ff)}/{len(ff)}", S + f"branch_pilot/{a_}/branches.jsonl recorded false successes, evaluator.func != infeasible (data/local/osworld_tasks), faithful replay")
vm = __import__("re").search(r"paced replay: \*\*(\d+)/(\d+)\*\*", (BP / "REPORT.md").read_text())
m.add("brValidOk", vm.group(1), S + "branch_pilot/REPORT.md 'paced replay' validation")
m.add("brValidN", vm.group(2), S + "branch_pilot/REPORT.md 'paced replay' validation")
m.write()
print("online ok", {k: (len(v), round(sum(v.values()), 2)) for k, v in R.items()}, "mde", round(mde, 3))
