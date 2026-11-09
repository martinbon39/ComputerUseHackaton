from common import *
import argparse
import shutil
import time
from safetensors.torch import load_file, save_file


@torch.inference_mode()
def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("out")
    args = ap.parse_args()
    out = Path(args.out)
    assert out.parent == Path("/dev/shm") and out.name.startswith("regmean_") and not out.exists()
    pack = torch.load(ROOT / "candidate_factors.pt", weights_only=True, map_location="cpu")
    factors = pack["learned"]
    assert set(factors) == set(writer_names())
    index = json.loads((HOLO / "model.safetensors.index.json").read_text())
    shards = sorted(set(index["weight_map"].values()))
    required = sum((HOLO / shard).stat().st_size for shard in shards) + 1_000_000_000
    assert shutil.disk_usage(out.parent).free > required, ("insufficient shared memory", required)
    out.mkdir()
    edits = {}
    count = 0
    total = 0
    start = time.monotonic()
    for shard in shards:
        tensors = load_file(HOLO / shard)
        for name, weight in list(tensors.items()):
            count += 1
            total += weight.numel()
            if name not in factors:
                continue
            f = factors[name]
            assert f["left"].dtype == f["right"].dtype == torch.float64
            delta = f["left"] @ f["right"]
            assert delta.shape == weight.shape and torch.isfinite(delta).all()
            new = (weight.double() + delta).to(weight.dtype)
            assert torch.isfinite(new).all()
            realized = new.double() - weight.double()
            edits[name] = dict(shape=list(weight.shape), changed=int((new != weight).sum()), requested_norm=float(delta.norm()),
                               realized_norm=float(realized.norm()), relative_norm=float(realized.norm() / weight.double().norm()),
                               quantization_relative_error=float((realized - delta).norm() / delta.norm()))
            tensors[name] = new.contiguous()
        save_file(tensors, out / shard, metadata={"format": "pt"})
        print(json.dumps(dict(shard=shard, seconds=time.monotonic() - start)), flush=True)
        del tensors
    for path in HOLO.iterdir():
        if path.is_file() and path.suffix != ".safetensors":
            shutil.copyfile(path, out / path.name)
    assert count == 724 and set(edits) == set(factors)
    files = {p.name: sha(p) for p in out.iterdir() if p.is_file()}
    manifest = dict(source=str(HOLO), factors_sha256=sha(ROOT / "candidate_factors.pt"), construction=pack["metadata"],
                    edited=edits, tensors=count, elements=total, changed_elements=sum(v["changed"] for v in edits.values()), files=files,
                    seconds=time.monotonic() - start, caveat="Nullspace preservation is exact in FP64 construction; BF16 rounding can introduce off-subspace error.")
    write_json(out / "regmean_manifest.json", manifest)
    write_json(ROOT / "checkpoint_manifest.json", manifest)
    print(json.dumps(dict(out=str(out), tensors=count, edited=len(edits), changed=manifest["changed_elements"])), flush=True)


if __name__ == "__main__":
    main()
