#!/workspace/venv/bin/python
import os

os.environ.update(OMP_NUM_THREADS="2", MKL_NUM_THREADS="2", OPENBLAS_NUM_THREADS="2")

import hashlib
import json
import math
import sys
from pathlib import Path

import torch
from safetensors import safe_open

torch.set_num_threads(2)

HOLO = Path("/workspace/hf/hub/models--Hcompany--Holo-3.1-4B/snapshots/8c88265a5a159bfd1492db9243733dd2e6e04a6e")
QWEN = Path("/root/expo/base")
CUA = Path("/dev/shm/astra_merge_cua")
OUT_ROOT = Path("/dev/shm/moon-vision")
WORK_CANDIDATES = (Path("/workspace/astra/moon-vision"), Path("/dev/shm/moon-vision"))


def read_json(path):
    return json.loads(path.read_text())


def file_sha(path):
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(8 << 20), b""):
            digest.update(block)
    return digest.hexdigest()


def tensor_sha(tensor):
    raw = tensor.detach().cpu().contiguous().view(torch.uint8).numpy().tobytes()
    return hashlib.sha256(raw).hexdigest()


class Weights:
    def __init__(self, path):
        self.path = Path(path)
        self.index = read_json(self.path / "model.safetensors.index.json")
        self.weight_map = self.index["weight_map"]
        self.files = {
            name: safe_open(str(self.path / name), framework="pt", device="cpu")
            for name in sorted(set(self.weight_map.values()))
        }
        keys = set().union(*(set(handle.keys()) for handle in self.files.values()))
        assert keys == set(self.weight_map), f"{self.path}: key union differs from index"

    def get(self, key):
        return self.files[self.weight_map[key]].get_tensor(key)


def assert_finite(tensor, label):
    if tensor.is_floating_point():
        assert bool(torch.isfinite(tensor).all()), f"nonfinite tensor: {label}"


def raw_equal(left, right):
    return torch.equal(
        left.detach().cpu().contiguous().view(torch.uint8),
        right.detach().cpu().contiguous().view(torch.uint8),
    )


def source_provenance():
    candidates = [p / "source_provenance.json" for p in WORK_CANDIDATES]
    manifest_path = next((p for p in candidates if p.exists()), None)
    assert manifest_path is not None, "source_provenance.json is missing"
    recorded = read_json(manifest_path)
    expected_paths = {str(HOLO), str(QWEN), str(CUA)}
    assert set(recorded) == expected_paths, "source provenance paths differ"
    for source_path, records in recorded.items():
        for name, expected in records.items():
            actual_path = Path(source_path) / name
            assert actual_path.is_file(), f"missing source file: {actual_path}"
            actual = {"sha256": file_sha(actual_path), "bytes": actual_path.stat().st_size}
            assert actual == expected, f"source changed: {actual_path}"
    return manifest_path, recorded


def expected_sidecars():
    return {
        source.name
        for source in HOLO.iterdir()
        if source.is_file() and source.suffix != ".safetensors" and source.name not in {"README.md", "latest"}
    }


def verify_checkpoint(label, coefficient, source_manifest):
    output_path = OUT_ROOT / label
    assert output_path.is_dir(), f"missing checkpoint: {output_path}"
    output_config = read_json(output_path / "config.json")
    holo_config = read_json(HOLO / "config.json")
    output_index = read_json(output_path / "model.safetensors.index.json")
    holo_index = read_json(HOLO / "model.safetensors.index.json")
    assert output_config == holo_config, "config.json differs from Holo"
    assert output_index == holo_index, "model.safetensors.index.json differs from Holo"

    weight_map = output_index["weight_map"]
    assert len(weight_map) == 724, f"expected 724 tensors, got {len(weight_map)}"
    visual_keys = sorted(key for key in weight_map if key.startswith("model.visual."))
    assert len(visual_keys) == 297, f"expected 297 visual tensors, got {len(visual_keys)}"
    assert any(key.startswith("model.visual.merger.") for key in visual_keys), "merger tensors absent"
    nonvisual_keys = sorted(set(weight_map) - set(visual_keys))
    assert len(nonvisual_keys) == 427, f"expected 427 nonvisual tensors, got {len(nonvisual_keys)}"

    holo = Weights(HOLO)
    qwen = Weights(QWEN)
    cua = Weights(CUA)
    output = Weights(output_path)
    assert output.weight_map == holo.weight_map, "output map differs from Holo"

    manifest = read_json(output_path / "vision_manifest.json")
    assert manifest["coefficient"] == coefficient
    assert manifest["donor"] == str(CUA)
    assert manifest["reference"] == str(QWEN)
    assert manifest["holo"] == str(HOLO)
    assert manifest["total_tensors"] == 724
    assert manifest["selected_tensors"] == 297
    assert manifest["source_provenance"] == source_manifest
    assert len(manifest["per_tensor"]) == 724

    expected_files = expected_sidecars() | set(weight_map.values())
    actual_files = {path.name for path in output_path.iterdir() if path.is_file()}
    assert actual_files == expected_files | {"vision_manifest.json"}, "output file set differs"
    for name, expected in manifest["files"].items():
        path = output_path / name
        assert path.is_file(), f"manifest file missing: {path}"
        actual = {"bytes": path.stat().st_size, "sha256": file_sha(path)}
        assert actual == expected, f"output file hash mismatch: {path}"
        if name in expected_sidecars():
            source = HOLO / name
            assert actual == {"bytes": source.stat().st_size, "sha256": file_sha(source)}, f"sidecar differs from Holo: {name}"
    assert set(manifest["files"]) == expected_files, "manifest file set differs"

    changed_elements = 0
    update_l2_squared = 0.0
    served_changed_elements = 0
    served_l2_squared = 0.0
    selected_count = 0
    nonvisual_count = 0
    for key in sorted(weight_map):
        original = holo.get(key)
        actual = output.get(key)
        assert actual.dtype == original.dtype and actual.shape == original.shape, f"shape/dtype: {key}"
        assert_finite(original, f"Holo:{key}")
        assert_finite(actual, f"output:{key}")
        row = manifest["per_tensor"][key]
        assert row["selected"] == key.startswith("model.visual.")
        assert row["dtype"] == str(actual.dtype)
        assert row["original_sha256"] == tensor_sha(original)
        assert row["output_sha256"] == tensor_sha(actual)
        if key.startswith("model.visual."):
            selected_count += 1
            donor = cua.get(key)
            reference = qwen.get(key)
            assert donor.shape == original.shape and reference.shape == original.shape, f"input shape: {key}"
            assert_finite(donor, f"CUA:{key}")
            assert_finite(reference, f"Qwen:{key}")
            expected = (original.float() + coefficient * (donor.float() - reference.float())).to(original.dtype)
            assert raw_equal(actual, expected), f"formula bytes differ: {key}"
            delta = actual.float() - original.float()
            changed_elements += int(torch.count_nonzero(delta).item())
            update_l2_squared += float(delta.square().sum(dtype=torch.float64).item())
            original_bf16 = original.to(torch.bfloat16)
            actual_bf16 = actual.to(torch.bfloat16)
            served_delta = actual_bf16.float() - original_bf16.float()
            served_changed_elements += int(torch.count_nonzero(served_delta).item())
            served_l2_squared += float(served_delta.square().sum(dtype=torch.float64).item())
        else:
            nonvisual_count += 1
            assert raw_equal(actual, original), f"nonvisual tensor changed: {key}"

    assert selected_count == 297 and nonvisual_count == 427
    assert manifest["changed_elements"] == changed_elements
    assert math.isclose(manifest["update_l2"], math.sqrt(update_l2_squared), rel_tol=1e-6, abs_tol=1e-9)
    return {
        "path": str(output_path),
        "coefficient": coefficient,
        "status": "PASS",
        "total_tensors": 724,
        "selected_tensors": selected_count,
        "nonvisual_tensors": nonvisual_count,
        "changed_elements": changed_elements,
        "update_l2": math.sqrt(update_l2_squared),
        "bf16_serving_changed_elements": served_changed_elements,
        "bf16_serving_update_l2": math.sqrt(served_l2_squared),
    }


def main():
    source_manifest_path, source_manifest = source_provenance()
    checks = {"source_manifest": str(source_manifest_path), "checkpoints": []}
    failures = []
    for label, coefficient in (("cua_b050", 0.5), ("cua_b100", 1.0)):
        try:
            checks["checkpoints"].append(verify_checkpoint(label, coefficient, source_manifest))
        except Exception as error:
            checks["checkpoints"].append({"path": str(OUT_ROOT / label), "status": "FAIL", "error": repr(error)})
            failures.append(label)
    checks["status"] = "FAIL" if failures else "PASS"
    checks["failures"] = failures
    destination = next((p / "VERIFY_CHECKPOINTS.json" for p in WORK_CANDIDATES if (p / "source_provenance.json").exists()), WORK_CANDIDATES[0] / "VERIFY_CHECKPOINTS.json")
    temporary = destination.with_suffix(destination.suffix + ".tmp")
    temporary.write_text(json.dumps(checks, indent=2) + "\n")
    temporary.replace(destination)
    print(json.dumps(checks, indent=2))
    if failures:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
