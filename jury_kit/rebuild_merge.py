#!/usr/bin/env python3
"""Level 2: rebuild the merged checkpoint from the three public Hugging Face models and compare sha256.

    theta = theta_Holo + 0.5 * (theta_CUA - theta_Qwen)      language tower only (keys 'model.language_model.*')

Vision tower, lm_head and every non-language tensor stay exactly Holo's. Arithmetic in float32, result cast back to
bfloat16 (the dtype of Holo). Same recipe as our merge_v2.py (arithmetic, beta 0.5, no layer range).

Pinned revisions (exact commits):
  Hcompany/Holo-3.1-4B                                   8c88265a5a159bfd1492db9243733dd2e6e04a6e
  Qwen/Qwen3.5-4B                                        851bf6e806efd8d0a36b00ddf55e13ccb7b8cd0a
  OnAnOrange/CUA-Lite-Qwen3.5-4B-ScaleCUA-gpt5_5-epoch3-public   df6eba93efb2df3ed9adc810e0f7f4e038959c74

Modes
  --check N   cheap: recompute N tensors (default 2) and compare them with the same tensors in a merged checkpoint
              given by --merged DIR (e.g. the one published on HF). Needs the three inputs, not the full build.
  --build DIR full rebuild into DIR (about 9 GB, CPU, a few minutes), then compare file sha256 with expected_sha256.json.
Inputs are downloaded from the Hub unless --holo/--qwen/--cua point to local snapshot directories.
"""
import argparse, hashlib, json, pathlib, shutil, sys

REVS = {
    "holo": ("Hcompany/Holo-3.1-4B", "8c88265a5a159bfd1492db9243733dd2e6e04a6e"),
    "qwen": ("Qwen/Qwen3.5-4B", "851bf6e806efd8d0a36b00ddf55e13ccb7b8cd0a"),
    "cua": ("OnAnOrange/CUA-Lite-Qwen3.5-4B-ScaleCUA-gpt5_5-epoch3-public", "df6eba93efb2df3ed9adc810e0f7f4e038959c74"),
}
BETA = 0.5
HERE = pathlib.Path(__file__).resolve().parent


def fetch(key, override):
    if override:
        return pathlib.Path(override)
    from huggingface_hub import snapshot_download
    repo, rev = REVS[key]
    return pathlib.Path(snapshot_download(repo, revision=rev, allow_patterns=["*.safetensors", "*.json", "*.jinja", "*.txt"]))


class Weights:
    def __init__(self, path):
        from safetensors import safe_open
        self.path = path
        idx = path / "model.safetensors.index.json"
        if idx.exists():
            self.wm = json.loads(idx.read_text())["weight_map"]
        else:
            files = sorted(path.glob("*.safetensors"))
            self.wm = {k: f.name for f in files for k in safe_open(str(f), "pt").keys()}
        self.h = {f: safe_open(str(path / f), "pt", device="cpu") for f in set(self.wm.values())}

    def get(self, k):
        return self.h[self.wm[k]].get_tensor(k)


def merge_tensor(holo, qwen, cua, k):
    orig = holo.get(k)
    if not k.startswith("model.language_model."):
        return orig
    delta = cua.get(k).float() - qwen.get(k).float()
    return (orig.float() + BETA * delta).to(orig.dtype)


def sha256(p):
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for b in iter(lambda: f.read(8 << 20), b""):
            h.update(b)
    return h.hexdigest()


def check(a, holo, qwen, cua):
    import torch
    merged = Weights(pathlib.Path(a.merged))
    lang = sorted(k for k in holo.wm if k.startswith("model.language_model.layers.") and k.endswith("weight")
                  and len(holo.h[holo.wm[k]].get_slice(k).get_shape()) == 2)
    picks = a.key or [lang[len(lang) // 3], lang[2 * len(lang) // 3], "model.language_model.embed_tokens.weight"][: max(a.check, 1)]
    ok = True
    for k in picks:
        mine, theirs, orig = merge_tensor(holo, qwen, cua, k), merged.get(k), holo.get(k)
        same = torch.equal(mine, theirs)
        moved = not torch.equal(mine, orig)
        print(f"{'OK ' if same else 'BAD'} {k}  dtype={mine.dtype}  bit-identical={same}  differs-from-Holo={moved}  "
              f"max|merged-Holo|={float((mine.float() - orig.float()).abs().max()):.3e}")
        ok &= same  # 'moved' is informative only: BF16 rounding leaves some tensors unchanged
    return ok


def build(a, holo, qwen, cua):
    from safetensors.torch import save_file
    out = pathlib.Path(a.build)
    out.mkdir(parents=True, exist_ok=False)
    for p in holo.path.iterdir():
        if p.is_file() and p.suffix != ".safetensors" and p.name not in ("README.md", "latest"):
            shutil.copyfile(p, out / p.name)
    for shard in sorted(set(holo.wm.values())):
        tensors = {k: merge_tensor(holo, qwen, cua, k) for k in sorted(k for k, f in holo.wm.items() if f == shard)}
        save_file(tensors, str(out / shard), metadata={"format": "pt"})
        print("saved", shard, flush=True)
    exp = json.loads((HERE / "expected_sha256.json").read_text())["files"]
    ok = True
    for name, e in exp.items():
        got = sha256(out / name)
        good = got == e["sha256"]
        ok &= good
        print(f"{'MATCH' if good else 'DIFFERENT'}  {name}\n   rebuilt  {got}\n   expected {e['sha256']}")
    return ok


def main():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--check", type=int, metavar="N")
    p.add_argument("--merged", help="directory of a merged checkpoint to compare tensors against (with --check)")
    p.add_argument("--key", action="append", help="tensor name to compare (repeatable); default: 2 language-layer matrices")
    p.add_argument("--build", metavar="DIR")
    p.add_argument("--holo"); p.add_argument("--qwen"); p.add_argument("--cua")
    a = p.parse_args()
    if not a.check and not a.build:
        p.error("choose --check N --merged DIR, or --build DIR")
    if a.check and not a.merged:
        p.error("--check needs --merged DIR")
    holo, qwen, cua = (Weights(fetch(k, getattr(a, k))) for k in ("holo", "qwen", "cua"))
    ok = True
    if a.check:
        ok &= check(a, holo, qwen, cua)
    if a.build:
        ok &= build(a, holo, qwen, cua)
    print("RESULT:", "PASS" if ok else "FAIL")
    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main()
