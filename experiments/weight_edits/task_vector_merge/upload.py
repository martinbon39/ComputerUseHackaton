import os
os.environ.update(OMP_NUM_THREADS="2", MKL_NUM_THREADS="2", OPENBLAS_NUM_THREADS="2")
import torch
torch.set_num_threads(2)
import argparse
import json
import subprocess
import time
from pathlib import Path

p = argparse.ArgumentParser()
p.add_argument("checkpoint")
p.add_argument("name")
p.add_argument("account", choices=["1", "2"])
p.add_argument("record")
a = p.parse_args()
checkpoint = Path(a.checkpoint)
manifest = json.loads((checkpoint / "merge_manifest.json").read_text())
assert a.name == checkpoint.name
assert all((checkpoint / f).stat().st_size == info["bytes"] for f, info in manifest["files"].items())
start = time.time()
completed = subprocess.run(["bash", "/workspace/modal_put_ckpt.sh", str(checkpoint), a.name, a.account], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=False)
record = {"name": a.name, "account": int(a.account), "checkpoint": str(checkpoint), "destination": f"holo-models:/ckpt/{a.name}", "exit_code": completed.returncode, "seconds": time.time()-start, "completed_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()), "files": manifest["files"], "client_output": "discarded before storage"}
Path(a.record).write_text(json.dumps(record, indent=2)+"\n")
print(json.dumps({k:v for k,v in record.items() if k != "files"}), flush=True)
raise SystemExit(completed.returncode)
