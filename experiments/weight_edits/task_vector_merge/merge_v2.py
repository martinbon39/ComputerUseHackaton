import os
os.environ.update(OMP_NUM_THREADS="2", MKL_NUM_THREADS="2", OPENBLAS_NUM_THREADS="2")
import torch
torch.set_num_threads(2)
import argparse
import hashlib
import json
import math
import shutil
import time
from pathlib import Path
from safetensors import safe_open
from safetensors.torch import save_file


class Weights:
    def __init__(self, path):
        self.path = Path(path)
        self.config = json.loads((self.path / "config.json").read_text())
        self.index = json.loads((self.path / "model.safetensors.index.json").read_text())
        self.wm = self.index["weight_map"]
        self.handles = {f: safe_open(str(self.path / f), framework="pt", device="cpu") for f in set(self.wm.values())}
        self.shapes = {k: list(self.handles[f].get_slice(k).get_shape()) for k, f in self.wm.items()}

    def get(self, k):
        return self.handles[self.wm[k]].get_tensor(k)


def sha(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for block in iter(lambda: f.read(8 << 20), b""):
            h.update(block)
    return h.hexdigest()


def atomic_json(path, value):
    path = Path(path)
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(json.dumps(value, indent=2) + "\n")
    tmp.replace(path)


def compatibility(h, q, d):
    common = set(h.wm) - {"lm_head.weight"}
    for name, x in [("reference", q), ("donor", d)]:
        missing = sorted(common - set(x.wm))
        unexpected = sorted(k for k in set(x.wm) - set(h.wm) if not k.startswith("mtp."))
        mismatch = [k for k in common & set(x.wm) if x.shapes[k] != h.shapes[k]]
        if missing or unexpected or mismatch:
            raise ValueError({"model": name, "missing": missing, "unexpected": unexpected, "shape_mismatch": mismatch})
    checks = ["hidden_size", "intermediate_size", "num_hidden_layers", "num_attention_heads", "num_key_value_heads", "head_dim", "layer_types", "linear_conv_kernel_dim", "linear_key_head_dim", "linear_value_head_dim", "linear_num_key_heads", "linear_num_value_heads", "vocab_size", "rms_norm_eps", "hidden_act", "rope_parameters", "attn_output_gate", "attention_bias"]
    for field in checks:
        vals = [x.config["text_config"].get(field) for x in [h, q, d]]
        if vals[0] != vals[1] or vals[0] != vals[2]:
            raise ValueError({"architecture_field": field, "values": vals})
    vision_metadata = {"dtype", "torch_dtype", "model_type", "transformers_version"}
    for x in [h, q, d]:
        if x.config["vision_config"].get("model_type") not in {"qwen3_5", "qwen3_5_vision"}:
            raise ValueError("unexpected vision model type")
    for x in [q, d]:
        if {k: v for k, v in h.config["vision_config"].items() if k not in vision_metadata} != {k: v for k, v in x.config["vision_config"].items() if k not in vision_metadata}:
            raise ValueError("vision config mismatch")
    return {"matched": len(common), "shape_mismatches": 0, "holo_tensors": len(h.wm), "reference_tensors": len(q.wm), "donor_tensors": len(d.wm), "ignored_reference": sorted(set(q.wm)-common), "ignored_donor": sorted(set(d.wm)-common), "head_policy": "preserve Holo explicit lm_head exactly", "vision_policy": "preserve Holo exactly"}


def metrics(h, q, d, qb):
    groups = {}
    rows = {}
    for i, k in enumerate(sorted(set(h.wm) & set(q.wm) & set(d.wm) & set(qb.wm))):
        hh, qq, dd, bb = [x.get(k).float().flatten() for x in [h, q, d, qb]]
        td = dd - qq
        th = hh - qq
        db = dd - bb
        pq = qq - bb
        row = {"d2": torch.dot(dd, dd).item(), "q2": torch.dot(qq, qq).item(), "b2": torch.dot(bb, bb).item(), "dq": torch.dot(dd, qq).item(), "db": torch.dot(dd, bb).item(), "td2": torch.dot(td, td).item(), "th2": torch.dot(th, th).item(), "tdth": torch.dot(td, th).item(), "db2": torch.dot(db, db).item(), "pq2": torch.dot(pq, pq).item(), "tdpq": torch.dot(td, pq).item()}
        group = "language_layers" if k.startswith("model.language_model.layers.") else "vision" if k.startswith("model.visual.") else "embedding_norm"
        acc = groups.setdefault(group, {v: 0.0 for v in row})
        for v in row:
            acc[v] += row[v]
        rows[k] = row
        if i % 80 == 0:
            print("metric", i, k, flush=True)
    for acc in groups.values():
        for name, xy, xx, yy in [("cos_donor_qwen", "dq", "d2", "q2"), ("cos_donor_base", "db", "d2", "b2"), ("cos_tau_d_tau_h", "tdth", "td2", "th2"), ("cos_tau_d_posttrain", "tdpq", "td2", "pq2")]:
            denom = math.sqrt(acc[xx] * acc[yy])
            acc[name] = acc[xy] / denom if denom else None
        acc["distance_to_qwen"] = math.sqrt(acc["td2"])
        acc["distance_to_base"] = math.sqrt(acc["db2"])
    return {"groups": groups, "per_tensor": rows}


def build(h, q, donors, a):
    out = Path(a.output)
    out.mkdir(exist_ok=False)
    for p in h.path.iterdir():
        if p.is_file() and p.suffix != ".safetensors" and p.name not in ["README.md", "latest"]:
            shutil.copyfile(p, out / p.name)
    changed = []
    retained = []
    delta2 = 0.0
    nnz = 0
    generator = torch.Generator(device="cpu").manual_seed(a.seed)
    for shard in sorted(set(h.wm.values())):
        tensors = {}
        for k in sorted(key for key, f in h.wm.items() if f == shard):
            original = h.get(k)
            selected = k.startswith("model.language_model.")
            if a.layer_range is not None:
                selected = k.startswith("model.language_model.layers.") and a.layer_range[0] <= int(k.split(".")[3]) < a.layer_range[1]
            if not selected:
                tensors[k] = original
                retained.append(k)
                continue
            base = q.get(k).float()
            deltas = [d.get(k).float() - base for d in donors]
            if a.method == "ties":
                trimmed = []
                for delta in deltas:
                    count = max(1, math.ceil(delta.numel() * a.density))
                    mask = torch.zeros(delta.numel(), dtype=torch.bool)
                    mask[torch.topk(delta.abs().flatten(), count, sorted=False).indices] = True
                    trimmed.append(delta * mask.reshape(delta.shape))
                sign = torch.stack(trimmed).sum(0).sign()
                counts = torch.zeros_like(base)
                merged = torch.zeros_like(base)
                for delta in trimmed:
                    use = (delta.sign() == sign) & (delta != 0)
                    merged += delta * use
                    counts += use
                update = merged / counts.clamp_min(1)
            elif a.method == "dare":
                update = sum(delta * (torch.rand(delta.shape, generator=generator) < a.density) / a.density for delta in deltas) / len(deltas)
            else:
                update = sum(deltas) / len(deltas)
            edited = (original.float() + a.beta * update).to(original.dtype)
            if not torch.isfinite(edited).all():
                raise ValueError("nonfinite " + k)
            actual_delta = edited.float() - original.float()
            delta2 += torch.sum(actual_delta.square(), dtype=torch.float64).item()
            nnz += torch.count_nonzero(actual_delta).item()
            (changed if not torch.equal(edited, original) else retained).append(k)
            tensors[k] = edited
        target = out / shard
        save_file(tensors, str(target), metadata={"format": "pt"})
        del tensors
        print("saved", target, flush=True)
    result = {"time_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()), "method": a.method, "beta": a.beta, "density": a.density, "seed": a.seed, "layer_range": a.layer_range, "holo": str(h.path), "reference": str(q.path), "donors": [str(d.path) for d in donors], "output": str(out), "changed_tensors": changed, "retained_tensors": retained, "changed_elements": nnz, "actual_update_l2": math.sqrt(delta2), "formula": "Holo + beta * mean(donor - Qwen), selected language tensors only; layer_range is half-open; TIES or DARE applied to deltas when specified", "files": {p.name: {"bytes": p.stat().st_size, "sha256": sha(p)} for p in sorted(out.iterdir()) if p.is_file()}}
    atomic_json(out / "merge_manifest.json", result)
    return result


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--holo", default="/workspace/hf/hub/models--Hcompany--Holo-3.1-4B/snapshots/8c88265a5a159bfd1492db9243733dd2e6e04a6e")
    p.add_argument("--reference", default="/root/expo/base")
    p.add_argument("--base", default="/root/expo/base_pt")
    p.add_argument("--donor", action="append", required=True)
    p.add_argument("--output")
    p.add_argument("--report", required=True)
    p.add_argument("--beta", type=float, default=0.5)
    p.add_argument("--method", choices=["arithmetic", "ties", "dare"], default="arithmetic")
    p.add_argument("--density", type=float, default=0.2)
    p.add_argument("--seed", type=int, default=20261108)
    p.add_argument("--layer-range", type=int, nargs=2, metavar=("START", "STOP"))
    p.add_argument("--measure", action="store_true")
    a = p.parse_args()
    if not 0 < a.density <= 1 or not math.isfinite(a.beta):
        p.error("density must be in (0, 1] and beta must be finite")
    h, q = Weights(a.holo), Weights(a.reference)
    if a.layer_range is not None and not 0 <= a.layer_range[0] < a.layer_range[1] <= h.config["text_config"]["num_hidden_layers"]:
        p.error("layer range must be nonempty and within the language layer count")
    donors = [Weights(d) for d in a.donor]
    report = {"compatibility": [compatibility(h, q, d) for d in donors]}
    atomic_json(a.report, report)
    if a.measure:
        qb = Weights(a.base)
        report["metrics"] = {str(d.path): metrics(h, q, d, qb) for d in donors}
        atomic_json(a.report, report)
        for d in donors:
            g = report["metrics"][str(d.path)]["groups"]["language_layers"]
            if not (g["cos_donor_qwen"] > g["cos_donor_base"] and g["distance_to_qwen"] < g["distance_to_base"]):
                raise ValueError("post-trained ancestry gate failed")
    if a.output:
        report["build"] = build(h, q, donors, a)
        atomic_json(a.report, report)
    print("COMPLETE", a.report, flush=True)


if __name__ == "__main__":
    main()
