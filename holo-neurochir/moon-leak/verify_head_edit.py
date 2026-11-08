#!/usr/bin/env python3
import os

os.environ.update(
    OMP_NUM_THREADS="2",
    MKL_NUM_THREADS="2",
    OPENBLAS_NUM_THREADS="2",
    CUDA_VISIBLE_DEVICES="",
)

import argparse
import datetime as dt
import hashlib
import json
import re
from pathlib import Path

import torch
from safetensors import safe_open

torch.set_num_threads(2)
torch.set_num_interop_threads(2)

SOURCE = Path("/workspace/hf/hub/models--Hcompany--Holo-3.1-4B/snapshots/8c88265a5a159bfd1492db9243733dd2e6e04a6e")
CHECKPOINT_ROOT = Path("/dev/shm/moon-leak")
RECEIPT_ROOT = Path("/workspace/astra/moon-leak")
INDEX_NAME = "model.safetensors.index.json"
HEAD_WIDTH = 256
EXPECTED_MATRIX_SHAPE = (2560, 4096)


def digest(path):
    value = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(8 * 1024 * 1024), b""):
            value.update(block)
    return value.hexdigest()


def require(condition, message):
    if not condition:
        raise RuntimeError(message)


def bitwise_equal(left, right):
    if left.shape != right.shape or left.dtype != right.dtype:
        return False
    left_bytes = left.contiguous().view(torch.uint8)
    right_bytes = right.contiguous().view(torch.uint8)
    return torch.equal(left_bytes, right_bytes)


def load_spec(path):
    spec = json.loads(path.read_text())
    require(set(spec) >= {"name", "scale", "heads"}, "spec requires name, scale, and heads")
    require(isinstance(spec["name"], str) and re.fullmatch(r"[A-Za-z0-9_.-]+", spec["name"]), "unsafe spec name")
    scale = spec["scale"]
    require(not isinstance(scale, bool) and isinstance(scale, (int, float)) and scale in (0, 0.5), "scale must be 0 or 0.5")
    heads = spec["heads"]
    require(isinstance(heads, list) and 2 <= len(heads) <= 6, "heads must contain 2 to 6 entries")
    normalized = []
    for item in heads:
        require(isinstance(item, list) and len(item) == 2, "each head must be [layer, head]")
        layer, head = item
        require(type(layer) is int and type(head) is int, "layer and head must be integers")
        require(layer in range(3, 32, 4) and head in range(16), f"invalid head: {item}")
        normalized.append((layer, head))
    require(len(set(normalized)) == len(normalized), "duplicate head declaration")
    return spec, normalized


def resolve_inputs(spec_arg, checkpoint_arg):
    source = SOURCE.resolve(strict=True)
    receipt_root = RECEIPT_ROOT.resolve(strict=True)
    checkpoint_root = CHECKPOINT_ROOT.resolve(strict=True)
    spec_path = spec_arg.resolve(strict=True)
    require(spec_path.parent == receipt_root, f"spec must be directly under {receipt_root}")
    spec, heads = load_spec(spec_path)
    checkpoint = checkpoint_arg.resolve(strict=True)
    require(checkpoint.is_dir(), "checkpoint must be a directory")
    require(checkpoint.parent == checkpoint_root, f"checkpoint must be directly under {checkpoint_root}")
    require(checkpoint.name == spec["name"], "checkpoint directory name must equal spec name")
    return source, receipt_root, spec_path, spec, heads, checkpoint


def file_inventory(directory):
    return {path.name: path for path in directory.iterdir() if path.is_file()}


def compare_artifacts(source, checkpoint):
    source_files = file_inventory(source)
    checkpoint_files = file_inventory(checkpoint)
    require(set(checkpoint_files) == set(source_files), "checkpoint artifact names differ from source")
    non_tensor_hashes = {}
    for name in sorted(source_files):
        if name.endswith(".safetensors"):
            continue
        source_hash = digest(source_files[name])
        checkpoint_hash = digest(checkpoint_files[name])
        require(checkpoint_hash == source_hash, f"non-tensor artifact differs: {name}")
        non_tensor_hashes[name] = source_hash
    require(INDEX_NAME in source_files, f"source is missing {INDEX_NAME}")
    source_index = json.loads(source_files[INDEX_NAME].read_text())
    checkpoint_index = json.loads(checkpoint_files[INDEX_NAME].read_text())
    require(source_index == checkpoint_index, "checkpoint shard index differs from source")
    require(isinstance(source_index.get("weight_map"), dict) and source_index["weight_map"], "invalid source weight_map")
    shards = set(source_index["weight_map"].values())
    source_shards = {name for name in source_files if name.endswith(".safetensors")}
    checkpoint_shards = {name for name in checkpoint_files if name.endswith(".safetensors")}
    require(source_shards == shards, "source shard artifacts do not exactly match its index")
    require(checkpoint_shards == shards, "checkpoint shard artifacts do not exactly match its index")
    return source_index, sorted(shards), non_tensor_hashes


def target_map(heads):
    targets = {}
    for layer, head in heads:
        key = f"model.language_model.layers.{layer}.self_attn.o_proj.weight"
        targets.setdefault(key, []).append(head)
    return {key: sorted(value) for key, value in targets.items()}


def audit_tensors(source, checkpoint, index, shards, targets, scale):
    weight_map = index["weight_map"]
    keys_by_shard = {}
    for key, shard in weight_map.items():
        keys_by_shard.setdefault(shard, set()).add(key)
    require(set(targets) <= set(weight_map), "one or more target matrices are absent from the index")
    tensor_count = 0
    tensor_numel = 0
    target_receipts = []
    shard_receipts = []
    observed_targets = set()
    for shard in shards:
        with safe_open(source / shard, framework="pt", device="cpu") as source_file, safe_open(
            checkpoint / shard, framework="pt", device="cpu"
        ) as checkpoint_file:
            source_keys = set(source_file.keys())
            checkpoint_keys = set(checkpoint_file.keys())
            mapped_keys = keys_by_shard.get(shard, set())
            require(source_keys == mapped_keys, f"source keys/index mismatch in {shard}")
            require(checkpoint_keys == mapped_keys, f"checkpoint keys/index mismatch in {shard}")
            require(source_file.metadata() == checkpoint_file.metadata(), f"safetensors metadata differs in {shard}")
            for key in sorted(mapped_keys):
                source_tensor = source_file.get_tensor(key)
                checkpoint_tensor = checkpoint_file.get_tensor(key)
                require(source_tensor.shape == checkpoint_tensor.shape, f"shape differs: {key}")
                require(source_tensor.dtype == checkpoint_tensor.dtype, f"dtype differs: {key}")
                tensor_count += 1
                tensor_numel += source_tensor.numel()
                if key in targets:
                    require(tuple(source_tensor.shape) == EXPECTED_MATRIX_SHAPE, f"unexpected o_proj shape: {key}")
                    expected = source_tensor.clone()
                    for head in targets[key]:
                        start = head * HEAD_WIDTH
                        expected[:, start : start + HEAD_WIDTH].mul_(scale)
                    require(bitwise_equal(checkpoint_tensor, expected), f"target edit mismatch: {key}")
                    target_receipts.append(
                        {
                            "key": key,
                            "shard": shard,
                            "heads": targets[key],
                            "dtype": str(source_tensor.dtype),
                            "shape": list(source_tensor.shape),
                            "target_columns": len(targets[key]) * HEAD_WIDTH,
                        }
                    )
                    observed_targets.add(key)
                    del expected
                else:
                    require(bitwise_equal(checkpoint_tensor, source_tensor), f"non-target tensor changed: {key}")
                del source_tensor, checkpoint_tensor
            shard_receipts.append(
                {
                    "shard": shard,
                    "tensor_count": len(mapped_keys),
                    "metadata": source_file.metadata(),
                }
            )
    require(observed_targets == set(targets), "not every declared target was audited")
    return tensor_count, tensor_numel, target_receipts, shard_receipts


def write_receipt(receipt_root, spec, value):
    destination = receipt_root / f"verify_{spec['name']}.json"
    temporary = receipt_root / f".verify_{spec['name']}.{os.getpid()}.tmp"
    temporary.write_text(json.dumps(value, indent=2) + "\n")
    os.replace(temporary, destination)
    return destination


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("spec", type=Path)
    parser.add_argument("checkpoint", type=Path)
    args = parser.parse_args()
    source, receipt_root, spec_path, spec, heads, checkpoint = resolve_inputs(args.spec, args.checkpoint)
    index, shards, non_tensor_hashes = compare_artifacts(source, checkpoint)
    targets = target_map(heads)
    tensor_count, tensor_numel, target_receipts, shard_receipts = audit_tensors(
        source, checkpoint, index, shards, targets, spec["scale"]
    )
    receipt = {
        "verified_utc": dt.datetime.now(dt.timezone.utc).isoformat(),
        "status": "PASS",
        "spec": spec,
        "spec_sha256": digest(spec_path),
        "source": str(source),
        "checkpoint": str(checkpoint),
        "index_sha256": digest(source / INDEX_NAME),
        "artifact_count": len(file_inventory(source)),
        "shard_count": len(shards),
        "tensor_count": tensor_count,
        "tensor_numel": tensor_numel,
        "target_matrices": target_receipts,
        "unchanged_tensor_count": tensor_count - len(target_receipts),
        "non_tensor_sha256": non_tensor_hashes,
        "shards": shard_receipts,
        "checks": {
            "artifact_names_exact": True,
            "non_tensor_files_byte_identical": True,
            "index_mapping_exact": True,
            "all_index_keys_present_in_declared_shards": True,
            "all_shapes_and_dtypes_equal": True,
            "declared_head_columns_scaled_bitwise_exact": True,
            "all_other_bytes_unchanged": True,
        },
    }
    destination = write_receipt(receipt_root, spec, receipt)
    print(json.dumps({"status": "PASS", "receipt": str(destination), "tensors": tensor_count}, indent=2))


if __name__ == "__main__":
    main()
