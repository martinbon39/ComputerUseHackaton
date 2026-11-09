import os
os.environ.update(OMP_NUM_THREADS="2", MKL_NUM_THREADS="2", OPENBLAS_NUM_THREADS="2")
import torch
torch.set_num_threads(2)
import argparse
import hashlib
import json
import math
import shutil
from pathlib import Path
from safetensors import safe_open
from safetensors.torch import save_file

HOLO = "/workspace/hf/hub/models--Hcompany--Holo-3.1-4B/snapshots/8c88265a5a159bfd1492db9243733dd2e6e04a6e"
QWEN = "/root/expo/base"
CUA = "/dev/shm/astra_merge_cua"


def sha(path):
    digest = hashlib.sha256()
    with open(path, "rb") as stream:
        for block in iter(lambda: stream.read(8 << 20), b""):
            digest.update(block)
    return digest.hexdigest()


def tensor_sha(tensor):
    return hashlib.sha256(tensor.contiguous().view(torch.uint8).numpy().tobytes()).hexdigest()


def write_json(path, value):
    temp = path.with_suffix(path.suffix + ".tmp")
    temp.write_text(json.dumps(value, indent=2) + "\n")
    temp.replace(path)


class Weights:
    def __init__(self, path):
        self.path = Path(path)
        self.config = json.loads((self.path / "config.json").read_text())
        self.index = json.loads((self.path / "model.safetensors.index.json").read_text())
        self.wm = self.index["weight_map"]
        self.files = {name: safe_open(str(self.path / name), framework="pt", device="cpu") for name in set(self.wm.values())}
        assert set().union(*(set(f.keys()) for f in self.files.values())) == set(self.wm)
        for key, filename in self.wm.items():
            assert key in self.files[filename].keys()

    def get(self, key):
        return self.files[self.wm[key]].get_tensor(key)

    def provenance(self):
        return {name: {"sha256": sha(self.path / name), "bytes": (self.path / name).stat().st_size} for name in sorted(set(self.wm.values()) | {"config.json", "model.safetensors.index.json"})}


def compatible(models):
    ignored = {"dtype", "torch_dtype", "model_type", "transformers_version"}
    configs = [{k: v for k, v in model.config["vision_config"].items() if k not in ignored} for model in models]
    assert all(c == configs[0] for c in configs)
    keys = sorted(k for k in models[0].wm if k.startswith("model.visual."))
    assert len(keys) == 297 and any(k.startswith("model.visual.merger.") for k in keys)
    for model in models:
        assert sorted(k for k in model.wm if k.startswith("model.visual.")) == keys
        assert model.config["vision_config"]["model_type"] in {"qwen3_5", "qwen3_5_vision"}
    for key in keys:
        tensors = [model.get(key) for model in models]
        assert all(t.shape == tensors[0].shape for t in tensors)
        assert all(t.is_floating_point() and torch.isfinite(t).all() for t in tensors)
    return keys


def measure(models, keys):
    rows = {}
    for key in keys:
        h, q, d = [m.get(key) for m in models]
        dq, hq = d.float() - q.float(), h.float() - q.float()
        rows[key] = {"shape": list(h.shape), "numel": h.numel(), "dtypes": [str(x.dtype) for x in [h, q, d]], "cua_qwen_l2_squared": dq.square().sum(dtype=torch.float64).item(), "holo_qwen_l2_squared": hq.square().sum(dtype=torch.float64).item(), "cua_qwen_nonzero": torch.count_nonzero(dq).item(), "holo_qwen_nonzero": torch.count_nonzero(hq).item(), "input_sha256": [tensor_sha(x) for x in [h, q, d]]}
    totals = {name: sum(r[name] for r in rows.values()) for name in ["numel", "cua_qwen_l2_squared", "holo_qwen_l2_squared", "cua_qwen_nonzero", "holo_qwen_nonzero"]}
    totals["cua_qwen_l2"] = math.sqrt(totals["cua_qwen_l2_squared"])
    totals["holo_qwen_l2"] = math.sqrt(totals["holo_qwen_l2_squared"])
    return {"totals": totals, "per_tensor": rows}


def build(h, q, donor, coefficient, out, source_provenance):
    out.mkdir(exist_ok=False)
    for source in sorted(h.path.iterdir()):
        if source.is_file() and source.suffix != ".safetensors" and source.name not in {"README.md", "latest"}:
            shutil.copyfile(source, out / source.name)
    for shard in sorted(set(h.wm.values())):
        tensors = {}
        for key in sorted(k for k, name in h.wm.items() if name == shard):
            original = h.get(key)
            edited = (original.float() + coefficient * (donor.get(key).float() - q.get(key).float())).to(original.dtype) if key.startswith("model.visual.") else original
            assert torch.isfinite(edited).all(), key
            tensors[key] = edited
        save_file(tensors, str(out / shard), metadata={"format": "pt"})
        del tensors
        print("saved", out / shard, flush=True)
    output = Weights(out)
    assert output.index == h.index and output.config == h.config
    rows = {}
    for key in sorted(h.wm):
        original, actual = h.get(key), output.get(key)
        selected = key.startswith("model.visual.")
        expected = (original.float() + coefficient * (donor.get(key).float() - q.get(key).float())).to(original.dtype) if selected else original
        assert actual.dtype == original.dtype and actual.shape == original.shape
        assert torch.equal(actual.view(torch.uint8), expected.view(torch.uint8)), key
        delta = actual.float() - original.float() if selected else None
        rows[key] = {"selected": selected, "shape": list(actual.shape), "dtype": str(actual.dtype), "original_sha256": tensor_sha(original), "output_sha256": tensor_sha(actual), "formula_bitexact": True, "changed_elements": torch.count_nonzero(delta).item() if selected else 0, "update_l2_squared": delta.square().sum(dtype=torch.float64).item() if selected else 0}
    files = {p.name: {"bytes": p.stat().st_size, "sha256": sha(p)} for p in sorted(out.iterdir()) if p.is_file()}
    manifest = {"holo": str(h.path), "reference": str(q.path), "donor": str(donor.path), "coefficient": coefficient, "formula": "cast_H_dtype(H.float32 + coefficient * (donor.float32 - Qwen.float32)), only model.visual.*; every other tensor bitwise Holo", "source_provenance": source_provenance, "files": files, "per_tensor": rows, "total_tensors": len(rows), "selected_tensors": sum(r["selected"] for r in rows.values()), "changed_tensors": sum(r["changed_elements"] > 0 for r in rows.values()), "changed_elements": sum(r["changed_elements"] for r in rows.values()), "update_l2": math.sqrt(sum(r["update_l2_squared"] for r in rows.values()))}
    assert manifest["selected_tensors"] == 297
    write_json(out / "vision_manifest.json", manifest)
    print("verified", out, manifest["changed_tensors"], manifest["update_l2"], flush=True)
    return {"path": str(out), "coefficient": coefficient, "manifest_sha256": sha(out / "vision_manifest.json")}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--work", required=True)
    parser.add_argument("--output-root", required=True)
    parser.add_argument("--measure-only", action="store_true")
    args = parser.parse_args()
    work = Path(args.work)
    models = [Weights(p) for p in [HOLO, QWEN, CUA]]
    keys = compatible(models)
    metrics = measure(models, keys)
    write_json(work / "vision_delta.json", metrics)
    print(json.dumps(metrics["totals"]), flush=True)
    use_cua = metrics["totals"]["cua_qwen_nonzero"] > 0
    if not use_cua:
        assert metrics["totals"]["holo_qwen_nonzero"] > 0, "Both adaptations are zero"
    if args.measure_only:
        return
    sources = {str(m.path): m.provenance() for m in models}
    write_json(work / "source_provenance.json", sources)
    root = Path(args.output_root)
    root.mkdir(exist_ok=False)
    donor = models[2] if use_cua else models[0]
    doses = [0.5, 1.0] if use_cua else [0.25, 0.5]
    outputs = []
    for dose in doses:
        label = ("cua_b" if use_cua else "holo_g") + f"{int(dose * 100):03d}"
        outputs.append(build(models[0], models[1], donor, dose, root / label, sources))
        write_json(work / "CHECKPOINTS.json", {"source": "cua" if use_cua else "holo", "outputs": outputs})
    for model in models:
        assert model.provenance() == sources[str(model.path)], "Source mutated during construction"
    print("COMPLETE", flush=True)


if __name__ == "__main__":
    main()
