"""Phase 4: weight surgery without gradients (MIT 'Sparks of Weight-Space Programming' style).

For layer l and unit direction u (residual-stream space), orthogonalise the matrix that WRITES into the
residual stream:  W_down' = W_down - alpha * u (u^T W_down).
Targeted version: only the top-k columns (MLP neurons) of down_proj whose write vector has the largest |u^T W[:, j]|.
Optional: also the attention output projection of the same layer (writers=["mlp", "attn"]).
"""
import holo.settings as S
import json
from pathlib import Path
import numpy as np
import torch


def load_spec(path):
    return json.loads(Path(path).read_text(encoding="utf-8"))


def _directions(spec):
    D = np.load(S.ROOT / spec["direction_file"])
    return {int(l): D["U"][int(l)].astype(np.float32) for l in spec["layers"]}


def _writers(layer, which):
    out = []
    if "mlp" in which:
        out.append(("mlp.down_proj", layer.mlp.down_proj))
    if "attn" in which:
        if hasattr(layer, "self_attn"):
            out.append(("self_attn.o_proj", layer.self_attn.o_proj))
        elif hasattr(layer, "linear_attn"):
            out.append(("linear_attn.out_proj", layer.linear_attn.out_proj))
    return out


@torch.no_grad()
def apply_patch_inplace(model, spec):
    """Edits the weights in place. Returns stats (n weights modified, relative norm of the change)."""
    layers = model.model.language_model.layers
    alpha = float(spec.get("alpha", 1.0)); topk = spec.get("topk")
    stats = {"n_modified": 0, "delta_fro": 0.0, "per_layer": {}}
    for l, u_np in _directions(spec).items():
        for name, lin in _writers(layers[l], spec.get("writers", ["mlp"])):
            W = lin.weight  # [d_model, d_in]
            u = torch.tensor(u_np, device=W.device, dtype=torch.float32); u = u / u.norm()
            Wf = W.float()
            coef = u @ Wf  # [d_in]: contribution of each column to u
            if topk:
                cols = torch.topk(coef.abs(), int(topk)).indices
            else:
                cols = torch.arange(Wf.shape[1], device=W.device)
            delta = alpha * torch.outer(u, coef[cols])  # [d_model, k]
            Wf[:, cols] -= delta
            W.copy_(Wf.to(W.dtype))
            n = int(delta.numel())
            stats["n_modified"] += n
            stats["delta_fro"] += float(delta.norm() ** 2)
            stats["per_layer"][f"{l}.{name}"] = {"cols": int(len(cols)), "n": n,
                                                 "rel_change": float(delta.norm() / W.float().norm()),
                                                 "top_cols": cols[:16].tolist()}
    stats["delta_fro"] = stats["delta_fro"] ** 0.5
    total = sum(p.numel() for p in model.parameters())
    stats["total_params"] = int(total)
    stats["pct_modified"] = 100.0 * stats["n_modified"] / total
    return stats


def steering_from_spec(spec):
    return _directions(spec), float(spec.get("alpha", 1.0))


def save_patched(holo, spec, out_dir):
    out_dir = Path(out_dir); out_dir.mkdir(parents=True, exist_ok=True)
    holo.model.save_pretrained(out_dir, safe_serialization=True)
    holo.processor.save_pretrained(out_dir)
    (out_dir / "patch_spec.json").write_text(json.dumps(spec, indent=1), encoding="utf-8")
