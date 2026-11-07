"""Build a vLLM-servable patched checkpoint of Holo-3.1-4B from a patch_spec (pod, /workspace/venv).

The checkpoint is NOT written with save_pretrained: the pod's venv has transformers 5.x while vLLM runs on 4.57, so
the output keeps the original HF snapshot (tokenizer, key names) and only rewrites the shards holding edited tensors;
untouched shards are symlinks to the original blobs.

Spec kinds:
  surgery (default)  holo.surgery format: direction_file, layers, alpha, topk, writers (apply_patch_inplace).
                     Projection removal W' = W - alpha u u^T W on the writers of the listed layers; alpha > 1
                     pushes the u component negative.
  steering           {"kind": "steering", "direction_file", "layers": [l], "alpha"}: the residual-projection hook
                     at layer l compiled as an orthogonalisation of every attn+mlp writer of layers 0..l against u_l.
                     Approximation of the hook (the embedding's u component is kept: embeddings are tied to lm_head).
  lm_head            {"kind": "lm_head", "tokens": ["answer", ...] and/or "token_ids": [...], "delta_file": npz with
                     "delta" [n_tokens, d] or [d], "alpha"}: lm_head rows of those tokens += alpha * delta.
                     The snapshot is tied but already stores lm_head.weight (== embed_tokens): that tensor gets the
                     edit and tie_word_embeddings becomes false, so the input embeddings stay unchanged.
  delta              {"kind": "delta", "edits": [{"key": <checkpoint tensor name>, "cols": [...] | "rows": [...],
                     "delta_file": npz, "delta_key": "delta", "alpha": 1.0}, ...]}: raw column / row additions,
                     W[:, cols] += alpha * delta ([d_out] or [d_out, n_cols]) or W[rows] += alpha * delta
                     ([d_in] or [n_rows, d_in]). No model load. Editing lm_head.weight unties the checkpoint.
Usage: PYTHONPATH=. HOLO_MODEL=Hcompany/Holo-3.1-4B python scripts/make_patched_ckpt.py <spec.json> <out_dir>
"""
import holo.settings as S
import json, shutil, sys
from pathlib import Path
import numpy as np
import torch
from huggingface_hub import snapshot_download
from safetensors.torch import load_file, save_file
from holo.surgery import apply_patch_inplace, load_spec

EMBED = "model.language_model.embed_tokens.weight"
LM_HEAD = "lm_head.weight"


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


def writer_edits(spec, src, out_dir, weight_map):
    """{checkpoint key: new tensor} for surgery / steering specs, computed by apply_patch_inplace on the HF model."""
    from holo.model import Holo
    sspec = surgery_spec(spec, out_dir)
    holo = Holo(str(src))
    stats = apply_patch_inplace(holo.model, sspec)
    params = dict(holo.model.named_parameters())
    edited = {f"model.language_model.layers.{k}.weight" for k in stats["per_layer"]}
    missing = sorted(k for k in edited if k not in weight_map or k not in params)
    assert not missing, f"edited tensors not found under checkpoint key names: {missing[:5]}"
    return {k: params[k].detach().cpu() for k in edited}, {"applied_spec": sspec, "stats": stats}


def lm_head_edit(spec, src, weight_map):
    """The untied lm_head: embed_tokens with alpha * delta added to the rows of the given tokens."""
    assert torch.equal(load_file(src / weight_map[LM_HEAD])[LM_HEAD], load_file(src / weight_map[EMBED])[EMBED])
    from transformers import AutoTokenizer
    tok = AutoTokenizer.from_pretrained(src)
    ids = [int(i) for i in spec.get("token_ids", [])]
    for t in spec.get("tokens", []):
        i = tok.convert_tokens_to_ids(t)
        assert i is not None and i != tok.unk_token_id, f"token {t!r} is not a single vocabulary token"
        ids.append(int(i))
    assert ids and len(set(ids)) == len(ids), f"need distinct token ids, got {ids}"
    E = load_file(src / weight_map[EMBED])[EMBED]
    delta = torch.from_numpy(np.load(S.ROOT / spec["delta_file"])["delta"]).float()
    delta = delta.expand(len(ids), E.shape[1]) if delta.dim() == 1 else delta
    assert delta.shape == (len(ids), E.shape[1]), f"delta {tuple(delta.shape)} for {len(ids)} tokens"
    W = E.clone()
    W[ids] = (E[ids].float() + float(spec.get("alpha", 1.0)) * delta).to(E.dtype)
    rows = {str(i): tok.convert_ids_to_tokens(i) for i in ids}
    return W, {"token_ids": ids, "tokens": rows}


def delta_edits(spec, src, weight_map):
    """{checkpoint key: new tensor} for raw row / column additions."""
    out, applied = {}, []
    for e in spec["edits"]:
        k = e["key"]
        assert k in weight_map, f"unknown checkpoint tensor {k}"
        W = out[k] if k in out else load_file(src / weight_map[k])[k].clone()
        D = np.load(S.ROOT / e["delta_file"])
        delta = torch.from_numpy(np.asarray(D[e.get("delta_key", "delta")])).float()
        alpha = float(e.get("alpha", 1.0))
        assert ("cols" in e) != ("rows" in e), "each edit needs exactly one of cols / rows"
        if "cols" in e:
            idx = [int(c) for c in e["cols"]]
            delta = delta[:, None].expand(W.shape[0], len(idx)) if delta.dim() == 1 else delta
            assert delta.shape == (W.shape[0], len(idx)), f"{k}: delta {tuple(delta.shape)} for cols {idx}"
            W[:, idx] = (W[:, idx].float() + alpha * delta).to(W.dtype)
        else:
            idx = [int(r) for r in e["rows"]]
            delta = delta[None].expand(len(idx), W.shape[1]) if delta.dim() == 1 else delta
            assert delta.shape == (len(idx), W.shape[1]), f"{k}: delta {tuple(delta.shape)} for rows {idx}"
            W[idx] = (W[idx].float() + alpha * delta).to(W.dtype)
        out[k] = W
        applied.append({"key": k, "cols" if "cols" in e else "rows": idx, "alpha": alpha,
                        "delta_norm": float(delta.norm())})
    return out, {"edits_applied": applied}


def untie(config):
    assert config["tie_word_embeddings"] and config["text_config"]["tie_word_embeddings"]
    config["tie_word_embeddings"] = False
    config["text_config"]["tie_word_embeddings"] = False


def main(spec_path, out_dir):
    out_dir = Path(out_dir)
    assert not (out_dir / "model.safetensors.index.json").exists(), f"{out_dir} already holds a checkpoint"
    out_dir.mkdir(parents=True, exist_ok=True)
    src = Path(snapshot_download(S.MODEL_ID, local_files_only=True))
    spec = load_spec(spec_path)
    index = json.loads((src / "model.safetensors.index.json").read_text())
    config = json.loads((src / "config.json").read_text())
    weight_map = index["weight_map"]
    kind = spec.get("kind", "surgery")

    if kind == "lm_head":
        W, info = lm_head_edit(spec, src, weight_map)
        replaced = {LM_HEAD: W}
        untie(config)
    elif kind == "delta":
        replaced, info = delta_edits(spec, src, weight_map)
        if LM_HEAD in replaced:
            untie(config)
    else:
        replaced, info = writer_edits(spec, src, out_dir, weight_map)

    by_shard = {}
    for k in replaced:
        by_shard.setdefault(weight_map[k], []).append(k)
    per_key = {}
    for f in sorted(p.name for p in src.iterdir()):
        if f in by_shard:
            tensors = load_file(src / f)
            for k in by_shard[f]:
                new = replaced[k].to(tensors[k].dtype).contiguous()
                assert new.shape == tensors[k].shape, k
                d = new.float() - tensors[k].float()
                per_key[k] = {"max_abs_diff": float(d.abs().max()),
                              "rel_fro": float(d.norm() / tensors[k].float().norm()),
                              "rows_changed": int((d != 0).any(dim=1).sum())}
                tensors[k] = new
            save_file(tensors, out_dir / f, metadata={"format": "pt"})
        elif f.endswith(".safetensors"):
            (out_dir / f).symlink_to((src / f).resolve())
        elif f != "config.json":
            shutil.copyfile((src / f).resolve(), out_dir / f)
    (out_dir / "config.json").write_text(json.dumps(config, indent=2))

    manifest = {"source": str(src), "spec": spec, **info, "rewritten_shards": sorted(by_shard),
                "edited_tensors": per_key}
    (out_dir / "patch_spec.json").write_text(json.dumps(spec, indent=1))
    (out_dir / "patch_manifest.json").write_text(json.dumps(manifest, indent=1))
    print(json.dumps({"out": str(out_dir), "kind": kind, "n_edited_tensors": len(per_key),
                      "max_rel_fro": max(v["rel_fro"] for v in per_key.values()),
                      **({"token_ids": info["token_ids"]} if kind == "lm_head" else {})}))


if __name__ == "__main__":
    main(*sys.argv[1:3])
