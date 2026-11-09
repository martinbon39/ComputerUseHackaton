import os
os.environ.update(OMP_NUM_THREADS="2", MKL_NUM_THREADS="2", OPENBLAS_NUM_THREADS="2", TOKENIZERS_PARALLELISM="false", PYTHONDONTWRITEBYTECODE="1")
import torch
torch.set_num_threads(2)
import hashlib
import json
import sys
from pathlib import Path

sys.dont_write_bytecode = True
ROOT = Path(os.environ.get("REGMEAN_ROOT", "/dev/shm/astra-regmean"))
HOLO = Path("/workspace/hf/hub/models--Hcompany--Holo-3.1-4B/snapshots/8c88265a5a159bfd1492db9243733dd2e6e04a6e")
QWEN = Path("/root/expo/base")
CUA = Path("/dev/shm/astra_merge_cua")
BROAD = Path("/dev/shm/astra-broad")
BANNED = "chrome/480bcfea-d68f-4aaa-a0a9-2589ef319381"
os.environ.update(HOLO_MODEL=str(HOLO), HF_HOME="/workspace/hf", HF_HUB_OFFLINE="1", TRANSFORMERS_OFFLINE="1")


def sha(path):
    h = hashlib.sha256()
    with Path(path).open("rb") as f:
        for block in iter(lambda: f.read(8 * 1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def write_json(path, obj):
    Path(path).write_text(json.dumps(obj, indent=2, allow_nan=False) + "\n")


def writer_names():
    return [f"model.language_model.layers.{i}.{module}.weight"
            for i in range(12, 24)
            for module in ["mlp.down_proj", "self_attn.o_proj" if i % 4 == 3 else "linear_attn.out_proj"]]


def read_frozen():
    assert sha(ROOT / "manifest.json") == (ROOT / "manifest.sha256").read_text().strip()
    return json.loads((ROOT / "manifest.json").read_text())
