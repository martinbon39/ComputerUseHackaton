#!/usr/bin/env python3
import argparse
import hashlib
import json
import math
import os
from pathlib import Path

os.environ.setdefault("OMP_NUM_THREADS", "2")
os.environ.setdefault("MKL_NUM_THREADS", "2")
os.environ.setdefault("OPENBLAS_NUM_THREADS", "2")

import torch
from safetensors import safe_open

torch.set_num_threads(2)


def digest(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for block in iter(lambda: f.read(8 << 20), b""):
            h.update(block)
    return h.hexdigest()


class Weights:
    def __init__(self, path):
        self.path = Path(path)
        self.index = json.loads((self.path / "model.safetensors.index.json").read_text())
        self.wm = self.index["weight_map"]
        self.handles = {
            name: safe_open(str(self.path / name), framework="pt", device="cpu")
            for name in set(self.wm.values())
        }

    def get(self, key):
        return self.handles[self.wm[key]].get_tensor(key)


def main():
    parser = argparse.ArgumentParser(description="Independent exact verifier for Astra arithmetic, TIES, and DARE merge candidates")
    parser.add_argument("checkpoint", type=Path)
    parser.add_argument("evidence", type=Path)
    args = parser.parse_args()

    out = args.checkpoint.resolve()
    manifest_path = out / "merge_manifest.json"
    manifest = json.loads(manifest_path.read_text())
    method = manifest["method"]
    if method not in {"arithmetic", "ties", "dare"}:
        raise ValueError(f"unsupported method: {method}")
    beta = float(manifest["beta"])
    density = float(manifest["density"])
    seed = int(manifest["seed"])
    layer_range = manifest.get("layer_range")
    if not torch.isfinite(torch.tensor(beta)):
        raise ValueError("non-finite beta")
    if not 0 < density <= 1:
        raise ValueError("density must be in (0, 1]")

    holo = Weights(manifest["holo"])
    reference = Weights(manifest["reference"])
    donors = [Weights(path) for path in manifest["donors"]]
    merged = Weights(out)
    if not donors:
        raise ValueError("no donors")
    if not isinstance(layer_range, list) or len(layer_range) != 2 or not all(type(value) is int for value in layer_range):
        raise ValueError("layer_range must be a two-integer half-open interval")
    layer_start, layer_stop = layer_range
    num_layers = int(json.loads((holo.path / "config.json").read_text())["text_config"]["num_hidden_layers"])
    if not 0 <= layer_start < layer_stop <= num_layers:
        raise ValueError("layer_range must be nonempty and within the language layer count")

    def layer_number(key):
        prefix = "model.language_model.layers."
        if not key.startswith(prefix):
            return None
        component = key[len(prefix):].split(".", 1)[0]
        if not component.isdigit():
            raise ValueError(f"malformed language layer key: {key}")
        return int(component)

    selected_keys = {
        key for key in holo.wm
        if (number := layer_number(key)) is not None and layer_start <= number < layer_stop
    }
    selected_layers = sorted({layer_number(key) for key in selected_keys})
    expected_layers = list(range(layer_start, layer_stop))
    if selected_layers != expected_layers:
        raise ValueError({"expected_selected_layers": expected_layers, "actual_selected_layers": selected_layers})

    assert merged.wm == holo.wm, "output weight_map differs from Holo"
    indexed_shards = set(merged.wm.values())
    disk_shards = {p.name for p in out.glob("*.safetensors")}
    assert indexed_shards == disk_shards, (indexed_shards - disk_shards, disk_shards - indexed_shards)
    serialized = {}
    for shard, handle in merged.handles.items():
        for key in handle.keys():
            assert key not in serialized, f"duplicate serialized key {key}"
            serialized[key] = shard
    assert serialized == merged.wm, "serialized keys/shards differ from index"

    selected_formula_verified = 0
    preserved_policy_verified = 0
    physically_changed = set()
    generator = torch.Generator(device="cpu").manual_seed(seed)
    ordered_keys = [
        key
        for shard in sorted(set(holo.wm.values()))
        for key in sorted(key for key, filename in holo.wm.items() if filename == shard)
    ]
    for i, key in enumerate(ordered_keys):
        original = holo.get(key)
        actual = merged.get(key)
        assert actual.shape == original.shape, (key, actual.shape, original.shape)
        assert actual.dtype == original.dtype, (key, actual.dtype, original.dtype)
        assert torch.isfinite(actual).all(), f"nonfinite {key}"
        if key in selected_keys:
            base = reference.get(key).float()
            deltas = [donor.get(key).float() - base for donor in donors]
            if method == "arithmetic":
                update = sum(deltas) / len(deltas)
            elif method == "ties":
                trimmed = []
                for delta in deltas:
                    count = max(1, math.ceil(delta.numel() * density))
                    mask = torch.zeros(delta.numel(), dtype=torch.bool)
                    mask[torch.topk(delta.abs().flatten(), count, sorted=False).indices] = True
                    trimmed.append(delta * mask.reshape(delta.shape))
                elected_sign = torch.stack(trimmed).sum(0).sign()
                aligned_sum = torch.zeros_like(base)
                aligned_count = torch.zeros_like(base)
                for delta in trimmed:
                    use = (delta.sign() == elected_sign) & (delta != 0)
                    aligned_sum += delta * use
                    aligned_count += use
                update = aligned_sum / aligned_count.clamp_min(1)
            else:
                update = sum(
                    delta * (torch.rand(delta.shape, generator=generator) < density) / density
                    for delta in deltas
                ) / len(deltas)
            expected = (original.float() + beta * update).to(original.dtype)
            assert torch.equal(actual, expected), f"formula mismatch {key}: max={torch.max(torch.abs(actual.float()-expected.float())).item()}"
            selected_formula_verified += 1
        else:
            assert torch.equal(actual, original), f"preservation mismatch {key}"
            preserved_policy_verified += 1
        if not torch.equal(actual, original):
            physically_changed.add(key)
        if i % 80 == 0:
            print("tensor", i, key, flush=True)

    assert set(manifest["changed_tensors"]) == physically_changed
    assert set(manifest["retained_tensors"]) == set(merged.wm) - physically_changed
    for name, metadata in manifest["files"].items():
        path = out / name
        assert path.is_file(), name
        assert path.stat().st_size == metadata["bytes"], name
        assert digest(path) == metadata["sha256"], name

    holo_path = holo.path
    expected_aux = {
        p.name for p in holo_path.iterdir()
        if p.is_file() and p.suffix != ".safetensors" and p.name not in {"README.md", "latest"}
    }
    actual_aux = {
        p.name for p in out.iterdir()
        if p.is_file() and p.suffix != ".safetensors" and p.name != "merge_manifest.json"
    }
    assert actual_aux == expected_aux, (expected_aux - actual_aux, actual_aux - expected_aux)
    for name in expected_aux:
        assert digest(out / name) == digest(holo_path / name), f"aux mismatch {name}"

    from transformers import AutoConfig, AutoProcessor
    config = AutoConfig.from_pretrained(str(out), local_files_only=True, trust_remote_code=True)
    processor = AutoProcessor.from_pretrained(str(out), local_files_only=True, trust_remote_code=True)
    checker_path = Path(__file__).resolve()
    evidence = {
        "verdict": "PASS",
        "checker": str(checker_path),
        "checker_sha256": digest(checker_path),
        "artifact": str(out),
        "manifest": str(manifest_path),
        "method": manifest["method"],
        "beta": beta,
        "density": density,
        "seed": seed,
        "layer_range": layer_range,
        "selected_layers": selected_layers,
        "donors": [str(d.path) for d in donors],
        "tensors": len(merged.wm),
        "selected_formula_verified": selected_formula_verified,
        "physically_changed": len(physically_changed),
        "preserved_policy_verified": preserved_policy_verified,
        "shards": len(indexed_shards),
        "aux": len(expected_aux),
        "config_class": type(config).__name__,
        "processor_class": type(processor).__name__,
        "full_model_allocation": "NOT RUN"
    }
    tmp = args.evidence.with_suffix(args.evidence.suffix + ".tmp")
    tmp.write_text(json.dumps(evidence, indent=2) + "\n")
    tmp.replace(args.evidence)
    print(json.dumps(evidence, indent=2))


if __name__ == "__main__":
    main()
