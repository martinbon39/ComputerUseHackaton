"""fs+ answer counts with and without the one infeasible fs+ context (chrome/480bcfea...@4).

On an infeasible task the correct action is `answer` with a refusal, so an `answer` there is not a false success.
For every arm whose fs+ `answer` count the paper reports, this script gives the count over all fs+ contexts and the
count with that context removed.

Split modes:
  per-context  the source file lists outputs or counts per context.
  implied      the source only has stratum totals, but every fs+ output answered (k = n) and the cohort is shown to
               contain the context with a known number of samples, so removing it leaves (k - m)/(n - m) exactly.

Sources:
  data/local/diagnostic_osw_diag.json, diagnostic_osw_diag2.json         infeasible flag of the task (both passes)
  data/pod_astra/4b/, think/, value/, circuit/, perceive/, verify/, mit1/  Table 2 arms (figs/causal.py)
  data/pod_astra/neurons/metrics.json                                    construction vs. evaluation tasks
  data/pod_astra/free/external/<arm>/summary.json, audit_external_*      attractor arms and blind audits
  data/pod_astra/merge/<arm>_generations.jsonl                           verbatim copies of /tmp/astra-merge-work/<arm>_full/
                                                                         generations.jsonl (sha256 = STATIC_RESULTS.json)
  data/pod_astra/broad/ceiling.jsonl                                     ceiling-test recipient context
"""
import ast
import hashlib
import json
from collections import Counter

from common import DATA, Macros, load, tex_escape, write_table

TASK = "chrome/480bcfea-d68f-4aaa-a0a9-2589ef319381"
STEP = 4
UUID = TASK.split("/")[1]
SHORT = UUID[:8]
PA = "data/pod_astra/"
m = Macros("infeasible")
rows = []  # (group, arm label, macro key, (k, n), (k_ex, n_ex), mode, source)


def is_ctx(task_id, t):
    return str(task_id).endswith(UUID) and int(t) == STEP


def jsonl(rel):
    return [json.loads(l) for l in (DATA / rel).read_text().splitlines() if l.strip()]


def as_dict(x):
    return x if isinstance(x, dict) else ast.literal_eval(x)


def truthy(x):
    return x is True or x == "True"


def split(items):
    """items: (task_id, t, k_answer, n) for fs+ only -> ((k, n), (k_ex, n_ex))."""
    k = sum(i[2] for i in items)
    n = sum(i[3] for i in items)
    kx = sum(i[2] for i in items if not is_ctx(i[0], i[1]))
    nx = sum(i[3] for i in items if not is_ctx(i[0], i[1]))
    assert nx < n, "context absent from this source"
    return (k, n), (kx, nx)


def implied(k, n, m_ctx):
    assert k == n, "an implied split needs every fs+ output to answer"
    return (k, n), (k - m_ctx, n - m_ctx)


def add(group, label, key, counts, mode, src):
    (k, n), (kx, nx) = counts
    rows.append((group, label, key, (k, n), (kx, nx), mode, src))
    m.add(f"inf{key}All", f"{k}/{n}", src + f" fs+ answer, all contexts ({mode})")
    m.add(f"inf{key}Excl", f"{kx}/{nx}", src + f" fs+ answer, without {SHORT}@{STEP} ({mode})")


# ---------------------------------------------------------------- the task is infeasible in both diagnostic passes
for f in ("local/diagnostic_osw_diag.json", "local/diagnostic_osw_diag2.json"):
    t = [x for x in load(f)["tasks"] if x["task"] == TASK]
    assert len(t) == 1 and t[0]["infeasible"] is True and t[0]["fs_labels"][STEP] == "fs+", f
m.add("infTask", SHORT, f"data/local/diagnostic_osw_diag.json tasks[{TASK}] (infeasible=True, fs_labels[{STEP}]=fs+; same in diagnostic_osw_diag2.json)")
m.add("infTaskId", tex_escape(TASK), "data/local/diagnostic_osw_diag.json tasks[].task")
m.add("infStep", STEP, "data/local/diagnostic_osw_diag.json tasks[].fs_labels index of fs+")

# ---------------------------------------------------------------- Table 2 (figs/causal.py)
G = "Steering screens (Table~\\ref{tab:causal})"
l24 = []
for r in jsonl("pod_astra/4b/pilot_c1_add_l24.jsonl"):
    if "tool" in r and "row" in r and as_dict(r["row"])["label"] == "fs+":
        row = as_dict(r["row"])
        l24.append((row["task_id"], row["t"], int(truthy(r["answer"])), 1))
m_pilot = sum(i[3] for i in l24 if is_ctx(i[0], i[1]))
j16, j24 = load("pod_astra/4b/pilot_c1_add_l16_job.json"), load("pod_astra/4b/pilot_c1_add_l24_job.json")
assert (j16["manifest"], j16["indices"]) == (j24["manifest"], j24["indices"])
mt24 = load("pod_astra/4b/pilot_c1_add_l24_metrics.json")["strata"]["fs+"]
ref = load("pod_astra/4b/runtime_status.json")["strata"]["fs+"]
assert (ref["answer"], ref["n"]) == (mt24["original"]["answer"]["count"], mt24["n"])
add(G, "original reference", "CausalOrig", implied(ref["answer"], ref["n"], m_pilot), "implied",
    PA + "4b/runtime_status.json strata.fs+ (cohort: original block of 4b/pilot_c1_add_l24_metrics.json, rows in 4b/pilot_c1_add_l24.jsonl)")
s16 = load("pod_astra/4b/pilot_c1_add_l16_metrics.json")["strata"]["fs+"]
add(G, "residual addition L16", "CausalAddSixteen", implied(s16["candidate"]["answer"]["count"], s16["n"], m_pilot), "implied",
    PA + "4b/pilot_c1_add_l16_metrics.json strata.fs+ (job indices = 4b/pilot_c1_add_l24_job.json)")
c24 = split(l24)
assert c24[0] == (mt24["candidate"]["answer"]["count"], mt24["n"])
add(G, "residual addition L24", "CausalAddTwentyFour", c24, "per-context", PA + "4b/pilot_c1_add_l24.jsonl")

jt = load("pod_astra/think/screen_add_half_job.json")
assert jt["indices"] == j24["indices"]
st = load("pod_astra/think/metrics_active.json")["screen_add_half"]["strata"]["fs+"]
add(G, "``conclusion'' direction, L31", "CausalThink", implied(st["candidate"]["answer"]["count"], st["n"], m_pilot), "implied",
    PA + "think/metrics_active.json screen_add_half.strata.fs+ (job indices = 4b/pilot_c1_add_l24_job.json)")

vs = {l["job"]["name"]: l for l in load("pod_astra/value/summary.json")["lots"]}
m_value = None
for name, lab, key in [("r1_value_L24_a05_prefill", "Value Axis, value, L24", "CausalValueTwentyFour"),
                       ("r1_commitment_L24_a05_prefill", "Value Axis, commitment, L24", "CausalCommitTwentyFour")]:
    it = [(i["task"], i["t"], i["answer"], i["n"]) for i in vs[name]["instances"] if i["label"] == "fs+"]
    c = split(it)
    cmp_ = load(f"pod_astra/value/{name}.comparison.json")["strata"]["fs+"]
    assert c[0] == (cmp_["candidate"]["answer"]["count"], cmp_["n"])
    m_value = sum(i[3] for i in it if is_ctx(i[0], i[1]))
    add(G, lab, key, c, "per-context", PA + f"value/summary.json lots[{name}].instances")
v18 = []
for r in jsonl("pod_astra/value/r1_value_L18_a05_prefill.jsonl"):
    if "row" in r and as_dict(r["row"])["label"] == "fs+":
        row = as_dict(r["row"])
        v18.append((row["task_id"], row["t"], int(truthy(r["answer"])), 1))
c = split(v18)
cmp_ = load("pod_astra/value/r1_value_L18_a05_prefill.comparison.json")["strata"]["fs+"]
assert c[0] == (cmp_["candidate"]["answer"]["count"], cmp_["n"])
add(G, "Value Axis, value, L18", "CausalValueEighteen", c, "per-context", PA + "value/r1_value_L18_a05_prefill.jsonl")
cmp_ = load("pod_astra/value/r1_commitment_L18_a05_prefill.comparison.json")["strata"]["fs+"]
add(G, "Value Axis, commitment, L18", "CausalCommitEighteen",
    implied(cmp_["candidate"]["answer"]["count"], cmp_["n"], m_value), "implied",
    PA + "value/r1_commitment_L18_a05_prefill.comparison.json strata.fs+ (cohort: value/summary.json, same fs+ n)")

nm = load("pod_astra/neurons/metrics.json")
assert TASK in nm["construction_tasks"] and TASK not in nm["eval_tasks"]

for e in load("pod_astra/circuit/behavior_summary.json")["experiments"]:
    sp = e["spec"]
    it = []
    for iid, v in e["per_instance"].items():
        if v["label"] == "fs+":
            tid, t = iid.rsplit("_", 1)
            it.append((tid, int(t), sum(x == "answer" for x in v["tools"]), len(v["tools"])))
    c = split(it)
    assert c[0] == (e["metrics"]["fs+"]["answer"], e["metrics"]["fs+"]["n"])
    lab = ("circuit, random control" if sp["random"] else "circuit C1") + f", $\\alpha={sp['alpha']}$"
    key = "CausalCircuit" + ("Random" if sp["random"] else "") + {0.5: "Half", 1.0: "Full"}[sp["alpha"]]
    add(G, lab, key, c, "per-context", PA + f"circuit/behavior_summary.json experiments[{sp['name']}].per_instance")

for tag, a_, key in [("a0p5", "0.5", "Half"), ("a1", "1", "One"), ("a2", "2", "Two"), ("a4", "4", "Four"), ("random_a4", "4", "RandomFour")]:
    f = f"completion_l15_{tag}" if not tag.startswith("random") else "completion_random_l15_a4"
    d = load(f"pod_astra/perceive/{f}.metrics.json")
    pi = [p for p in d["per_instance"] if p["label"] == "fs+"]
    c = split([(p["task_id"], p["t"], p["candidate_answer"], len(p["candidate_tools"])) for p in pi])
    s_ = d["stats"]["fs+"]
    assert c[0] == (round(s_["candidate"] * s_["n"]), s_["n"])
    rnd = tag.startswith("random")
    add(G, f"perceive{', random control' if rnd else ''}, $\\alpha={a_}$", "CausalPerceive" + key, c, "per-context",
        PA + f"perceive/{f}.metrics.json per_instance")
    if rnd:
        cb = split([(p["task_id"], p["t"], p["baseline_answer"], len(p["baseline_tools"])) for p in pi])
        assert cb[0] == (round(s_["baseline"] * s_["n"]), s_["n"])
        add(G, "perceive reference contexts (original)", "CausalPerceiveBase", cb, "per-context",
            PA + f"perceive/{f}.metrics.json per_instance baseline_answer")

vm = load("pod_astra/verify/metrics.json")["metrics"]
for arm, lab, key in [("baseline_calibration", "verify, calibration baseline", "CausalVerifyBase"),
                      ("verify_a1", "verify, dose 1", "CausalVerifyOne"), ("verify_a2", "verify, dose 2", "CausalVerifyTwo"),
                      ("random_a1", "verify, random control, dose 1", "CausalVerifyRandomOne"),
                      ("random_a2", "verify, random control, dose 2", "CausalVerifyRandomTwo")]:
    x = vm[arm]
    it = [(k_.rsplit(":", 1)[0], k_.rsplit(":", 1)[1], v["answer"], v["n"]) for k_, v in x["per_instance"].items() if v["label"] == "fs+"]
    c = split(it)
    assert c[0] == (x["fs+"]["answer"], x["fs+"]["n"])
    add(G, lab, key, c, "per-context", PA + f"verify/metrics.json metrics.{arm}.per_instance")

for f, lab, key in [("lot05_vllm_baseline", "weight edits, vLLM reference", "CausalMitBase"),
                    ("lot06_vllm_wait2", "``Wait'' output row", "CausalMitWait"),
                    ("lot08_decay080", "linear-attention retention $\\times0.8$", "CausalMitDecayShort"),
                    ("lot09_decay125", "linear-attention retention $\\times1.25$", "CausalMitDecayLong")]:
    d = load(f"pod_astra/mit1/{f}.summary.json")
    b = [x for x in d["brief"] if x["label"] == "fs+"]
    c = split([(x["task"], x["t"], int(x["tool"] == "answer"), 1) for x in b])
    assert c[0] == (d["counts"]["fs+"]["answer"], d["counts"]["fs+"]["observed"])
    add(G, lab, key, c, "per-context", PA + f"mit1/{f}.summary.json brief")
d = load("pod_astra/mit1/semantic_lot14.json")
o = [x for x in d["outputs"] if x["label"] == "fs+"]
c = split([(x["task_id"], x["t"], int(x["false_completion"]), 1) for x in o])
assert c[0] == (d["summary"]["fs_plus"]["false_completion"], d["summary"]["fs_plus"]["outputs"])
add(G, "H4 audit: false-completion claims", "CausalMitHfourFalse", c, "per-context", PA + "mit1/semantic_lot14.json outputs")
for f in ("semantic_lot19.json", "SEMANTIC_AUDIT_LOT15_ADDED_BASELINE.json"):
    assert not any(a["task_id"] == TASK for a in load("pod_astra/mit1/" + f)["annotations"])

# ---------------------------------------------------------------- attractor arms (figs/attractor.py) and blind audits
G = "Mechanism-level edits (Table~\\ref{tab:attractor})"
S = PA + "free/"
ARMS = [("orig_modal", "original (re-served)", "Orig"), ("free_h2", "H2", "Htwo"), ("free_h3_l05", "H3, $\\lambda=0.5$", "Hthreehalf"),
        ("free_h5_l05", "H5, $\\lambda=0.5$", "Hfivehalf"), ("free_h6_s05", "H6", "Hsix"), ("free_h2_l2", "H2, $\\lambda=2$", "Htwotwo"),
        ("free_h9_a020", "H9", "Hnine"), ("free_h10_half", "H10, $s=0.5$", "Htenhalf"), ("free_h10_zero", "H10, $s=0$", "Htenzero"),
        ("free_h3_l1", "H3, $\\lambda=1$", "Hthreefull")]
per_ctx_n = {}
for arm, lab, key in ARMS:
    it = []
    for k_, v in load(f"pod_astra/free/external/{arm}/summary.json")["per_row"].items():
        _, g, ctx = k_.split(" | ")
        if g == "fs+":
            tid, t = ctx.rsplit("@", 1)
            it.append((tid, t, v["answer"], v["n"]))
            if is_ctx(tid, t):
                per_ctx_n[arm] = v["n"]
    add(G, lab, "Free" + key, split(it), "per-context", S + f"external/{arm}/summary.json per_row")

ADJ = "audit_external_h6_pair.fs_text.adjudicated.verdict.json"
akey = load("pod_astra/free/audit_external_h6_pair.key.json")
adj = [x for x in load("pod_astra/free/" + ADJ)["samples"] if x["kind"] == "gui" and x["label"] == "fs+"]
for arm, lab, key in [("orig_modal", "audit: original", "Orig"), ("free_h6_s05", "audit: H6", "Hsix")]:
    it = [(akey[x["id"]][1], akey[x["id"]][2], int(x["false_completion_claim"]), 1) for x in adj if akey[x["id"]][0] == arm]
    add(G, lab + ", false-completion claims", "FreeAudit" + key, split(it), "per-context", S + ADJ + " + audit_external_h6_pair.key.json")
for r in load("pod_astra/free/audit_external_all4.aggregate.json")["counts"]:
    if r["group"] == "fs+" and r["arm"] != "orig_modal":
        lab, key = next((l, k) for a, l, k in ARMS if a == r["arm"])
        add(G, f"audit: {lab}, false-completion claims", "FreeAudit" + key,
            implied(r["false_completion_claim"], r["n"], per_ctx_n[r["arm"]]), "implied",
            S + f"audit_external_all4.aggregate.json counts[{r['arm']}, fs+] (per-context n: external/{r['arm']}/summary.json)")
nonans = [x for x in adj if akey[x["id"]][0] == "free_h6_s05" and x["tool"] != "answer"]
m.add("infHsixNonAnswer", len(nonans), S + ADJ + " H6 fs+ non-answer outputs")
m.add("infHsixNonAnswerOnCtx", sum(is_ctx(akey[x["id"]][1], akey[x["id"]][2]) for x in nonans),
      S + ADJ + f" H6 fs+ non-answer outputs on {SHORT}@{STEP}")

# ---------------------------------------------------------------- donor merges (figs/broad.py)
G = "Donor merge"
static = {r["name"]: r for r in load("pod_astra/merge/STATIC_RESULTS.json")["results"]}
for name, lab, key in [("Holo-3.1-4B", "original (re-served)", "Orig"), ("merge_cua_b025", "CUA donor, $\\beta=0.25$", "CuaQuarter"),
                       ("merge_cua_b050", "CUA donor, $\\beta=0.5$", "CuaHalf"), ("merge_fara_b050", "Fara donor, $\\beta=0.5$", "FaraHalf")]:
    rel = f"pod_astra/merge/{name}_generations.jsonl"
    assert hashlib.sha256((DATA / rel).read_bytes()).hexdigest() == static[name]["generations_sha256"]
    it = []
    for r in jsonl(rel):
        row = as_dict(r["row"])
        if row.get("label") == "fs+":
            it.append((row["task_id"], row["t"], int(truthy(r["answer"])), 1))
    c = split(it)
    g = static[name]["groups"]["fs+"]
    assert c[0] == (g["answer"], g["n"])
    add(G, lab, "Merge" + key, c, "per-context", "data/" + rel + " (sha256 = merge/STATIC_RESULTS.json generations_sha256)")

# ---------------------------------------------------------------- ceiling test recipient
rec = {(r["metadata"]["task_id"], r["metadata"]["t"]) for r in jsonl("pod_astra/broad/ceiling.jsonl") if r["metadata"]["label"] == "fs+"}
m.add("ceilRecipientInfeasible", "yes" if rec == {(TASK, STEP)} else ("partly" if (TASK, STEP) in rec else "no"),
      PA + f"broad/ceiling.jsonl metadata (label fs+): recipient contexts {sorted(rec)}")

# ---------------------------------------------------------------- sources that do not contain the task id
absent = []
for d_ in ("ratio", "mit2", "short", "tact"):
    hit = any(SHORT in p.read_text(errors="ignore") for p in (DATA / "pod_astra" / d_).rglob("*") if p.is_file())
    assert not hit, d_
    absent.append(d_)
m.add("infAbsent", ", ".join(absent), PA + "{" + ",".join(absent) + "}/* contain no occurrence of " + SHORT)

body = ["\\begin{tabular}{llcc}", "\\toprule",
        "Source & Arm & fs+ \\texttt{answer} (all) & fs+ \\texttt{answer} (excl.\\ infeasible) \\\\", "\\midrule"]
prev = None
for group, lab, key, (k, n), (kx, nx), mode, src in rows:
    if prev is not None and group != prev:
        body.append("\\midrule")
    mark = "$^{*}$" if mode == "implied" else ""
    body.append(f"{group if group != prev else ''} & {lab} & {k}/{n} & {kx}/{nx}{mark} \\\\ % source: {src}")
    prev = group
body += ["\\midrule",
         f"\\multicolumn{{4}}{{p{{12cm}}}}{{\\footnotesize Not included: \\texttt{{neurons}} (task {SHORT} is a construction task, "
         f"not evaluated); {', '.join(f'\\texttt{{{a}}}' for a in absent)} (no task id {SHORT} in their data files). "
         f"$^{{*}}$ every fs+ output answered, so the split follows from the per-context sample count.}} \\\\ "
         f"% source: {PA}neurons/metrics.json construction_tasks/eval_tasks; " + ", ".join(PA + a + "/*" for a in absent),
         "\\bottomrule", "\\end{tabular}", ""]
write_table("infeasible", "\n".join(body), "infeasible")
m.write()
for r in rows:
    print(f"{r[0][:22]:22s} {r[2]:26s} {r[3][0]}/{r[3][1]:<3} -> {r[4][0]}/{r[4][1]:<3} {r[5]}")
print("ceiling recipients", rec, "absent", absent, "H6 non-answer", len(nonans))
