"""ExPO weight extrapolation (Zheng et al. 2024, arXiv 2404.16792) of Holo-3.1-4B from its base Qwen/Qwen3.5-4B (pod).

W(lam) = W_base + lam * (W_holo - W_base), computed in float64, written in Holo's dtype (bf16).
Only tensors present in both checkpoints with the same shape are extrapolated, and only those in --scope:
  lang   model.language_model.layers.* + model.language_model.norm.weight (default)
  vision model.visual.*
  all    every shared tensor except the tied embedding / lm_head
The tied embed_tokens / lm_head stay Holo's: Holo retrained them (row cosine to base < 0.2 on >= 10% of rows, norm x2),
so extrapolating them moves the output vocabulary itself. Same layout as make_patched_ckpt.py: Holo's snapshot files,
rewritten shards, config/tokenizer/processor copied. lam=1.0 is checked to give Holo bit-exactly on every edited tensor.
  attn   model.language_model.layers.*.self_attn.* / linear_attn.* (layer norms excluded)
  mlp    model.language_model.layers.*.mlp.*
--rv A B: task-vector addition instead, W = W_holo + lam * (W_A - W_B) (e.g. A = Qwen3.5-4B, B = Qwen3.5-4B-Base:
the Qwen post-training vector), same scopes, A and B both needed with Holo's shape; lam=0 is checked to give Holo.
Usage: [EXPO_BASE=<Qwen3.5-4B snapshot copy>] /workspace/venv/bin/python scripts/make_expo_ckpt.py <lam> <out_dir>
       [lang|vision|all|attn|mlp ...] [--rv <A_dir> <B_dir>]
/workspace has a 100 GB quota shared by the fleet: the base copy and the outputs live on /root and /dev/shm.
"""
import glob, json, os, shutil, sys
from pathlib import Path
import torch
from safetensors import safe_open
from safetensors.torch import load_file, save_file

HUB = "/workspace/hf/hub"
BASE = Path(os.environ.get("EXPO_BASE") or glob.glob(f"{HUB}/models--Qwen--Qwen3.5-4B/snapshots/*")[0])
HOLO = Path(glob.glob(f"{HUB}/models--Hcompany--Holo-3.1-4B/snapshots/*")[0])
SCOPES = {"lang": lambda k: k.startswith("model.language_model.layers.") or k == "model.language_model.norm.weight",
          "vision": lambda k: k.startswith("model.visual."),
          "all": lambda k: k not in ("model.language_model.embed_tokens.weight", "lm_head.weight"),
          "attn": lambda k: k.startswith("model.language_model.layers.") and (".self_attn." in k or ".linear_attn." in k),
          "mlp": lambda k: k.startswith("model.language_model.layers.") and ".mlp." in k}


def tensor_index(d):
    wm = json.loads((d / "model.safetensors.index.json").read_text())["weight_map"]
    out = {}
    for f in sorted(set(wm.values())):
        with safe_open(d / f, "pt") as s:
            for k in s.keys():
                out[k] = (d / f, tuple(s.get_slice(k).get_shape()))
    return out


def read(info, k):
    with safe_open(info[k][0], "pt") as s:
        return s.get_tensor(k)


def main(lam, out_dir, *scopes):
    rv = None
    if "--rv" in scopes:
        i = scopes.index("--rv")
        rv, scopes = (Path(scopes[i + 1]), Path(scopes[i + 2])), scopes[:i] + scopes[i + 3:]
    lam, out_dir, scopes = float(lam), Path(out_dir), scopes or ("lang",)
    assert not (out_dir / "model.safetensors.index.json").exists(), f"{out_dir} already holds a checkpoint"
    out_dir.mkdir(parents=True, exist_ok=True)
    binfo = tensor_index(BASE) if rv is None else tensor_index(rv[0])
    b2info = None if rv is None else tensor_index(rv[1])
    hwm = json.loads((HOLO / "model.safetensors.index.json").read_text())["weight_map"]
    per_key, kept, identity_bad = {}, {"holo_only": [], "shape_mismatch": [], "out_of_scope": 0}, 0
    for f in sorted(p.name for p in HOLO.iterdir()):
        if not f.endswith(".safetensors"):
            if f != "model.safetensors.index.json":
                shutil.copyfile((HOLO / f).resolve(), out_dir / f)
            continue
        tensors = load_file(HOLO / f)
        for k, h in tensors.items():
            if k not in binfo or (b2info is not None and k not in b2info):
                kept["holo_only"].append(k)
                continue
            if not any(SCOPES[s](k) for s in scopes):
                kept["out_of_scope"] += 1
                continue
            b = read(binfo, k)
            b2 = None if b2info is None else read(b2info, k)
            if tuple(b.shape) != tuple(h.shape) or (b2 is not None and tuple(b2.shape) != tuple(h.shape)):
                kept["shape_mismatch"].append(k)
                continue
            hd, bd = h.double(), b.double()
            if b2 is None:
                identity_bad += int(not torch.equal((bd + 1.0 * (hd - bd)).to(h.dtype), h))
                new = (bd + lam * (hd - bd)).to(h.dtype).contiguous()
            else:
                v = bd - b2.double()
                identity_bad += int(not torch.equal((hd + 0.0 * v).to(h.dtype), h))
                new = (hd + lam * v).to(h.dtype).contiguous()
            d = new.double() - hd
            per_key[k] = {"rel_fro_vs_holo": float(d.norm() / hd.norm()), "base_dtype": str(b.dtype)}
            tensors[k] = new
        save_file(tensors, out_dir / f, metadata={"format": "pt"})
    shutil.copyfile((HOLO / "model.safetensors.index.json").resolve(), out_dir / "model.safetensors.index.json")
    rel = sorted(v["rel_fro_vs_holo"] for v in per_key.values())
    method = "ExPO W_base + lam (W_holo - W_base)" if rv is None else f"task vector W_holo + lam (W_{rv[0]} - W_{rv[1]})"
    manifest = {"method": method, "lam": lam, "scopes": scopes, "base": str(BASE if rv is None else rv),
                "holo": str(HOLO), "n_extrapolated": len(per_key), "identity_lam_tensors_differing_from_holo": identity_bad,
                "kept_holo": kept, "rel_fro_vs_holo_median": rel[len(rel) // 2], "rel_fro_vs_holo_max": rel[-1],
                "tensors": per_key}
    (out_dir / "expo_manifest.json").write_text(json.dumps(manifest, indent=1))
    print(json.dumps({k: manifest[k] for k in ("lam", "scopes", "n_extrapolated", "identity_lam_tensors_differing_from_holo",
                                               "rel_fro_vs_holo_median", "rel_fro_vs_holo_max")},),
          json.dumps({"holo_only": kept["holo_only"], "shape_mismatch": kept["shape_mismatch"],
                      "out_of_scope": kept["out_of_scope"]}))


if __name__ == "__main__":
    main(*sys.argv[1:])
