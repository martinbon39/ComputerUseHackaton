"""Ceiling test (astra-broad) and donor merge (astra-merge).

Sources (verbatim copies from the pod):
  data/pod_astra/broad/ceiling.jsonl      forced-input replay, logits only: one fs+ decision step and its donor
                                          (the previous GUI action of the same task), writer outputs swapped at
                                          the decision position, blocks 0-11 / 12-23 / 24-31 (PROTOCOL.md stage 0)
  data/pod_astra/broad/PROTOCOL.md        block definitions, self-swap and donor-reproduction checks
  data/pod_astra/merge/STATIC_RESULTS.json  51 generations per arm, vLLM on Modal, original re-served (CUA 0.25/0.5, Fara 0.5)
  data/pod_astra/merge/VERIFY_*_BEHAVIOR.{json,md}  independent audits of these counts and of the replacing actions
"""
import json
import re

from common import FIGS, C, DATA, Macros, load, setup_mpl

m = Macros("broad")
SB = "data/pod_astra/broad/ceiling.jsonl"
rows = {}
for line in (DATA / "pod_astra/broad/ceiling.jsonl").read_text().splitlines():
    r = json.loads(line)
    rows[r["name"]] = r
mg = {k: r["answer_margin"] for k, r in rows.items()}
assert mg["self_swap"] == mg["baseline_fs"], "self-swap must reproduce the baseline"
assert mg["mlp+mixer_all"] == mg["baseline_donor"], "swapping every writer must reproduce the donor"
names = {"baseline_fs": "Base", "baseline_donor": "Donor", "mlp_all": "MlpAll", "mlp_early": "MlpEarly",
         "mlp_middle": "MlpMiddle", "mlp_late": "MlpLate", "mlp+mixer_all": "BothAll",
         "mlp+mixer_early": "BothEarly", "mlp+mixer_middle": "BothMiddle"}
for k, n in names.items():
    m.add("ceil" + n, f"{mg[k]:+.1f}".replace("-", "$-$"), SB + f" {k}.answer_margin")
m.add("ceilNContexts", len({r["metadata"]["id"] for r in rows.values() if r["metadata"]["label"] == "fs+"}),
      SB + " distinct fs+ recipient contexts")
m.add("ceilNForward", max(r["forward"] for r in rows.values()), SB + " forward counter")

SR = "data/pod_astra/broad/ceiling_resume.jsonl"
rr = {}
for line in (DATA / "pod_astra/broad/ceiling_resume.jsonl").read_text().splitlines():
    r = json.loads(line)
    rr[r["name"]] = r
mr = {k: r["answer_margin"] for k, r in rr.items()}
assert mr["resume_self_swap"] == mr["baseline_fs_0"] and mr["resume_resid31_donor"] == mr["baseline_donor_0"]
for k, n in {"resume_mlp+mixer_late": "BothLate", "baseline_fs_1": "SecBase", "baseline_donor_1": "SecDonor",
             "second_fs_mlp_all": "SecMlpAll", "second_fs_mlp+mixer_middle": "SecBothMiddle",
             "baseline_true_finish": "TrueBase", "true_finish_mlp+mixer_middle": "TrueBothMiddle"}.items():
    m.add("ceil" + n, f"{mr[k]:+.1f}".replace("-", "$-$"), SR + f" {k}.answer_margin")
m.add("ceilNContextsAll", len({r["metadata"]["id"] for r in list(rows.values()) + list(rr.values()) if r["metadata"]["label"] in ("fs+", "fs-")}),
      SB + " + " + SR + " distinct recipient contexts")
m.add("ceilFirstTask", rows["baseline_fs"]["metadata"]["task_id"].split("/")[1][:8], SB + " baseline_fs metadata.task_id")
SM = "data/pod_astra/merge/STATIC_RESULTS.json"
res = {r["name"]: r["groups"] for r in load("pod_astra/merge/STATIC_RESULTS.json")["results"]}
for tag, name in [("CuaOrig", "Holo-3.1-4B"), ("Cua", "merge_cua_b050"), ("CuaQ", "merge_cua_b025"), ("Fara", "merge_fara_b050")]:
    g = res[name]
    m.add(f"merge{tag}Fsp", f"{g['fs+']['answer']}/{g['fs+']['n']}", SM + f" {name} fs+ answer")
    m.add(f"merge{tag}Fsm", f"{g['fs-']['answer']}/{g['fs-']['n']}", SM + f" {name} fs- answer")
    m.add(f"merge{tag}Healthy", f"{g['healthy']['valid_nonanswer']}/{g['healthy']['n']}", SM + f" {name} healthy valid_nonanswer")
    m.add(f"merge{tag}Inv", sum(g[k]["invalid"] for k in g), SM + f" {name} invalid, all strata")
VM = "data/pod_astra/merge/"
for tag, f in [("Cua", "VERIFY_CUA_B050.json"), ("CuaQ", "VERIFY_CUA_B025.json"), ("Fara", "VERIFY_FARA_B050.json")]:
    v = load("pod_astra/merge/" + f)
    m.add(f"merge{tag}Unchanged", v["language_formula_verified"] - v["physically_changed"], VM + f + " language_formula_verified - physically_changed")
    m.add(f"merge{tag}LangTensors", v["language_formula_verified"], VM + f + " language_formula_verified")
rep = (DATA / "pod_astra/merge/REPORT_orbit.md").read_text()
tau = float(re.search(r"L2\(donor-Qwen\)=([0-9.]+)", rep).group(1))
act = float(re.search(r"actual update L2=([0-9]+\.[0-9]+)", rep).group(1))
m.add("mergeCuaIntendedNorm", f"{0.5 * tau:.2f}", VM + "REPORT_orbit.md: 0.5 * L2(donor-Qwen), language layers")
m.add("mergeCuaActualNorm", f"{act:.2f}", VM + "REPORT_orbit.md: actual update L2 after BF16 rounding (beta 0.5)")
SE = "data/pod_astra/broad/"
def strata(arm):
    c, per = {}, {}
    for k, v in load(f"pod_astra/broad/{arm}/summary.json")["per_row"].items():
        _, lab, ctx = k.split(" | ")
        c.setdefault(lab, {"answer": 0, "valid_nonanswer": 0, "invalid": 0, "n": 0})
        for f in c[lab]:
            c[lab][f] += v[f]
        per[ctx] = v
    return c, per
for tag, arm in [("Orig", "eval_original"), ("Edit", "eval_p100"), ("Rand", "eval_random100"), ("Half", "eval_p050")]:
    c, per = strata(arm)
    m.add(f"alpha{tag}Fsp", f"{c['fs+']['answer']}/{c['fs+']['n']}", SE + arm + "/summary.json fs+ answer")
    m.add(f"alpha{tag}Fsm", f"{c['fs-']['answer']}/{c['fs-']['n']}", SE + arm + "/summary.json fs- answer")
    m.add(f"alpha{tag}Healthy", f"{c['healthy']['valid_nonanswer']}/{c['healthy']['n']}", SE + arm + "/summary.json healthy valid_nonanswer")
    m.add(f"alpha{tag}Inv", sum(x["invalid"] for x in c.values()), SE + arm + "/summary.json invalid")
    fsp = sorted((k, v) for k, v in per.items() if k.startswith(("libreoffice_calc", "multi_apps/b337")))
    for j, (k, v) in enumerate(fsp):
        m.add(f"alpha{tag}FspCtx{'AB'[j]}", f"{v['answer']}/{v['n']}", SE + arm + f"/summary.json per_row fs+ {k}")
st = load("pod_astra/broad/derive_residual.json")["stats"]
m.add("alphaNWriters", len({(x["layer"], x["kind"]) for x in st}), SE + "derive_residual.json stats (layer, kind) pairs")
m.add("alphaLayers", f"{min(x['layer'] for x in st)}--{max(x['layer'] for x in st)}", SE + "derive_residual.json stats layers")
SA = "data/pod_astra/broad/anchoring.jsonl"
an = {}
for line in (DATA / "pod_astra/broad/anchoring.jsonl").read_text().splitlines():
    r = json.loads(line)
    an[r["name"]] = r["answer_margin"]
for c, C_ in [("fs_0", "A"), ("fs_1", "B")]:
    for k, K in [("original", "Orig"), ("reason_only", "Reason"), ("json_only", "Json"), ("reason_and_json", "Both")]:
        m.add(f"anc{C_}{K}", f"{an[f'{c}_{k}']:+.1f}".replace("-", "$-$"), SA + f" {c}_{k}.answer_margin")
assert an["fs_0_original"] == mg["baseline_fs"]
for c, C_, donor in [("fs_0", "A", mg["baseline_donor"]), ("fs_1", "B", mr["baseline_donor_1"])]:
    m.add(f"anc{C_}Screen", f"{an[f'{c}_reason_and_json'] - donor:.1f}", SA + f" {c}_reason_and_json minus donor margin (screen and history)")
pj = load("pod_astra/broad/projection_summary.json")["outcomes"]
r1 = next(o for o in pj if o["rank"] == 1 and o["dose"] == 1.0)["margins"]
for k, K in [("fs_0", "FspA"), ("fs_1", "FspB"), ("preserve_0", "TrueA"), ("preserve_1", "TrueB")]:
    m.add(f"projOne{K}", f"{r1[k]:+.1f}", "data/pod_astra/broad/projection_summary.json rank 1 dose 1 margins." + k)
r0 = next(o for o in pj if o["rank"] == 0)["margins"]
m.add("projZeroTrueB", f"{r0['preserve_1']:+.1f}", "data/pod_astra/broad/projection_summary.json rank 0 margins.preserve_1")
m.write()

plt = setup_mpl()
groups = [("a  fs+ context 1: infeasible task\n(answer is the correct tool)", [
              (mg["baseline_fs"], "recorded step", C["red"]), (mg["baseline_donor"], "donor: previous step (a click)", C["green"]),
              (mg["mlp_early"], "MLPs 0–11", C["grey"]), (mg["mlp_middle"], "MLPs 12–23", C["grey"]),
              (mg["mlp_late"], "MLPs 24–31", C["grey"]), (mg["mlp_all"], "MLPs, all layers", C["grey"]),
              (mg["mlp+mixer_early"], "MLPs + mixers 0–11", C["blue"]), (mg["mlp+mixer_middle"], "MLPs + mixers 12–23", C["blue"]),
              (mr["resume_mlp+mixer_late"], "MLPs + mixers 24–31", C["blue"])]),
          ("b  fs+ context 2: false completion", [
              (mr["baseline_fs_1"], "recorded step", C["red"]), (mr["baseline_donor_1"], "donor: previous step", C["green"]),
              (mr["second_fs_mlp_all"], "MLPs, all layers", C["grey"]), (mr["second_fs_mlp+mixer_middle"], "MLPs + mixers 12–23", C["blue"])]),
          ("c  true completion\n(donor from another task)", [
              (mr["baseline_true_finish"], "recorded step", C["red"]), (mr["true_finish_mlp+mixer_middle"], "MLPs + mixers 12–23", C["blue"])])]
fig, axs = plt.subplots(1, 3, figsize=(7.0, 2.3), gridspec_kw={"width_ratios": [1.0, 1.0, 1.0], "wspace": 0.9})
for ax, (title, bars) in zip(axs, groups):
    for i, (v, lab, col) in enumerate(bars):
        ax.barh(i, v, color=col, height=0.7)
        ax.text(v + (0.8 if v >= 0 else -0.8), i, f"{v:+.1f}", va="center", ha="left" if v >= 0 else "right", fontsize=5.6)
    ax.axvline(0, color="black", lw=0.8)
    ax.set_yticks(range(len(bars)), [b[1] for b in bars], fontsize=5.8)
    ax.set_ylim(8.6, -0.6)
    ax.set_xlim(-30, 30)
    ax.set_title(title, fontsize=6.4, loc="left")
axs[1].set_xlabel("margin of answer over the best GUI tool, logits (below 0: the next tool token flips)")
fig.savefig(FIGS / "ceiling.pdf")
print("broad ok", mg)
