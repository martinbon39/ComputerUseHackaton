import argparse
import fcntl
import gc
import hashlib
import json
import math
import os
import time
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
from pathlib import Path

os.environ.update(
    OMP_NUM_THREADS="2",
    MKL_NUM_THREADS="2",
    OPENBLAS_NUM_THREADS="2",
    CUDA_VISIBLE_DEVICES="",
    PYTHONDONTWRITEBYTECODE="1",
)

import torch
from safetensors import safe_open

torch.set_num_threads(2)
torch.set_num_interop_threads(2)

ROOT_DEFAULT = Path("/dev/shm/astra-regmean")
CHECKPOINT_DEFAULT = Path("/dev/shm/regmean_cua_centered_fp16")
HOLO = Path(
    "/workspace/hf/hub/models--Hcompany--Holo-3.1-4B/snapshots/"
    "8c88265a5a159bfd1492db9243733dd2e6e04a6e"
)
QWEN = Path("/root/expo/base")
CUA = Path("/dev/shm/astra_merge_cua")
EXPECTED_TENSORS = 724
EXPECTED_MANIFEST_SHA256 = "f517da46643a8d1b5493cd5730075af6cff9de410523c23914e3eddc9de56878"
EXPECTED_CAPTURES_SHA256 = "b16a233837d6b19603e80e6359a45a48af5fbd19643ca2fba09ee95fa08d71f1"
EXPECTED_DERIVE_SHA256 = "b899ad2d032e5807d6257df40f12401410a0f8adb8e8ba36f4a36f173dd1f374"
EXPECTED_BUILD_SHA256 = "3157e231f3c96aaa8aae7cb58cd29af68112fe1ed7039a5aef74855d1aac1824"
EXPECTED_BUILD_FP16_SHA256 = "d6f868f97069256ad2e19991f71e7410cb5c12ea545706932214b79b833b8cc4"
EXPECTED_COMMON_SHA256 = "7fcb7c778ff22eb714b4f5a8a6714627afb015d21fbe6dd7603d0ed400f8d7eb"
EXPECTED_MATH_REVIEW_SHA256 = "aff6779e144e395091be7bc4d1ea7cab9d4adaba48f104cd3de0fb05ebf345e1"
EXPECTED_DONOR_SHARDS = {
    QWEN / "model.safetensors-00001-of-00002.safetensors": "26a93f066e1916adb13453dae5a0c707c0fbc71299ed98779571a907b8e74c61",
    QWEN / "model.safetensors-00002-of-00002.safetensors": "cb544bd9bfae93dc59b0f22b292f5933573854a7f9b97835c67060d7d910e188",
    CUA / "model.safetensors-00001-of-00002.safetensors": "a8ad0e6fb47369fed2262d423d713e47f8f7d878851e0ee8bdd7c90bc47d8237",
    CUA / "model.safetensors-00002-of-00002.safetensors": "ae5828491a638b66d198b52297fcf07c1cb9970326c7e027c55afc791bdff213",
}


def sha256(path):
    digest = hashlib.sha256()
    with Path(path).open("rb", buffering=8 << 20) as handle:
        for block in iter(lambda: handle.read(8 << 20), b""):
            digest.update(block)
    return digest.hexdigest()


def atomic_json(path, value):
    path = Path(path)
    temporary = path.with_name(f"{path.name}.{os.getpid()}.tmp")
    with temporary.open("w") as handle:
        handle.write(json.dumps(value, indent=2, sort_keys=True, allow_nan=False) + "\n")
        handle.flush()
        os.fsync(handle.fileno())
    os.replace(temporary, path)
    directory = os.open(path.parent, os.O_RDONLY | os.O_DIRECTORY)
    try:
        os.fsync(directory)
    finally:
        os.close(directory)


def load_json(path):
    value = json.loads(Path(path).read_text())
    if not isinstance(value, dict):
        raise TypeError(f"expected JSON object: {path}")
    return value


def writer_schema():
    result = {}
    for layer in range(12, 24):
        result[f"model.language_model.layers.{layer}.mlp.down_proj.weight"] = (2560, 9216)
        module = "self_attn.o_proj" if layer % 4 == 3 else "linear_attn.out_proj"
        result[f"model.language_model.layers.{layer}.{module}.weight"] = (2560, 4096)
    return result


def relative_files(root):
    return {path.relative_to(root).as_posix(): path for path in Path(root).rglob("*") if path.is_file()}


def finite_float(value):
    return isinstance(value, (int, float)) and math.isfinite(float(value))


def canonical_json(value):
    return json.loads(json.dumps(value, sort_keys=True, allow_nan=False))


def relative_error(actual, expected):
    denominator = expected.norm().clamp_min(torch.finfo(expected.dtype).tiny)
    return float((actual - expected).norm() / denominator)


class Weights:
    def __init__(self, root):
        self.root = Path(root)
        self.index_path = self.root / "model.safetensors.index.json"
        self.index = load_json(self.index_path)
        self.weight_map = self.index["weight_map"]
        self.handles = {
            shard: safe_open(str(self.root / shard), framework="pt", device="cpu")
            for shard in sorted(set(self.weight_map.values()))
        }

    def get(self, key):
        return self.handles[self.weight_map[key]].get_tensor(key)

    def actual_keys(self):
        all_keys = set()
        per_shard = {}
        for shard, handle in self.handles.items():
            keys = set(handle.keys())
            per_shard[shard] = keys
            all_keys.update(keys)
        return all_keys, per_shard


class Review:
    def __init__(self, root, checkpoint):
        self.root = Path(root)
        self.checkpoint = Path(checkpoint)
        self.started = time.monotonic()
        self.error_counts = {}
        self.errors = []
        self.counts = {
            "tensor_keys": 0,
            "finite_tensors": 0,
            "edited_tensors": 0,
            "materially_changed_writers": 0,
            "unchanged_tensors": 0,
            "changed_values": 0,
            "factor_writers": 0,
            "capture_contexts": 0,
            "math_writers": 0,
            "source_byte_hashes": 0,
            "base_assets_bitexact": 0,
        }
        self.hashes = {
            "controls": {},
            "donor_sources": {},
            "checkpoint": {},
            "base_assets": {},
        }
        self.math = {
            "formula": "E=(0.5*(W_CUA-W_Qwen)*F)*R, R=(X*(X.T*X+epsilon*I)^-1*J).T, X=[F,T,G]",
            "fp16_exact_preservation_claimed": False,
            "writers": {},
        }
        self.nullspace_vectors = {}

    def fail(self, code, **detail):
        self.error_counts[code] = self.error_counts.get(code, 0) + 1
        if len(self.errors) < 200:
            self.errors.append(dict(code=code, **detail))

    def check(self, condition, code, **detail):
        if not condition:
            self.fail(code, **detail)
        return condition

    def result(self):
        return {
            "generated_at_utc": datetime.now(timezone.utc).isoformat(),
            "status": "PASSED" if not self.error_counts else "FAILED",
            "target": str(self.checkpoint),
            "checkpoint": str(self.checkpoint),
            "passed": not self.error_counts,
            "counts": self.counts,
            "hashes": self.hashes,
            "math": self.math,
            "error_counts": self.error_counts,
            "errors": self.errors,
            "execution": {
                "elapsed_seconds": time.monotonic() - self.started,
                "torch_threads": torch.get_num_threads(),
                "torch_interop_threads": torch.get_num_interop_threads(),
                "cuda_visible_devices": os.environ["CUDA_VISIBLE_DEVICES"],
                "cpu_affinity": sorted(os.sched_getaffinity(0)),
            },
            "scope": {
                "behavioral_efficacy": "NOT_RUN",
                "gpu": "NOT_USED",
                "reserve_or_test_content": "NOT_READ",
                "fp16_nullspace": "MEASURED_ONLY_NOT_ASSERTED_EXACT",
            },
        }


def verify_control_files(review):
    expected = {
        review.root / "manifest.json": EXPECTED_MANIFEST_SHA256,
        review.root / "derive.py": EXPECTED_DERIVE_SHA256,
        review.root / "build.py": EXPECTED_BUILD_SHA256,
        review.root / "build_fp16.py": EXPECTED_BUILD_FP16_SHA256,
        review.root / "common.py": EXPECTED_COMMON_SHA256,
        review.root / "VERIFY_MATH.json": EXPECTED_MATH_REVIEW_SHA256,
    }
    for path, digest in expected.items():
        if not review.check(path.is_file(), "control_file_missing", path=str(path)):
            continue
        actual = sha256(path)
        review.hashes["controls"][str(path)] = actual
        review.check(actual == digest, "control_file_hash_mismatch", path=str(path), expected=digest, actual=actual)
    captures_path = review.root / "captures.pt"
    captures_sha_path = review.root / "captures.sha256"
    if review.check(captures_path.is_file(), "captures_missing", path=str(captures_path)) and review.check(
        captures_sha_path.is_file(), "captures_sha_missing", path=str(captures_sha_path)
    ):
        recorded = captures_sha_path.read_text().strip()
        review.check(recorded == EXPECTED_CAPTURES_SHA256, "frozen_capture_digest_changed", expected=EXPECTED_CAPTURES_SHA256, actual=recorded)
        actual = sha256(captures_path)
        review.hashes["controls"][str(captures_path)] = actual
        review.check(actual == recorded, "captures_byte_hash_mismatch", expected=recorded, actual=actual)
    math_path = review.root / "VERIFY_MATH.json"
    if math_path.is_file():
        math_review = load_json(math_path)
        review.check(math_review.get("verdict", {}).get("math_artifact") == "PASS", "certified_math_review_not_passed")
        files = math_review.get("files", {})
        review.check(files.get("derive.py") == EXPECTED_DERIVE_SHA256, "math_review_derive_hash_mismatch")
        review.check(files.get("build.py") == EXPECTED_BUILD_SHA256, "math_review_build_hash_mismatch")
        review.check(files.get("local_and_pod_copies_identical") is True, "math_review_source_identity_not_certified")
        formula = math_review.get("formula", {})
        review.check(formula.get("donor_delta") == "0.5 * (W_CUA - W_Qwen)", "math_review_donor_formula_mismatch")
        review.check(formula.get("epsilon") == "alpha * trace(X^T X) / d", "math_review_epsilon_formula_mismatch")


def verify_donor_hashes(review):
    missing = [path for path in EXPECTED_DONOR_SHARDS if not path.is_file()]
    for path in missing:
        review.fail("donor_shard_missing", path=str(path))
    paths = sorted(set(EXPECTED_DONOR_SHARDS) - set(missing), key=str)
    with ThreadPoolExecutor(max_workers=2) as pool:
        digests = list(pool.map(sha256, paths))
    for path, actual in zip(paths, digests):
        expected = EXPECTED_DONOR_SHARDS[path]
        review.hashes["donor_sources"][str(path)] = {
            "actual": actual,
            "expected": expected,
            "bytes": path.stat().st_size,
            "match": actual == expected,
        }
        review.check(actual == expected, "donor_shard_hash_mismatch", path=str(path), expected=expected, actual=actual)
        review.counts["source_byte_hashes"] += 1


def validate_capture_pack(review, manifest, schema):
    path = review.root / "captures.pt"
    pack = torch.load(path, weights_only=True, map_location="cpu")
    review.check(isinstance(pack, dict), "capture_pack_not_mapping")
    review.check(pack.get("complete") is True, "capture_pack_incomplete")
    review.check(pack.get("manifest_sha256") == EXPECTED_MANIFEST_SHA256, "capture_manifest_hash_mismatch")
    captures = pack.get("captures")
    metadata = pack.get("metadata")
    if not isinstance(captures, dict) or not isinstance(metadata, dict):
        review.fail("capture_pack_structure_invalid")
        return pack
    rows = manifest.get("rows", [])
    expected_ids = {row["id"] for row in rows} | {f"text_{index}" for index in range(len(manifest.get("text_prompts", [])))}
    review.check(set(captures) == expected_ids, "capture_context_set_mismatch", expected=len(expected_ids), actual=len(captures))
    review.check(set(metadata) == expected_ids, "capture_metadata_set_mismatch")
    review.counts["capture_contexts"] = len(captures)
    for identifier in sorted(set(captures) & expected_ids):
        context = captures[identifier]
        if not isinstance(context, dict):
            review.fail("capture_context_not_mapping", context=identifier)
            continue
        review.check(set(context) == set(schema), "capture_writer_set_mismatch", context=identifier)
        positions = 1 if identifier.startswith("text_") else 2
        for name in sorted(set(context) & set(schema)):
            tensor = context[name]
            expected_shape = (positions, schema[name][1])
            review.check(isinstance(tensor, torch.Tensor), "capture_not_tensor", context=identifier, writer=name)
            if not isinstance(tensor, torch.Tensor):
                continue
            review.check(tensor.dtype == torch.float32, "capture_dtype_mismatch", context=identifier, writer=name, actual=str(tensor.dtype))
            review.check(tuple(tensor.shape) == expected_shape, "capture_shape_mismatch", context=identifier, writer=name, expected=list(expected_shape), actual=list(tensor.shape))
            review.check(bool(torch.isfinite(tensor).all()), "capture_nonfinite", context=identifier, writer=name)
    return pack


def key_blocks(pack, rows, name):
    blocks = []
    counts = {}
    for label in ("fs+", "fs-", "healthy"):
        values = [pack["captures"][row["id"]][name].T.double() for row in rows if row["label"] == label]
        if label == "healthy":
            values.extend(pack["captures"][key][name].T.double() for key in sorted(pack["captures"]) if key.startswith("text_"))
        raw = torch.cat(values, dim=1)
        counts[label] = raw.shape[1]
        blocks.append(raw / math.sqrt(raw.shape[1]))
    return blocks, counts


def normalized_scores(scores):
    if not isinstance(scores, dict):
        return {}
    return {float(key): float(value) for key, value in scores.items()}


def verify_factor_math(review, manifest, captures, qwen, cua, schema):
    factors_path = review.root / "candidate_factors.pt"
    derive_path = review.root / "derive.json"
    if not review.check(factors_path.is_file(), "factors_missing", path=str(factors_path)):
        return None
    if not review.check(derive_path.is_file(), "derive_record_missing", path=str(derive_path)):
        return None
    factor_hash = sha256(factors_path)
    derive_record = load_json(derive_path)
    review.hashes["controls"][str(factors_path)] = factor_hash
    review.hashes["controls"][str(derive_path)] = sha256(derive_path)
    review.check(derive_record.get("factors_sha256") == factor_hash, "derive_factor_hash_mismatch")
    pack = torch.load(factors_path, weights_only=True, map_location="cpu")
    review.check(set(pack) == {"learned", "metadata"}, "factor_pack_key_set_mismatch", actual=sorted(pack) if isinstance(pack, dict) else None)
    factors = pack.get("learned", {})
    metadata = pack.get("metadata", {})
    review.check(set(factors) == set(schema), "factor_writer_set_mismatch")
    review.counts["factor_writers"] = len(factors)
    review.check(metadata.get("manifest_sha256") == EXPECTED_MANIFEST_SHA256, "factor_manifest_hash_mismatch")
    review.check(metadata.get("captures_sha256") == EXPECTED_CAPTURES_SHA256, "factor_capture_hash_mismatch")
    review.check(metadata.get("positions") == ["prefill", "endthink_before_note"], "factor_positions_mismatch")
    review.check(metadata.get("formula") == "WH + .5*(WCUA-WQwen)*F*F.T*(F*F.T+T*T.T+G*G.T+epsilon*I)^-1", "factor_formula_mismatch")
    review.check(metadata.get("normalization") == "Each class block divided by sqrt(number of columns); healthy block includes three text prefill keys", "factor_normalization_mismatch")
    alphas = [float(value) for value in manifest.get("parameters", {}).get("ridge_trace_over_d", [])]
    scores = normalized_scores(metadata.get("scores"))
    chosen = float(metadata.get("alpha")) if finite_float(metadata.get("alpha")) else None
    review.check(set(scores) == set(alphas), "factor_score_grid_mismatch", scores=sorted(scores), alphas=alphas)
    if scores and chosen is not None:
        independent_choice = min(alphas, key=lambda alpha: (scores[alpha], -alpha))
        review.check(chosen == independent_choice, "chosen_alpha_not_score_minimum", chosen=chosen, expected=independent_choice)
        review.check(float(derive_record.get("chosen_alpha")) == chosen, "derive_chosen_alpha_mismatch")
        review.check(normalized_scores(derive_record.get("scores")) == scores, "derive_scores_mismatch")
    stats = metadata.get("stats", [])
    review.check(isinstance(stats, list) and len(stats) == len(schema), "selected_stats_count_mismatch", actual=len(stats) if isinstance(stats, list) else None)
    stats_by_writer = {row.get("writer"): row for row in stats if isinstance(row, dict)}
    review.check(set(stats_by_writer) == set(schema), "selected_stats_writer_set_mismatch")
    if chosen is None:
        return pack
    generator_seed = 20261108
    for writer_index, name in enumerate(sorted(schema)):
        if name not in factors or name not in qwen.weight_map or name not in cua.weight_map:
            review.fail("math_source_or_factor_missing", writer=name)
            continue
        factor = factors[name]
        left = factor.get("left") if isinstance(factor, dict) else None
        right = factor.get("right") if isinstance(factor, dict) else None
        if not isinstance(left, torch.Tensor) or not isinstance(right, torch.Tensor):
            review.fail("factor_not_tensor_pair", writer=name)
            continue
        review.check(left.dtype == torch.float64 and right.dtype == torch.float64, "factor_dtype_mismatch", writer=name, left=str(left.dtype), right=str(right.dtype))
        review.check(bool(torch.isfinite(left).all()) and bool(torch.isfinite(right).all()), "factor_nonfinite", writer=name)
        blocks, columns = key_blocks(captures, manifest["rows"], name)
        f, t, g = blocks
        x = torch.cat([f, t, g], dim=1)
        gram = x.T @ x
        epsilon = float(chosen * gram.trace() / x.shape[0])
        review.check(epsilon > 0 and math.isfinite(epsilon), "epsilon_invalid", writer=name, epsilon=epsilon)
        regularized = gram + epsilon * torch.eye(gram.shape[0], dtype=torch.float64)
        chol, info = torch.linalg.cholesky_ex(regularized)
        unique = int(info) == 0 and bool(torch.diagonal(chol).gt(0).all())
        review.check(unique, "regularized_solve_not_unique_spd", writer=name, cholesky_info=int(info))
        if not unique:
            continue
        target = torch.eye(gram.shape[0], dtype=torch.float64)[:, :f.shape[1]]
        coefficients = torch.cholesky_solve(target, chol)
        y = x @ coefficients
        expected_right = y.T
        normal_residual = x @ (x.T @ y) + epsilon * y - f
        normal_relative = float(normal_residual.norm() / f.norm())
        review.check(normal_relative < 1e-10, "normal_equation_residual_too_large", writer=name, value=normal_relative)
        right_shape_ok = tuple(right.shape) == tuple(expected_right.shape)
        review.check(right_shape_ok, "right_shape_mismatch", writer=name, expected=list(expected_right.shape), actual=list(right.shape))
        right_error = relative_error(right, expected_right) if right_shape_ok else math.inf
        review.check(right_shape_ok and right_error < 1e-12, "right_not_reconstructed_from_captures", writer=name, relative_error=right_error)
        qwen_weight = qwen.get(name)
        cua_weight = cua.get(name)
        review.check(qwen_weight.shape == cua_weight.shape == torch.Size(schema[name]), "donor_writer_shape_mismatch", writer=name)
        review.check(qwen_weight.dtype == cua_weight.dtype == torch.bfloat16, "donor_writer_dtype_mismatch", writer=name, qwen=str(qwen_weight.dtype), cua=str(cua_weight.dtype))
        review.check(bool(torch.isfinite(qwen_weight).all()) and bool(torch.isfinite(cua_weight).all()), "donor_writer_nonfinite", writer=name)
        donor_delta = (0.5 * (cua_weight.float() - qwen_weight.float())).double()
        expected_left = donor_delta @ f
        left_shape_ok = tuple(left.shape) == tuple(expected_left.shape)
        review.check(left_shape_ok, "left_shape_mismatch", writer=name, expected=list(expected_left.shape), actual=list(left.shape))
        left_error = relative_error(left, expected_left) if left_shape_ok else math.inf
        review.check(left_shape_ok and left_error < 1e-12, "left_not_delta_times_f", writer=name, relative_error=left_error)
        generator = torch.Generator().manual_seed(generator_seed + writer_index)
        random_vectors = torch.randn(x.shape[0], 3, dtype=torch.float64, generator=generator)
        q, _ = torch.linalg.qr(x, mode="reduced")
        null_vectors = random_vectors - q @ (q.T @ random_vectors)
        null_input_relative = float((x.T @ null_vectors).norm() / (x.norm() * null_vectors.norm()).clamp_min(torch.finfo(torch.float64).tiny))
        right_null_relative = float((right @ null_vectors).norm() / (right.norm() * null_vectors.norm()).clamp_min(torch.finfo(torch.float64).tiny))
        fp64_update = left @ right
        update_null_relative = float((fp64_update @ null_vectors).norm() / (fp64_update.norm() * null_vectors.norm()).clamp_min(torch.finfo(torch.float64).tiny))
        review.check(null_input_relative < 1e-10, "random_projection_not_in_construction_nullspace", writer=name, value=null_input_relative)
        review.check(right_null_relative < 1e-10, "right_not_null_on_random_nullspace", writer=name, value=right_null_relative)
        review.check(update_null_relative < 1e-10, "fp64_update_not_null_on_random_nullspace", writer=name, value=update_null_relative)
        review.nullspace_vectors[name] = null_vectors
        stat = stats_by_writer.get(name, {})
        if stat:
            review.check(float(stat.get("alpha")) == chosen, "stat_alpha_mismatch", writer=name)
            review.check(int(stat.get("columns")) == x.shape[1], "stat_column_count_mismatch", writer=name)
            review.check(int(stat.get("dimension")) == x.shape[0], "stat_dimension_mismatch", writer=name)
            recorded_epsilon = float(stat.get("epsilon"))
            review.check(math.isclose(recorded_epsilon, epsilon, rel_tol=1e-12, abs_tol=1e-15), "stat_epsilon_mismatch", writer=name, recorded=recorded_epsilon, actual=epsilon)
            recorded_residual = float(stat.get("normal_equation_relative_residual"))
            review.check(math.isclose(recorded_residual, normal_relative, rel_tol=1e-8, abs_tol=1e-14), "stat_normal_residual_mismatch", writer=name, recorded=recorded_residual, actual=normal_relative)
        review.math["writers"][name] = {
            "input_dimension": x.shape[0],
            "columns": columns,
            "epsilon": epsilon,
            "cholesky_unique_spd": unique,
            "normal_equation_relative_residual": normal_relative,
            "right_reconstruction_relative_error": right_error,
            "left_delta_f_relative_error": left_error,
            "random_nullspace_input_relative_residual": null_input_relative,
            "random_nullspace_right_relative_effect": right_null_relative,
            "random_nullspace_fp64_update_relative_effect": update_null_relative,
        }
        review.counts["math_writers"] += 1
        del f, t, g, blocks, x, gram, regularized, chol, target, coefficients, y, expected_right
        del qwen_weight, cua_weight, donor_delta, expected_left, q, random_vectors, null_vectors, fp64_update
        gc.collect()
    return pack


def verify_files(review, checkpoint_manifest, holo):
    source_files = relative_files(HOLO)
    target_files = relative_files(review.checkpoint)
    expected_target = set(source_files) | {"regmean_manifest.json"}
    review.check(set(target_files) == expected_target, "checkpoint_file_set_mismatch", missing=sorted(expected_target - set(target_files)), extra=sorted(set(target_files) - expected_target))
    manifest_files = checkpoint_manifest.get("files", {})
    review.check(set(manifest_files) == set(source_files), "checkpoint_manifest_file_set_mismatch")
    nonweights = sorted(name for name in source_files if not name.endswith(".safetensors"))
    for name in nonweights:
        if name not in target_files:
            continue
        source_digest = sha256(source_files[name])
        target_digest = sha256(target_files[name])
        review.hashes["base_assets"][name] = {"source": source_digest, "checkpoint": target_digest, "match": source_digest == target_digest}
        review.check(source_digest == target_digest, "base_asset_not_bitexact", file=name)
        review.counts["base_assets_bitexact"] += int(source_digest == target_digest)
    existing = sorted(name for name in source_files if name in target_files)
    with ThreadPoolExecutor(max_workers=2) as pool:
        digests = list(pool.map(lambda name: sha256(target_files[name]), existing))
    for name, digest in zip(existing, digests):
        review.hashes["checkpoint"][name] = {"sha256": digest, "bytes": target_files[name].stat().st_size}
        review.check(manifest_files.get(name) == digest, "checkpoint_file_manifest_hash_mismatch", file=name)
    source_index = HOLO / "model.safetensors.index.json"
    target_index = review.checkpoint / "model.safetensors.index.json"
    if target_index.is_file():
        review.check(target_index.read_bytes() == source_index.read_bytes(), "checkpoint_index_not_bitexact")
    review.check(checkpoint_manifest.get("source") == str(HOLO), "checkpoint_source_path_mismatch")
    checkpoint_copy = review.root / "checkpoint_manifest_fp16.json"
    if review.check(checkpoint_copy.is_file(), "root_checkpoint_manifest_missing"):
        review.check(load_json(checkpoint_copy) == checkpoint_manifest, "root_checkpoint_manifest_mismatch")


def verify_tensor_checkpoint(review, checkpoint_manifest, factors_pack, holo, output, schema):
    holo_keys = set(holo.weight_map)
    output_keys = set(output.weight_map)
    actual_output, per_shard = output.actual_keys()
    review.check(len(holo_keys) == EXPECTED_TENSORS, "holo_tensor_count_mismatch", actual=len(holo_keys))
    review.check(output.weight_map == holo.weight_map, "output_weight_map_mismatch")
    review.check(actual_output == holo_keys, "output_actual_tensor_set_mismatch")
    for shard, actual_keys in per_shard.items():
        indexed = {key for key, mapped in output.weight_map.items() if mapped == shard}
        review.check(actual_keys == indexed, "output_shard_index_mismatch", shard=shard)
    factors = factors_pack.get("learned", {}) if isinstance(factors_pack, dict) else {}
    edited_manifest = checkpoint_manifest.get("edited", {})
    review.check(set(edited_manifest) == set(schema), "checkpoint_edited_metadata_set_mismatch")
    total_elements = 0
    changed_values = 0
    for index, name in enumerate(sorted(holo_keys), 1):
        try:
            base = holo.get(name)
            candidate = output.get(name)
            total_elements += base.numel()
            shape_ok = candidate.shape == base.shape
            expected_dtype = torch.float16 if name in schema else base.dtype
            dtype_ok = candidate.dtype == expected_dtype
            review.check(shape_ok, "tensor_shape_mismatch", tensor=name, expected=list(base.shape), actual=list(candidate.shape))
            review.check(dtype_ok, "tensor_dtype_mismatch", tensor=name, expected=str(expected_dtype), actual=str(candidate.dtype))
            base_finite = bool(torch.isfinite(base).all())
            candidate_finite = bool(torch.isfinite(candidate).all())
            review.check(base_finite, "base_tensor_nonfinite", tensor=name)
            review.check(candidate_finite, "tensor_nonfinite", tensor=name)
            review.counts["finite_tensors"] += int(base_finite and candidate_finite)
            if not shape_ok or not dtype_ok:
                continue
            if name not in schema:
                equal = torch.equal(candidate, base)
                review.check(equal, "nonwriter_tensor_changed", tensor=name)
                review.counts["unchanged_tensors"] += int(equal)
                continue
            review.counts["edited_tensors"] += 1
            expected_shape = schema[name]
            review.check(tuple(base.shape) == expected_shape, "base_writer_shape_mismatch", tensor=name, expected=list(expected_shape), actual=list(base.shape))
            review.check(base.dtype == torch.bfloat16, "base_writer_dtype_mismatch", tensor=name, actual=str(base.dtype))
            review.check(candidate.dtype == torch.float16, "edited_writer_not_fp16", tensor=name, actual=str(candidate.dtype))
            factor = factors.get(name, {})
            left = factor.get("left") if isinstance(factor, dict) else None
            right = factor.get("right") if isinstance(factor, dict) else None
            if not isinstance(left, torch.Tensor) or not isinstance(right, torch.Tensor):
                review.fail("writer_factor_missing", tensor=name)
                continue
            delta = left @ right
            expected = (base.double() + delta).half()
            equal = torch.equal(candidate, expected)
            review.check(equal, "writer_formula_mismatch", tensor=name, mismatched_values=int(torch.count_nonzero(candidate != expected)))
            changed = int(torch.count_nonzero(candidate != base))
            changed_values += changed
            review.counts["materially_changed_writers"] += int(changed > 0)
            realized = candidate.double() - base.double()
            requested_norm = float(delta.norm())
            realized_norm = float(realized.norm())
            quantization_error = float((realized - delta).norm() / delta.norm())
            entry = edited_manifest.get(name, {})
            review.check(entry.get("shape") == list(base.shape), "edited_shape_metadata_mismatch", tensor=name)
            review.check(entry.get("changed") == changed, "edited_changed_count_mismatch", tensor=name)
            for field, actual in (
                ("requested_norm", requested_norm),
                ("realized_norm", realized_norm),
                ("relative_norm", float(realized.norm() / base.double().norm())),
                ("quantization_relative_error", quantization_error),
            ):
                recorded = entry.get(field)
                review.check(finite_float(recorded) and math.isclose(float(recorded), actual, rel_tol=1e-12, abs_tol=1e-15), "edited_numeric_metadata_mismatch", tensor=name, field=field, recorded=recorded, actual=actual)
            math_entry = review.math["writers"].get(name)
            null_vectors = review.nullspace_vectors.get(name)
            if math_entry is not None and null_vectors is not None:
                denominator = (realized.norm() * null_vectors.norm()).clamp_min(torch.finfo(torch.float64).tiny)
                math_entry["random_nullspace_fp16_realized_relative_effect_diagnostic"] = float((realized @ null_vectors).norm() / denominator)
            del delta, expected, realized
        except Exception as exc:
            review.fail("tensor_check_exception", tensor=name, error=type(exc).__name__, detail=str(exc))
        finally:
            if index % 24 == 0:
                gc.collect()
            if index % 100 == 0:
                print(json.dumps({"tensors_checked": index}), flush=True)
    review.counts["tensor_keys"] = len(actual_output)
    review.counts["changed_values"] = changed_values
    review.check(review.counts["tensor_keys"] == EXPECTED_TENSORS, "verified_tensor_count_mismatch")
    review.check(review.counts["finite_tensors"] == EXPECTED_TENSORS, "finite_tensor_count_mismatch")
    review.check(review.counts["edited_tensors"] == len(schema), "verified_writer_count_mismatch")
    review.check(review.counts["materially_changed_writers"] == len(schema), "materially_changed_writer_count_mismatch")
    review.check(review.counts["unchanged_tensors"] == EXPECTED_TENSORS - len(schema), "unchanged_tensor_count_mismatch")
    review.check(checkpoint_manifest.get("tensors") == EXPECTED_TENSORS, "manifest_tensor_count_mismatch")
    review.check(checkpoint_manifest.get("elements") == total_elements, "manifest_element_count_mismatch")
    review.check(checkpoint_manifest.get("changed_elements") == changed_values, "manifest_changed_value_count_mismatch")


def verify(root, checkpoint):
    review = Review(root, checkpoint)
    required = [
        review.root,
        review.checkpoint,
        HOLO,
        QWEN,
        CUA,
        review.root / "manifest.json",
        review.root / "captures.pt",
        review.root / "candidate_factors.pt",
        review.checkpoint / "regmean_manifest.json",
    ]
    for path in required:
        review.check(path.exists(), "required_path_missing", path=str(path))
    if review.error_counts:
        return review.result()
    verify_control_files(review)
    verify_donor_hashes(review)
    manifest = load_json(review.root / "manifest.json")
    schema = writer_schema()
    review.check(len(schema) == 24, "writer_schema_count_mismatch", actual=len(schema))
    captures = validate_capture_pack(review, manifest, schema)
    qwen = Weights(QWEN)
    cua = Weights(CUA)
    factor_pack = verify_factor_math(review, manifest, captures, qwen, cua, schema)
    checkpoint_manifest = load_json(review.checkpoint / "regmean_manifest.json")
    review.check(checkpoint_manifest.get("edited_storage_dtype") == "float16", "checkpoint_storage_dtype_metadata_mismatch")
    review.check(checkpoint_manifest.get("runtime_dtype") == "float16", "checkpoint_runtime_dtype_metadata_mismatch")
    review.check(
        checkpoint_manifest.get("caveat")
        == "Nullspace preservation is exact in FP64 construction; FP16 rounding can introduce off-subspace error.",
        "checkpoint_precision_caveat_mismatch",
    )
    factors_path = review.root / "candidate_factors.pt"
    review.check(checkpoint_manifest.get("factors_sha256") == sha256(factors_path), "checkpoint_factor_hash_mismatch")
    if factor_pack is not None:
        review.check(
            checkpoint_manifest.get("construction") == canonical_json(factor_pack.get("metadata")),
            "checkpoint_factor_metadata_mismatch",
        )
    holo = Weights(HOLO)
    output = Weights(review.checkpoint)
    verify_files(review, checkpoint_manifest, holo)
    if factor_pack is not None:
        verify_tensor_checkpoint(review, checkpoint_manifest, factor_pack, holo, output, schema)
    return review.result()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, default=ROOT_DEFAULT)
    parser.add_argument("--checkpoint", type=Path, default=CHECKPOINT_DEFAULT)
    parser.add_argument("--report", type=Path)
    args = parser.parse_args()
    report = args.report or args.root / "VERIFY_CHECKPOINT_FP16.json"
    lock_path = args.root / ".checkpoint_review_fp16.lock"
    with lock_path.open("w") as lock:
        try:
            fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError:
            print("CHECKPOINT_REVIEW_ALREADY_RUNNING", flush=True)
            raise SystemExit(2)
        atomic_json(report, {
            "generated_at_utc": datetime.now(timezone.utc).isoformat(),
            "target": str(args.checkpoint),
            "checkpoint": str(args.checkpoint),
            "status": "running",
            "passed": False,
            "error_counts": {"verification_in_progress": 1},
        })
        try:
            result = verify(args.root, args.checkpoint)
        except BaseException as exc:
            result = {
                "generated_at_utc": datetime.now(timezone.utc).isoformat(),
                "status": "FAILED",
                "target": str(args.checkpoint),
                "checkpoint": str(args.checkpoint),
                "passed": False,
                "error_counts": {"verifier_exception": 1},
                "errors": [{"code": "verifier_exception", "error": type(exc).__name__, "detail": str(exc)}],
            }
        atomic_json(report, result)
        print(json.dumps({"checkpoint_review": "PASSED" if result["passed"] else "FAILED", "error_counts": result.get("error_counts", {})}), flush=True)
        raise SystemExit(0 if result["passed"] else 1)


if __name__ == "__main__":
    main()
