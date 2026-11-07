"""Benchmark one generate step on replayed real contexts (same lengths as the rollouts).
Usage: HOLO_MODEL=... python scripts/bench_gen.py <runs_dir> [--no-fla]"""
import sys, time
if "--no-fla" in sys.argv:
    # make transformers believe FLA / causal-conv1d are absent -> pure PyTorch path
    import transformers.utils.import_utils as iu
    for n in ("is_flash_linear_attention_available", "is_causal_conv1d_available"):
        if hasattr(iu, n):
            setattr(iu, n, lambda: False)
    sys.modules["fla"] = None; sys.modules["causal_conv1d"] = None
import holo.settings as S
import torch
from pathlib import Path
from holo.model import Holo
from holo.replay import rebuild_messages, load
from holo.agent import TOOLS

holo = Holo()
runs = [d for d in sorted(Path(sys.argv[1]).iterdir()) if (d / "steps.jsonl").exists()][:6]
ctxs = []
for d in runs:
    s, steps = load(d)
    for t in range(min(3, len(steps))):
        ctxs.append(rebuild_messages(d, t))
print("contexts", len(ctxs), flush=True)
for rep in range(2):
    ts = []
    for m in ctxs:
        torch.cuda.synchronize(); t0 = time.time()
        g = holo.generate(m, TOOLS, seed=0, max_new_tokens=64)
        torch.cuda.synchronize(); ts.append(time.time() - t0)
    print(f"pass{rep}: mean {sum(ts)/len(ts):.2f}s  max {max(ts):.2f}s  n_in~{g['n_in']}", flush=True)
# prefill only vs decode split on one long context
m = ctxs[-1]
inp = holo.build_inputs(m, TOOLS, False)
torch.cuda.synchronize(); t0 = time.time()
with torch.no_grad(): holo.model(**inp)
torch.cuda.synchronize(); print(f"prefill {inp['input_ids'].shape[1]} tok: {time.time()-t0:.2f}s", flush=True)
