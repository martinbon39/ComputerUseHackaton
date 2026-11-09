"""Build linkedin_anim.html: a self-contained, deterministic 25 s animation (render(t), TOTAL) for a LinkedIn post.

Data: the 14 matched false/true completion pairs of the imminent-completion analysis
(paper/data/pod_astra/perceive/descriptive_v2.json, paper section "perceive", Fig. perceive b).
"""
import base64
import json
from pathlib import Path

H = Path(__file__).parent
SRC = H.parent / "paper/data/pod_astra/perceive/descriptive_v2.json"
LAYER = 15

desc = json.loads(SRC.read_text())
summary = next(s for s in desc["summary"] if s["layer"] == LAYER)
pairs = []
for row in desc["rows"]:
    pairs.append({
        "match": row["match"],
        "false": {k: [round(v, 4) for v in row["fs_plus"][k]] for k in ("previous_z", "terminal_z")},
        "true": {k: [round(v, 4) for v in row["fs_minus"][k]] for k in ("previous_z", "terminal_z")},
    })
data = {
    "source": "holo-neurochir/paper/data/pod_astra/perceive/descriptive_v2.json",
    "layer": LAYER,
    "n_pairs": summary["n"],
    "false_above_true_fraction": summary["matched_terminal_fs_plus_gt_fs_minus"],
    "terminal_gap_z": summary["matched_terminal_fs_plus_minus_fs_minus"],
    "pairs": pairs,
}
assert len(pairs) == summary["n"] == 14

def vendored(name):
    return (H / "vendor" / name).read_text().replace("</script", "<\\/script")


core = vendored("three-0.185.1.core.min.js")
three = vendored("three-0.185.1.module.min.js").replace('"./three.core.min.js"', '"three-core"')
assert '"three-core"' in three
font = base64.b64encode((H / "vendor/GeistMono-Regular.ttf").read_bytes()).decode()
app = (H / "app.js").read_text()
css = (H / "style.css").read_text().replace("__FONT__", font)

page = f"""<!doctype html><html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>Not Inside</title>
<style>{css}</style></head><body>
<div id="stage">
<canvas id="gl" aria-label="Holo-3.1-4B as 32 layers. At layer 15, true and false 'done' steps of the agent rise together and overlap."></canvas>
<svg id="finder" viewBox="0 0 1080 1350" aria-hidden="true"></svg>
<div class="cap" id="c1">Where does an AI agent<br>know it's wrong?</div>
<div class="cap low" id="c2"><span class="t">true “done”</span> <span class="vs">vs</span> <span class="f">false “done”</span></div>
<div class="cap low big" id="c3">Not inside.</div>
<div class="cap low" id="c4">It takes an outside check.</div>
<div class="cap end" id="c5"><span class="title">Cogito, Ergo Feci</span><span class="doi">Holo-3.1-4B · doi 10.5281/zenodo.24061167</span></div>
</div>
<script type="application/json" id="data">{json.dumps(data)}</script>
<script type="text/plain" id="three-core">{core}</script>
<script type="text/plain" id="three-src">{three}</script>
<script>(function(){{var u=function(id){{return URL.createObjectURL(new Blob([document.getElementById(id).textContent],{{type:'text/javascript'}}))}};var im=document.createElement('script');im.type='importmap';im.textContent=JSON.stringify({{imports:{{'three-core':u('three-core'),three:u('three-src')}}}});document.currentScript.after(im);}})();</script>
<script type="module">{app}</script>
</body></html>"""
(H / "linkedin_anim.html").write_text(page)
print("ok", len(page))
