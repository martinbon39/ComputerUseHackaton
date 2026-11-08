"""Gradient-free weight edits without a learned direction: ExPO and the Qwen post-training vector.

Sources:
  data/local/expo/probe_*.json     8 samples per completion step, vLLM, exact harness call (osworld/probe_expo.py)
  data/local/expo/EXPO_REPORT.md   lineage norms and cosine (holo-neurochir/report/EXPO_REPORT.md, section 2)
"""
import re

from common import DATA, Macros, load, write_table

m = Macros("expo")
S = "data/local/expo/"
ARMS = [("orig13", "Original (re-served)"), ("expo11", "ExPO $\\lambda=1.1$, language layers"),
        ("expo12", "ExPO $\\lambda=1.2$, language layers"), ("expo125", "ExPO $\\lambda=1.25$, language layers"),
        ("expo150", "ExPO $\\lambda=1.5$, language layers"), ("attn15", "ExPO $\\lambda=1.5$, attention only"),
        ("mlp15", "ExPO $\\lambda=1.5$, MLP only"), ("rv05", "Holo $+\\,0.5\\,$(Qwen3.5-4B $-$ Base)")]
rows, fsp_all = [], []
for tag, lab in ARMS:
    d = load(f"local/expo/probe_{tag}.json")
    fp = fm = inv = n = 0
    for t, v in d["tasks"].items():
        a = sum(s["tool"] == "answer" for s in v["samples"])
        n += len(v["samples"])
        inv += sum((not s["valid_json"]) or s["finish"] != "stop" for s in v["samples"])
        if v["score"] == 0:
            fp += a
            nfp = len(v["samples"]) * sum(1 for x in d["tasks"].values() if x["score"] == 0)
        else:
            fm += a
            nfm = len(v["samples"]) * sum(1 for x in d["tasks"].values() if x["score"] != 0)
    rows.append(f"{lab} & {fp}/{nfp} & {fm}/{nfm} & {inv}/{n} \\\\ % source: {S}probe_{tag}.json")
    if tag != "orig13":
        fsp_all.append(fp)
    else:
        m.add("expoOrigFsp", f"{fp}/{nfp}", S + "probe_orig13.json fs+ answers")
write_table("expo", "\\begin{tabular}{lccc}\n\\toprule\nEdit (no gradient, no data) & fs+ \\texttt{answer} & fs$-$ \\texttt{answer} & invalid/truncated \\\\\n\\midrule\n"
            + rows[0] + "\n\\midrule\n" + "\n".join(rows[1:]) + "\n\\bottomrule\n\\end{tabular}\n", "expo")
m.add("expoN", len(ARMS) - 1, S + "probe_*.json arms excluding the original")
m.add("expoFspMin", min(fsp_all), S + "probe_*.json min fs+ answers over edited arms")

rep = (DATA / "local/expo/EXPO_REPORT.md").read_text()


def num(pattern):
    return re.search(pattern, rep).group(1).replace(",", ".")


m.add("linHoloQ", num(r"‖Holo − Q4B‖ \| \*\*([0-9,]+) %"), S + "EXPO_REPORT.md section 2, ||Holo - Q4B||/||Holo||")
m.add("linHoloBase", num(r"‖Holo − Q4B-Base‖ \| \*\*([0-9,]+) %"), S + "EXPO_REPORT.md section 2")
m.add("linQBase", num(r"‖Q4B − Q4B-Base‖ \| \*\*([0-9,]+) %"), S + "EXPO_REPORT.md section 2")
m.add("linCos", num(r"Q4B − Q4B-Base\) = \*\*(−?[0-9,]+)\*\*").replace("−", "$-$"), S + "EXPO_REPORT.md section 2 cosine")
m.write()
print("expo ok", fsp_all)
