"""Isolated grounding test: one click per screenshot, target bbox known from the DOM.
Varies: image scale, crop to the MiniWoB area, prompt (agent tools vs H's element-localization prompt)."""
import holo.settings as S
import json, re, sys
import numpy as np
from PIL import Image
from holo.model import Holo
from holo.agent import make_env, TOOLS, SYSTEM_PROMPT, obs_message, parse

LOC_PROMPT = ('Localize an element on the GUI image according to the provided target and output a click position.\n'
              ' * You must output a valid JSON following the format: {"x": int 0..1000, "y": int 0..1000}\n Your target is:\n{T}')

holo = Holo()
cases = []
for seed in range(200, 212):
    env = make_env("click-button")
    obs, _ = env.reset(seed=seed)
    page = env.unwrapped.page
    sf = page._bgym_scale_factor
    target = re.findall(r'"(.*?)"', obs["goal"])[0]
    bb = page.evaluate("(t)=>{for(const b of document.querySelectorAll('#area button')){if(b.textContent.trim()===t){const r=b.getBoundingClientRect();return [r.x,r.y,r.width,r.height]}}return null}", target)
    area = page.evaluate("()=>{const r=document.querySelector('#wrap').getBoundingClientRect();return [r.x,r.y,r.width,r.height]}")
    cases.append((obs["goal"], target, Image.fromarray(obs["screenshot"]), [v * sf for v in bb], [v * sf for v in area]))
    env.close()

def run(cfg):
    hits = []
    for goal, target, img, bb, area in cases:
        x0, y0 = 0, 0
        im = img
        if cfg["crop"]:
            x0, y0 = int(area[0]), int(area[1])
            im = img.crop((x0, y0, int(area[0] + area[2]), int(area[1] + area[3])))
        W, H = im.size
        im = im.resize((int(W * cfg["scale"]), int(H * cfg["scale"])), Image.LANCZOS)
        if cfg["prompt"] == "agent":
            msgs = [{"role": "system", "content": SYSTEM_PROMPT}, {"role": "user", "content": goal}, obs_message(im)]
            g = holo.generate(msgs, TOOLS, capture=False, seed=0)
            _, _, call = parse(g["text"])
            xy = (call["arguments"].get("x"), call["arguments"].get("y")) if call and call["name"] == "click" else None
        else:
            msgs = [{"role": "user", "content": [{"type": "image", "image": im}, {"type": "text", "text": LOC_PROMPT.replace("{T}", f'the "{target}" button')}]}]
            g = holo.generate(msgs, None, capture=False, seed=0)
            m = re.search(r'"x"\s*:\s*(\d+).*?"y"\s*:\s*(\d+)', g["text"], re.S)
            xy = (int(m.group(1)), int(m.group(2))) if m else None
        ok = False
        if xy and None not in xy:
            px, py = x0 + xy[0] / 1000 * W, y0 + xy[1] / 1000 * H
            ok = bb[0] <= px <= bb[0] + bb[2] and bb[1] <= py <= bb[1] + bb[3]
        hits.append(ok)
    return float(np.mean(hits)), g["gen_s"]

for cfg in [dict(prompt="agent", crop=True, scale=3), dict(prompt="agent", crop=True, scale=5)]:
    print(json.dumps(cfg), "hit_rate=%.2f last_gen_s=%.1f" % run(cfg), flush=True)
