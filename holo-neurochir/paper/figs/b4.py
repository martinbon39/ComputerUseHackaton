"""Holo-3.1-4B: model geometry, label availability, original-behaviour pilot, and the [TO FILL] causal tables.

Sources:
  data/pod_hf/config_holo31_4B.json, config_holo31_0.8B.json   HF configs (revision in the copied path list)
  data/pod_astra/osw_shared_STATUS.json                         shared label status (admissible fs+/fs-)
  data/pod_astra/4b/runtime_status.json                         4B original-behaviour pilot (free generation)
The causal/surgery/held-out tables are placeholders until data/pod_astra/4b/<final files> exist.
"""
from common import Macros, load, write_table

m = Macros("b4")
for tag, f in [("Big", "pod_hf/config_holo31_4B.json"), ("Small", "pod_hf/config_holo31_0.8B.json")]:
    c = load(f)
    t = c["text_config"]
    S = "data/" + f
    m.add(f"cfg{tag}Layers", t["num_hidden_layers"], S + " text_config.num_hidden_layers")
    m.add(f"cfg{tag}Hidden", t["hidden_size"], S + " text_config.hidden_size")
    m.add(f"cfg{tag}Inter", t["intermediate_size"], S + " text_config.intermediate_size")
    m.add(f"cfg{tag}FullEvery", t["full_attention_interval"], S + " text_config.full_attention_interval")
    m.add(f"cfg{tag}VisDepth", c["vision_config"]["depth"], S + " vision_config.depth")
    m.add(f"cfg{tag}Tied", "tied" if c.get("tie_word_embeddings") else "untied", S + " tie_word_embeddings")

S = "data/pod_astra/osw_shared_STATUS.json"
st = load("pod_astra/osw_shared_STATUS.json")
m.add("bStatusUtc", st["updated_utc"], S + " updated_utc")
adm = st["admissible_total"]
m.add("bAdmFsPos", adm["fs+"], S + " admissible_total.fs+")
m.add("bAdmFsNeg", adm["fs-"], S + " admissible_total.fs-")
m.add("bGoFs", "false" if not st["go_fs"] else "true", S + " go_fs")
dg = st["passes"]["diag"]
m.add("bReplayFull", dg["n_replayed_full"], S + " passes.diag.n_replayed_full")
m.add("bReplayTail", dg["n_replayed_tail_only"], S + " passes.diag.n_replayed_tail_only")
m.add("bParseFail", dg["harness_events"]["parse_failed_3x"], S + " passes.diag.harness_events.parse_failed_3x")
m.add("bEnvFail", dg["harness_events"]["env_step_failed"], S + " passes.diag.harness_events.env_step_failed")

S = "data/pod_astra/4b/runtime_status.json"
rs = load("pod_astra/4b/runtime_status.json")
rows = []
for k, lab in [("fs+", "fs+ (false completion)"), ("fs-", "fs$-$ (true completion)"), ("healthy", "healthy (mid-episode)")]:
    v = rs["strata"][k]
    rows.append(f"{lab} & {v['n']} & {v['answer']} & {v['valid_nonanswer']} & {v['invalid_or_truncated']} \\\\")
write_table("b4_pilot", f"% source: {S}\n\\begin{{tabular}}{{lrrrr}}\n\\toprule\nStratum & Generations & \\texttt{{answer}} & Valid non-answer & Invalid/trunc. \\\\\n\\midrule\n"
            + "\n".join(rows) + "\n\\bottomrule\n\\end{tabular}\n", "b4")
m.add("bPilotN", rs["generated_outputs"], S + " generated_outputs")
m.add("bPilotFsAnswer", rs["strata"]["fs+"]["answer"], S + " strata.fs+.answer")
m.add("bPilotFsN", rs["strata"]["fs+"]["n"], S + " strata.fs+.n")
m.add("bPilotTrueAnswer", rs["strata"]["fs-"]["answer"], S + " strata.fs-.answer")
m.add("bPilotTrueN", rs["strata"]["fs-"]["n"], S + " strata.fs-.n")
m.add("bPilotHealthyAnswer", rs["strata"]["healthy"]["answer"], S + " strata.healthy.answer")
m.add("bPilotHealthyN", rs["strata"]["healthy"]["n"], S + " strata.healthy.n")
m.add("bCausalStatus", rs["causal_test"].replace("_", " "), S + " causal_test")

TF = r"\tofill{}"
write_table("b4_causal", "% PLACEHOLDER -- regenerate from the final 4B causal files (data/pod_astra/4b/...).\n"
            "\\begin{tabular}{lcccc}\n\\toprule\nArm & $P(\\texttt{answer}\\mid\\text{fs+})$ & $P(\\texttt{answer}\\mid\\text{fs}-)$ & HEALTH & Invalid \\\\\n\\midrule\n"
            + "\n".join(f"{a} & {TF} & {TF} & {TF} & {TF} \\\\" for a in
                        ["Original", "Random direction (matched norm)", "Steering, best layer", "Weight edit (compiled)"])
            + "\n\\bottomrule\n\\end{tabular}\n", "b4")
m.write()
print("b4 ok")
