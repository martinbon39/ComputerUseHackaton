"""Compare a patched checkpoint with the original Holo snapshot, independently of the builder (pod, /workspace/venv).

1. Tensors: every key of the index, original vs patched (torch.equal), with the number of differing rows (lm_head
   rows = token ids). Config keys that differ are listed.
2. Logits: one forward pass on a short prompt; token ids whose next-token logit moved by > 1e-3 (positive control).
3. Outputs (unless --no_generate): 3 prompts (2 text, 1 screenshot) through HF generate, greedy and seeded sampling.
Usage: PYTHONPATH=. HOLO_MODEL=Hcompany/Holo-3.1-4B python scripts/check_ckpt_equiv.py <patched_dir> <image.png>
       [--out f.json] [--no_generate] [--device cpu|cuda]
"""
import sys
if "cpu" in sys.argv:
    # FLA / causal-conv1d kernels are CUDA-only: make transformers take the pure PyTorch path (as bench_gen --no-fla)
    import transformers.utils.import_utils as iu
    for n in ("is_flash_linear_attention_available", "is_causal_conv1d_available"):
        if hasattr(iu, n):
            setattr(iu, n, lambda: False)
    sys.modules["fla"] = None; sys.modules["causal_conv1d"] = None
import holo.settings as S
import gc, json
from pathlib import Path
import torch
from huggingface_hub import snapshot_download
from PIL import Image
from safetensors import safe_open
from transformers import AutoModelForImageTextToText, AutoProcessor

PROMPTS = ["Describe in two sentences what a computer-use agent should do before declaring a task complete.",
           "List the steps to rename a file in a Linux terminal."]
IMAGE_PROMPT = "What is on this screen? Where would you click to submit?"

def flat(c, prefix=""):
    out = {}
    for k, v in c.items():
        out.update(flat(v, f"{prefix}{k}.") if isinstance(v, dict) else {f"{prefix}{k}": v})
    return out


def diff_tensors(src, dst):
    wm = json.loads((src / "model.safetensors.index.json").read_text())["weight_map"]
    assert wm == json.loads((dst / "model.safetensors.index.json").read_text())["weight_map"]
    differing = {}
    for shard in sorted(set(wm.values())):
        with safe_open(src / shard, "pt") as a, safe_open(dst / shard, "pt") as b:
            for k in a.keys():
                x, y = a.get_tensor(k), b.get_tensor(k)
                if not torch.equal(x, y):
                    rows = torch.nonzero((x != y).reshape(x.shape[0], -1).any(dim=1)).flatten().tolist()
                    differing[k] = {"n_rows": len(rows), "rows": rows[:20]}
    fa, fb = (flat(json.loads((d / "config.json").read_text())) for d in (src, dst))
    config_diff = {k: [fa.get(k), fb.get(k)] for k in sorted(fa.keys() | fb.keys()) if fa.get(k) != fb.get(k)}
    return len(wm), differing, config_diff


def conversations(image):
    convs = [[{"role": "user", "content": [{"type": "text", "text": p}]}] for p in PROMPTS]
    convs.append([{"role": "user", "content": [{"type": "image", "image": image},
                                               {"type": "text", "text": IMAGE_PROMPT}]}])
    return convs


def run(path, proc, image, device, generate):
    model = AutoModelForImageTextToText.from_pretrained(path, dtype=torch.bfloat16).to(device).eval()
    tied = model.lm_head.weight.data_ptr() == model.get_input_embeddings().weight.data_ptr()
    inputs = [proc.apply_chat_template(c, add_generation_prompt=True, tokenize=True, return_dict=True,
                                       return_tensors="pt", enable_thinking=False).to(device)
              for c in conversations(image)]
    with torch.no_grad():
        logits = model(**inputs[0]).logits[0, -1].float().cpu()
    out = []
    for inp in inputs if generate else []:
        n = inp["input_ids"].shape[1]
        row = {}
        for mode in ("greedy", "sample_seed0"):
            torch.manual_seed(0)
            kw = {"do_sample": False} if mode == "greedy" else {"do_sample": True, "temperature": 0.8, "top_p": 0.95}
            with torch.no_grad():
                ids = model.generate(**inp, max_new_tokens=48, **kw)[0, n:].tolist()
            row[mode] = {"ids": ids, "text": proc.decode(ids, skip_special_tokens=True)}
        out.append(row)
    del model; gc.collect()
    if device == "cuda":
        torch.cuda.empty_cache()
    return {"tied": tied, "logits": logits, "gen": out}


def main():
    args = sys.argv[1:]
    dst, image_path = Path(args[0]), args[1]
    out_json = args[args.index("--out") + 1] if "--out" in args else None
    device = args[args.index("--device") + 1] if "--device" in args else "cuda"
    generate = "--no_generate" not in args
    src = Path(snapshot_download(S.MODEL_ID, local_files_only=True))
    n_keys, differing, config_diff = diff_tensors(src, dst)
    proc = AutoProcessor.from_pretrained(src)
    image = Image.open(image_path).convert("RGB")
    a, b = run(str(src), proc, image, device, generate), run(str(dst), proc, image, device, generate)
    dl = b["logits"] - a["logits"]
    moved = torch.nonzero(dl.abs() > 1e-3).flatten().tolist()
    res = {"patched": str(dst), "n_keys": n_keys, "n_differing_tensors": len(differing), "differing": differing,
           "config_diff": config_diff, "lm_head_tied": [a["tied"], b["tied"]],
           "logits_max_abs_diff": float(dl.abs().max()), "logits_moved_ids": moved[:50],
           "logits_moved": {str(i): float(dl[i]) for i in moved[:50]}}
    if generate:
        same = [{m: a["gen"][i][m]["ids"] == b["gen"][i][m]["ids"] for m in a["gen"][i]} for i in range(len(a["gen"]))]
        res.update({"outputs_identical": same, "all_identical": all(all(s.values()) for s in same),
                    "orig_text": [r["greedy"]["text"] for r in a["gen"]],
                    "patched_text": [r["greedy"]["text"] for r in b["gen"]]})
    if out_json:
        Path(out_json).write_text(json.dumps(res, indent=1))
    keys = ("n_keys", "n_differing_tensors", "differing", "config_diff", "lm_head_tied",
            "logits_max_abs_diff", "logits_moved", "outputs_identical", "all_identical")
    print(json.dumps({k: res[k] for k in keys if k in res}))
    if generate:
        print("orig   :", res["orig_text"])
        print("patched:", res["patched_text"])


if __name__ == "__main__":
    main()
