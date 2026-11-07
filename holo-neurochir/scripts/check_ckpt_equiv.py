"""Compare a patched checkpoint with the original Holo snapshot, independently of the builder (pod, /workspace/venv).

1. Tensors: every key of the index, original vs patched (torch.equal) -> list of differing keys.
2. Outputs: the same 3 prompts (2 text, 1 screenshot) through HF generate, greedy and seeded sampling, on each model.
Usage: PYTHONPATH=. HOLO_MODEL=Hcompany/Holo-3.1-4B python scripts/check_ckpt_equiv.py <patched_dir> <image.png> [--out f.json]
"""
import holo.settings as S
import gc, json, sys
from pathlib import Path
import torch
from huggingface_hub import snapshot_download
from PIL import Image
from safetensors import safe_open
from transformers import AutoModelForImageTextToText, AutoProcessor

PROMPTS = ["Describe in two sentences what a computer-use agent should do before declaring a task complete.",
           "List the steps to rename a file in a Linux terminal."]
IMAGE_PROMPT = "What is on this screen? Where would you click to submit?"


def diff_tensors(src, dst):
    wm = json.loads((src / "model.safetensors.index.json").read_text())["weight_map"]
    differing = []
    for shard in sorted(set(wm.values())):
        with safe_open(src / shard, "pt") as a, safe_open(dst / shard, "pt") as b:
            assert set(a.keys()) == set(b.keys()), shard
            differing += [k for k in a.keys() if not torch.equal(a.get_tensor(k), b.get_tensor(k))]
    return len(wm), differing


def generate_all(path, proc, image):
    model = AutoModelForImageTextToText.from_pretrained(path, dtype=torch.bfloat16).to("cuda").eval()
    convs = [[{"role": "user", "content": [{"type": "text", "text": p}]}] for p in PROMPTS]
    convs.append([{"role": "user", "content": [{"type": "image", "image": image}, {"type": "text", "text": IMAGE_PROMPT}]}])
    out = []
    for conv in convs:
        inp = proc.apply_chat_template(conv, add_generation_prompt=True, tokenize=True, return_dict=True,
                                       return_tensors="pt", enable_thinking=False).to("cuda")
        n = inp["input_ids"].shape[1]
        row = {}
        for mode in ("greedy", "sample_seed0"):
            torch.manual_seed(0)
            kw = {"do_sample": False} if mode == "greedy" else {"do_sample": True, "temperature": 0.8, "top_p": 0.95}
            with torch.no_grad():
                ids = model.generate(**inp, max_new_tokens=48, **kw)[0, n:].tolist()
            row[mode] = {"ids": ids, "text": proc.decode(ids, skip_special_tokens=True)}
        out.append(row)
    del model; gc.collect(); torch.cuda.empty_cache()
    return out


def main():
    dst, image_path = Path(sys.argv[1]), sys.argv[2]
    out_json = sys.argv[sys.argv.index("--out") + 1] if "--out" in sys.argv else None
    src = Path(snapshot_download(S.MODEL_ID, local_files_only=True))
    n_keys, differing = diff_tensors(src, dst)
    proc = AutoProcessor.from_pretrained(src)
    image = Image.open(image_path).convert("RGB")
    a, b = generate_all(str(src), proc, image), generate_all(str(dst), proc, image)
    same = [{m: a[i][m]["ids"] == b[i][m]["ids"] for m in a[i]} for i in range(len(a))]
    res = {"patched": str(dst), "n_keys": n_keys, "n_differing_tensors": len(differing), "differing": differing,
           "outputs_identical": same, "all_identical": all(all(s.values()) for s in same),
           "orig_text": [r["greedy"]["text"] for r in a], "patched_text": [r["greedy"]["text"] for r in b]}
    if out_json:
        Path(out_json).write_text(json.dumps(res, indent=1))
    print(json.dumps({k: res[k] for k in ("n_keys", "n_differing_tensors", "outputs_identical", "all_identical")}))
    print("orig   :", res["orig_text"])
    print("patched:", res["patched_text"])


if __name__ == "__main__":
    main()
