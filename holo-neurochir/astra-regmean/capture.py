from common import *
import time
from transformers import AutoModelForImageTextToText, AutoProcessor

sys.path.insert(0, "/workspace/projet")
from holo.osw_replay import rebuild, to_hf
from holo.osw_taxonomy import load_task


def extend(inputs, extra):
    result = dict(inputs)
    ids = inputs["input_ids"]
    for key, value in inputs.items():
        if torch.is_tensor(value) and value.ndim == 2 and value.shape == ids.shape:
            pad = extra if key == "input_ids" else torch.ones_like(extra) if key == "attention_mask" else torch.zeros_like(extra, dtype=value.dtype)
            result[key] = torch.cat((value, pad), 1)
    return result


@torch.inference_mode()
def main():
    start = time.monotonic()
    m = read_frozen()
    out = ROOT / "captures.pt"
    assert not out.exists()
    torch.cuda.set_per_process_memory_fraction(18e9 / torch.cuda.get_device_properties(0).total_memory)
    processor = AutoProcessor.from_pretrained(HOLO)
    model = AutoModelForImageTextToText.from_pretrained(HOLO, dtype=torch.bfloat16).to("cuda").eval()
    modules = dict(model.named_modules())
    captured = {}
    positions = []
    handles = []
    for name in writer_names():
        module = modules[name.removesuffix(".weight")]
        def hook(mod, args, output, name=name):
            assert args[0].shape[-1] == mod.weight.shape[1]
            captured[name] = args[0][0, positions].float().cpu()
        handles.append(module.register_forward_hook(hook))
    captures = {}
    metadata = {}
    rows = m["rows"] + [dict(id=f"text_{i}", label="text", text_prompt=p) for i, p in enumerate(m["text_prompts"])]
    assert len(rows) <= 60
    for i, row in enumerate(rows):
        assert time.monotonic() - start < 1800 and not (ROOT / "STOP").exists() and not Path("/workspace/astra/4b/STOP_GPU").exists()
        if row["label"] == "text":
            messages = [{"role": "user", "content": row["text_prompt"]}]
            inputs = processor.apply_chat_template(messages, add_generation_prompt=True, tokenize=True, return_dict=True, return_tensors="pt", enable_thinking=True).to("cuda")
            positions = [inputs["input_ids"].shape[1] - 1]
            meta = dict(id=row["id"], label="text", n_in=inputs["input_ids"].shape[1], positions=positions)
        else:
            d = Path(row["path"])
            for filename, digest in {**row["sha256"], **row["images_sha256"]}.items():
                assert sha(d / filename) == digest
            _, _, steps = load_task(d)
            inputs = processor.apply_chat_template(to_hf(rebuild(d, steps, (d / "system_prompt.txt").read_text(), row["t"])), add_generation_prompt=True, tokenize=True, return_dict=True, return_tensors="pt", enable_thinking=True).to("cuda")
            n_in = inputs["input_ids"].shape[1]
            assert n_in == row["n_in"], (row["id"], n_in, row["n_in"])
            reason = (steps[row["t"]].get("reasoning") or "").strip() + "\n</think>\n\n"
            extra = processor.tokenizer(reason, add_special_tokens=False, return_tensors="pt")["input_ids"].to("cuda")
            inputs = extend(inputs, extra)
            positions = [n_in - 1, inputs["input_ids"].shape[1] - 1]
            meta = {k: row[k] for k in ["id", "task_id", "label", "t", "fold", "n_in"]}
            meta.update(positions=positions, reasoning_sha256=hashlib.sha256(reason.encode()).hexdigest(), current_json_tokens=0)
        meta["input_ids_sha256"] = hashlib.sha256(inputs["input_ids"].cpu().numpy().tobytes()).hexdigest()
        captured.clear()
        model(**inputs, use_cache=False, logits_to_keep=1)
        assert set(captured) == set(writer_names()) and all(torch.isfinite(v).all() for v in captured.values())
        captures[row["id"]] = dict(captured)
        metadata[row["id"]] = meta
        torch.save(dict(captures=captures, metadata=metadata, manifest_sha256=sha(ROOT / "manifest.json"), complete=i + 1 == len(rows)), ROOT / "captures.partial.pt")
        record = dict(context=row["id"], label=row["label"], count=i + 1, seconds=round(time.monotonic() - start, 2), n_in=meta["n_in"], peak_reserved=torch.cuda.max_memory_reserved())
        with (ROOT / "capture.jsonl").open("a") as log:
            log.write(json.dumps(record) + "\n")
        print(json.dumps(record), flush=True)
        del inputs
    (ROOT / "captures.partial.pt").rename(out)
    (ROOT / "captures.sha256").write_text(sha(out) + "\n")
    for handle in handles:
        handle.remove()


if __name__ == "__main__":
    main()
