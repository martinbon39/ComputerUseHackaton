import os
os.environ.update(OMP_NUM_THREADS="2", MKL_NUM_THREADS="2", OPENBLAS_NUM_THREADS="2")
import torch
torch.set_num_threads(2)
import argparse
import hashlib
import json
import runpy
import sys
from pathlib import Path

ROOT = Path("/home/orbit/projects/ComputerUseHackaton/holo-neurochir")
WORK = Path(__file__).resolve().parent
sys.path[:0] = [str(ROOT), str(ROOT / "osworld")]
from astra_cohort_probe import call, client_for, server_info
from holo.osw_replay import check_traj, rebuild, to_openai
from holo.osw_taxonomy import load_task

p = argparse.ArgumentParser()
p.add_argument("name")
p.add_argument("--mode", choices=["smoke", "full", "identity"], default="smoke")
p.add_argument("--url", default="https://martinbon39--holo-vllm-serve.us-east.modal.run/v1")
p.add_argument("--model")
a = p.parse_args()
frozen = json.loads((WORK / "probe_freeze.json").read_text())
for f, h in frozen["files"].items():
    assert hashlib.sha256(Path(f).read_bytes()).hexdigest() == h, f
os.environ["ASTRA_MERGE_AUTH"] = "Authorization: Bearer " + Path("/home/orbit/.holo_modal_key").read_text().strip()
client = client_for(a.url, "ASTRA_MERGE_AUTH")
models = client.with_options(timeout=45, max_retries=0).models.list().data
matches = [m for m in models if str(getattr(m, "root", "")).endswith("/" + a.name)]
if len(matches) != 1:
    raise RuntimeError({"expected_checkpoint": a.name, "observed": [{"id": m.id, "root": getattr(m, "root", None)} for m in models]})
model = a.model or matches[0].id
assert model == matches[0].id
print("IDENTITY", model, getattr(matches[0], "root", None), flush=True)
if a.mode == "identity":
    raise SystemExit(0)
out = WORK / (a.name + "_" + a.mode)
out.mkdir(exist_ok=False)
if a.mode == "full":
    sys.argv = [str(ROOT / "osworld/astra_cohort_probe.py"), str(WORK / "cohort.json"), "/home/orbit/osw/results_diag", str(out), "--server", f"{a.url}={model}=ASTRA_MERGE_AUTH", "--k", "8", "--label", a.name]
    runpy.run_path(str(ROOT / "osworld/astra_cohort_probe.py"), run_name="__main__")
else:
    co = json.loads((WORK / "cohort.json").read_text())
    rows = []
    for prompt in co["text_prompts"]:
        result = call(a.url, model, "ASTRA_MERGE_AUTH", [{"role": "user", "content": prompt}], 0, False)
        rows.append({"text_prompt": prompt, **result})
        (out / "smoke.json").write_text(json.dumps(rows, indent=2))
        if result.get("error") or result.get("truncated") or not result.get("content"):
            raise RuntimeError("text transport/length sanity failed")
    row = next(r for r in co["train"] if r["label"] == "healthy")
    d = Path("/home/orbit/osw/results_diag") / row["task_id"]
    _, _, steps = load_task(d)
    check_traj(d, steps)
    msgs = to_openai(rebuild(d, steps, (d / "system_prompt.txt").read_text(), row["t"]))
    result = call(a.url, model, "ASTRA_MERGE_AUTH", msgs, 0, True)
    rows.append({"row": row, **result})
    (out / "smoke.json").write_text(json.dumps(rows, indent=2))
    (out / "server.json").write_text(json.dumps(server_info(a.url, model, "ASTRA_MERGE_AUTH"), indent=2))
    if result.get("error") or result.get("truncated") or not result.get("valid_nonanswer"):
        raise RuntimeError("healthy structured sanity failed")
    print("SMOKE_COMPLETE", out, flush=True)
