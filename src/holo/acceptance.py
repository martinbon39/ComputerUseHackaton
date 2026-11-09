"""Phase-1 acceptance test: easy tasks, success rate must be > 70 %."""
import holo.settings as S
import argparse, json
import numpy as np
from holo.model import Holo
from holo.agent import run_episode

ap = argparse.ArgumentParser()
ap.add_argument("--think", type=int, default=0)
ap.add_argument("--upscale", type=float, default=5.0)
ap.add_argument("--seeds", type=int, default=4)
ap.add_argument("--tag", default="accept")
a = ap.parse_args()
holo = Holo()
res = []
for task in ["click-button", "click-link", "enter-text"]:
    for seed in range(100, 100 + a.seeds):
        d = S.RUNS_DIR / a.tag / f"{task}_s{seed}_t{a.think}_u{a.upscale}"
        s = run_episode(holo, task, seed, d, enable_thinking=bool(a.think), upscale=a.upscale, max_steps=6)
        res.append(s)
        print(task, seed, "R=", s["reward"], "steps", s["n_steps"], "claimed", s["claimed_done"], "gen", s["gen_s_mean"], s["error"] and s["error"][:200], flush=True)
sr = np.mean([r["reward"] > 0 for r in res])
print(json.dumps({"think": a.think, "upscale": a.upscale, "n": len(res), "success": round(float(sr), 3),
                  "gen_s_mean": round(float(np.mean([r["gen_s_mean"] or 0 for r in res])), 2)}))
