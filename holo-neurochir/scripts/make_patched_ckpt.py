"""Build a vLLM-servable patched checkpoint of Holo-3.1-4B from a patch_spec (pod, /workspace/venv).

The edit itself is holo.surgery.apply_patch_inplace. The checkpoint is NOT written with save_pretrained: the pod's
venv has transformers 5.x while vLLM runs on 4.57, so the output keeps the original HF snapshot byte for byte
(config, tokenizer, index, key names) and only rewrites the shards holding edited tensors; untouched shards are
symlinks to the original blobs.

Spec kinds:
  surgery (default)  holo.surgery format: direction_file, layers, alpha, topk, writers.
  steering           {"kind": "steering", "direction_file", "layers": [l], "alpha"}: the residual-projection hook
                     at layer l compiled as an orthogonalisation of every attn+mlp writer of layers 0..l against u_l.
                     Approximation of the hook (the embedding's u component is kept: embeddings are tied to lm_head).
Usage: PYTHONPATH=. HOLO_MODEL=Hcompany/Holo-3.1-4B python scripts/make_patched_ckpt.py <spec.json> <out_dir>
"""
import holo.settings as S
import json, shutil, sys
from pathlib import Path
import numpy as np
import torch
from huggingface_hub import snapshot_download
from safetensors.torch import load_file, save_file
from holo.model import Holo
from holo.surgery import apply_patch_inplace, load_spec


def surgery_spec(spec, out_dir):
    if spec.get("kind", "surgery") == "surgery":
        return spec
    assert spec["kind"] == "steering" and len(spec["layers"]) == 1, "steering spec: exactly one layer"
    l = int(spec["layers"][0])
    U = np.load(S.ROOT / spec["direction_file"])["U"]
    derived = out_dir / "steering_directions.npz"
    np.savez(derived, U=np.repeat(U[l][None], l + 1, axis=0))
    return {"direction_file": str(derived), "layers": list(range(l + 1)), "alpha": spec["alpha"],
            "topk": None, "writers": ["mlp", "attn"], "compiled_from": spec}


def main(spec_path, out_dir):
    out_dir = Path(out_dir)
    assert not (out_dir / "model.safetensors.index.json").exists(), f"{out_dir} already holds a checkpoint"
    out_dir.mkdir(parents=True, exist_ok=True)
    src = Path(snapshot_download(S.MODEL_ID, local_files_only=True))
    spec = load_spec(spec_path)
    sspec = surgery_spec(spec, out_dir)

    holo = Holo(str(src))
    stats = apply_patch_inplace(holo.model, sspec)
    prefix = "model.language_model.layers"
    edited = {f"{prefix}.{k}.weight" for k in stats["per_layer"]}
    params = dict(holo.model.named_parameters())
    weight_map = json.loads((src / "model.safetensors.index.json").read_text())["weight_map"]
    missing = sorted(k for k in edited if k not in weight_map or k not in params)
    assert not missing, f"edited tensors not found under checkpoint key names: {missing[:5]}"

    by_shard = {}
    for k in edited:
        by_shard.setdefault(weight_map[k], []).append(k)
    per_key = {}
    for f in sorted(p.name for p in src.iterdir()):
        if f in by_shard:
            tensors = load_file(src / f)
            for k in by_shard[f]:
                new = params[k].detach().to("cpu", tensors[k].dtype).contiguous()
                assert new.shape == tensors[k].shape, k
                d = new.float() - tensors[k].float()
                per_key[k] = {"max_abs_diff": float(d.abs().max()),
                              "rel_fro": float(d.norm() / tensors[k].float().norm())}
                tensors[k] = new
            save_file(tensors, out_dir / f, metadata={"format": "pt"})
        elif f.endswith(".safetensors"):
            (out_dir / f).symlink_to((src / f).resolve())
        else:
            shutil.copyfile((src / f).resolve(), out_dir / f)

    manifest = {"source": str(src), "spec": spec, "applied_spec": sspec, "stats": stats,
                "rewritten_shards": sorted(by_shard), "edited_tensors": per_key}
    (out_dir / "patch_spec.json").write_text(json.dumps(spec, indent=1))
    (out_dir / "patch_manifest.json").write_text(json.dumps(manifest, indent=1))
    print(json.dumps({"out": str(out_dir), "n_edited_tensors": len(per_key), "pct_modified": stats["pct_modified"],
                      "max_rel_fro": max(v["rel_fro"] for v in per_key.values())}))


if __name__ == "__main__":
    main(*sys.argv[1:3])
