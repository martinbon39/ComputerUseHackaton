"""Replay OSWorld trajectories (RealtimeGUI Holo harness @ a763361, served by vLLM) in transformers to get activations.

Rebuilds, for every recorded step t, the exact message list HoloComputerAgent.run sent before generating step t:
  system = system_prompt.txt (instructions + output schema + <task>)
  per step: user <observation>[image]</observation>; keep the last `image_budget` images, older ones -> text
  "[screenshot evicted]"; assistant = the parsed step re-serialised ({note, thought, tool_call}, pydantic
  model_dump_json == compact json); then user <tool_output tool="...">...</tool_output>.
Chat template: the model's own, no tools, enable_thinking=True, add_generation_prompt.

One forward pass per step on [prefill + recorded reasoning + "\n</think>\n\n" + action JSON + <|im_end|>]:
  resid / mlp           residual stream and down_proj output at the LAST PREFILL token (same site as MiniWoB)
  resid_post / mlp_post same, at the last token before the action JSON (after the recorded reasoning)
  lp_action             mean log-prob of the recorded action JSON (teacher-forced): context-fidelity signal
Output: <out>/<domain>/<example_id>/acts.npz ([steps, L, D] float16 + per-step n_in) and replay.json.

Known gaps the trajectory files cannot reveal (the harness does not record them): a step whose env.step raised
leaves an unrecorded assistant message in the real context; a step whose model output failed to parse 3 times
evicts one extra image. Both log a warning in the run log ("env.step failed", "model call/parse failed").

Usage: python -m holo.osw_replay <results_dir> --out <acts_dir> [--vllm_url http://127.0.0.1:8002/v1 --served Holo-3.1-4B]
"""
import os
for _v in ("OMP_NUM_THREADS", "MKL_NUM_THREADS", "OPENBLAS_NUM_THREADS"):  # pod CPU quota ~10 cores shared by many jobs
    os.environ.setdefault(_v, "2")
os.environ.setdefault("TOKENIZERS_PARALLELISM", "false")
import holo.settings as S
import argparse, base64, io, json, time
from pathlib import Path
import numpy as np
import torch
from PIL import Image
from holo.osw_taxonomy import find_tasks, load_task, SCREEN

EVICTED = "[screenshot evicted]"


def assistant_json(r):
    return json.dumps({"note": r["note"], "thought": r["thought"], "tool_call": r["tool_call"]},
                      ensure_ascii=False, separators=(",", ":"))


def tool_output(r):
    info = r["info"]
    if set(info) == {"value"}:  # recorder wraps a non-dict info as {"value": info}; the agent used str(info)
        return str(info["value"])
    return info.get("tool_output", "")


def check_traj(d, steps):
    assert steps, f"{d}: empty traj"
    assert [s["step_num"] for s in steps] == list(range(1, len(steps) + 1)), f"{d}: step_num not contiguous"
    assert all(s["tool_name"] != "answer" for s in steps[:-1]), f"{d}: answer before the last step"
    for s in steps:
        assert s.get("screenshot_file") and (d / s["screenshot_file"]).exists(), f"{d}: missing {s.get('screenshot_file')}"
        assert s["tool_call"]["tool_name"] == s["tool_name"]


def rebuild(d, steps, sysprompt, t, image_budget=3):
    """Messages before step t. Image chunks carry a PIL image under '_pil' (converted per backend below)."""
    msgs = [{"role": "system", "content": sysprompt}]
    for i in range(t + 1):
        img = Image.open(d / steps[i]["screenshot_file"]).convert("RGB")
        msgs.append({"role": "user", "content": [{"type": "text", "text": "<observation>\n"},
                                                  {"type": "image_url", "_pil": img},
                                                  {"type": "text", "text": "\n</observation>"}]})
        seen = 0
        for m in reversed(msgs):
            if m["role"] != "user" or not isinstance(m["content"], list):
                continue
            for ch in m["content"]:
                if ch["type"] == "image_url":
                    seen += 1
                    if seen > image_budget:
                        ch.clear(); ch.update({"type": "text", "text": EVICTED})
        if i == t:
            break
        r = steps[i]
        msgs.append({"role": "assistant", "content": assistant_json(r)})
        msgs.append({"role": "user", "content": f'<tool_output tool="{r["tool_name"]}">\n{tool_output(r)}\n</tool_output>'})
    return msgs


def images_of(msgs):
    return [ch["_pil"] for m in msgs if isinstance(m["content"], list) for ch in m["content"] if ch["type"] == "image_url"]


def to_hf(msgs):
    conv = lambda ch: {"type": "image", "image": ch["_pil"]} if ch["type"] == "image_url" else ch
    return [{**m, "content": [conv(c) for c in m["content"]] if isinstance(m["content"], list) else m["content"]}
            for m in msgs]


def to_openai(msgs):
    def conv(ch):
        if ch["type"] != "image_url":
            return ch
        buf = io.BytesIO(); ch["_pil"].save(buf, format="PNG")
        return {"type": "image_url", "image_url": {"url": "data:image/png;base64," + base64.b64encode(buf.getvalue()).decode()}}
    return [{**m, "content": [conv(c) for c in m["content"]] if isinstance(m["content"], list) else m["content"]}
            for m in msgs]


def vllm_prompt_tokens(url, served, msgs):
    import urllib.request
    body = {"model": served, "messages": to_openai(msgs), "max_tokens": 1, "temperature": 0,
            "chat_template_kwargs": {"enable_thinking": True}}
    req = urllib.request.Request(url.rstrip("/") + "/chat/completions", data=json.dumps(body).encode(),
                                 headers={"Content-Type": "application/json"})
    return json.loads(urllib.request.urlopen(req, timeout=300).read())["usage"]["prompt_tokens"]


class Capture:
    """Hooks on every decoder layer + down_proj; keeps the activation at the requested sequence positions."""

    def __init__(self, holo):
        self.pos, self.resid, self.mlp = None, {}, {}
        for i, layer in enumerate(holo.layers):
            layer.register_forward_hook(self._hook(i, self.resid, layer=True))
            layer.mlp.down_proj.register_forward_hook(self._hook(i, self.mlp, layer=False))

    def _hook(self, i, store, layer):
        def hook(mod, inp, out):
            h = out[0] if (layer and isinstance(out, tuple)) else out
            if self.pos is not None and h.shape[1] > max(self.pos):
                store[i] = h[0, self.pos].float().cpu()
        return hook

    def stacked(self, store):  # -> [n_pos, L, D]
        return torch.stack([store[i] for i in sorted(store)], 1).numpy().astype(np.float16)


@torch.no_grad()
def replay_step(holo, cap, msgs, reasoning, action):
    tok = holo.processor.tokenizer
    inputs = holo.build_inputs(to_hf(msgs), None, enable_thinking=True)
    ids = inputs["input_ids"]
    n_in = ids.shape[1]
    r_ids = tok((reasoning or "").strip() + "\n</think>\n\n", add_special_tokens=False, return_tensors="pt")["input_ids"]
    a_ids = tok(action + "<|im_end|>", add_special_tokens=False, return_tensors="pt")["input_ids"]
    full = torch.cat([ids, r_ids.to(ids.device), a_ids.to(ids.device)], 1)
    n_r, n_a = r_ids.shape[1], a_ids.shape[1]
    kw = {k: v for k, v in inputs.items() if k not in ("input_ids", "attention_mask")}
    for k, v in kw.items():  # per-token side inputs (mm_token_type_ids): appended text tokens are type 0
        if torch.is_tensor(v) and v.dim() == 2 and v.shape == ids.shape:
            kw[k] = torch.cat([v, torch.zeros((1, full.shape[1] - n_in), dtype=v.dtype, device=v.device)], 1)
    cap.pos = [n_in - 1, n_in + n_r - 1]
    out = holo.model(input_ids=full, attention_mask=torch.ones_like(full), logits_to_keep=n_a + 1, **kw)
    cap.pos = None
    lp = torch.log_softmax(out.logits[0, :-1].float(), -1).gather(1, a_ids[0].to(full.device).unsqueeze(1))
    n_img_tokens = int((ids[0] == tok.convert_tokens_to_ids("<|image_pad|>")).sum())
    return {"resid": cap.stacked(cap.resid), "mlp": cap.stacked(cap.mlp), "n_in": n_in, "n_reason": n_r,
            "n_action": n_a, "lp_action": float(lp.mean()), "n_image_pad": n_img_tokens,
            "prompt_text": holo.processor.tokenizer.decode(ids[0])}


def replay_task(holo, cap, d, out_dir, image_budget=3, vllm=None, n_check=0, tail=0):
    """tail=0: every step -> acts.npz. tail=k: only the last k steps (terminal answer + the k-1 before) -> acts_tail.npz
    with their step indices in `t` (priority pass for the false-success direction)."""
    meta, score, steps = load_task(d)
    check_traj(d, steps)
    sysprompt = (d / "system_prompt.txt").read_text(encoding="utf-8")
    assert sysprompt.rstrip().endswith("</task>"), f"{d}: system prompt has no <task> block"
    R, M, RP, MP, rows = [], [], [], [], []
    sel = range(max(0, len(steps) - tail), len(steps)) if tail else range(len(steps))
    for t in sel:
        msgs = rebuild(d, steps, sysprompt, t, image_budget)
        imgs = images_of(msgs)
        # fidelity asserts: the images in context are exactly the last <=budget recorded observations, untouched
        assert len(imgs) == min(t + 1, image_budget)
        for k, im in enumerate(imgs):
            src = Image.open(d / steps[t - len(imgs) + 1 + k]["screenshot_file"]).convert("RGB")
            assert im.size == SCREEN and np.array_equal(np.asarray(im), np.asarray(src))
        n_evicted = sum(ch.get("text") == EVICTED for m in msgs if isinstance(m["content"], list) for ch in m["content"])
        assert n_evicted == t + 1 - len(imgs)
        assert sum(m["role"] == "assistant" for m in msgs) == t
        g = replay_step(holo, cap, msgs, steps[t].get("reasoning"), assistant_json(steps[t]))
        txt = g.pop("prompt_text")
        assert txt.count("<|vision_start|>") == len(imgs) and txt.count(EVICTED) == n_evicted
        if t > 0:
            assert assistant_json(steps[t - 1]) in txt and f'<tool_output tool="{steps[t - 1]["tool_name"]}">' in txt
        assert txt.endswith("<|im_start|>assistant\n<think>\n")
        row = {"t": t, **{k: g[k] for k in ("n_in", "n_reason", "n_action", "lp_action", "n_image_pad")},
               "n_images": len(imgs)}
        if vllm and (t < n_check or t == len(steps) - 1):  # the last step also catches unrecorded env.step failures
            try:
                row["vllm_prompt_tokens"] = vllm_prompt_tokens(vllm[0], vllm[1], msgs)
            except Exception as e:  # the check must not stop the replay; recorded so a missing check stays visible
                row["vllm_check_error"] = str(e)[:200]
        rows.append(row)
        R.append(g["resid"][0]); M.append(g["mlp"][0]); RP.append(g["resid"][1]); MP.append(g["mlp"][1])
    out_dir.mkdir(parents=True, exist_ok=True)
    name = "acts_tail" if tail else "acts"
    tmp = out_dir / f"{name}.tmp.npz"  # atomic: a killed replay never leaves a truncated acts file
    np.savez_compressed(tmp, resid=np.stack(R), mlp=np.stack(M), resid_post=np.stack(RP),
                        mlp_post=np.stack(MP), n_in=np.array([r["n_in"] for r in rows]), t=np.array([r["t"] for r in rows]))
    tmp.replace(out_dir / f"{name}.npz")
    (out_dir / f"replay{'_tail' if tail else ''}.json").write_text(
        json.dumps({"src": str(d), "score": score, "steps": rows}, indent=1))
    return rows


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("results_dir")
    ap.add_argument("--out", required=True)
    ap.add_argument("--image_budget", type=int, default=3)
    ap.add_argument("--vllm_url", default=None)
    ap.add_argument("--served", default="Holo-3.1-4B")
    ap.add_argument("--n_check", type=int, default=3, help="steps per task whose prompt length is checked against vLLM")
    ap.add_argument("--redo", action="store_true")
    ap.add_argument("--tail", type=int, default=0, help="only the last k steps of each task (-> acts_tail.npz)")
    ap.add_argument("--limit", type=int, default=0, help="stop after this many tasks (lets a loop re-prioritise)")
    ap.add_argument("--gpu_gb", type=float, default=12, help="per-process VRAM cap (the H200 is shared)")
    a = ap.parse_args()
    torch.set_num_threads(2); torch.set_num_interop_threads(2)
    if torch.cuda.is_available():
        torch.cuda.set_per_process_memory_fraction(a.gpu_gb * 2**30 / torch.cuda.get_device_properties(0).total_memory)
    from holo.model import Holo
    holo = Holo()
    cap = Capture(holo)
    root, out = Path(a.results_dir), Path(a.out)
    done = 0
    for d in find_tasks(root):
        if not (d / "result.txt").exists():  # unfinished or infra-failed episode
            continue
        meta = json.loads((d / "meta.json").read_text())
        task = f"{meta['domain']}/{meta['example_id']}"
        od = out / task
        target = "acts_tail.npz" if a.tail else "acts.npz"
        if ((od / target).exists() or (od / "acts.npz").exists() or (od / f"oom_{target}").exists()) and not a.redo:
            continue
        if a.limit and done >= a.limit:
            break
        done += 1
        t0 = time.time()
        try:
            rows = replay_task(holo, cap, d, od, a.image_budget, (a.vllm_url, a.served) if a.vllm_url else None,
                               a.n_check, a.tail)
        except AssertionError as e:
            print(f"SKIP {task}: {e}", flush=True)
            continue
        except torch.OutOfMemoryError:  # longest contexts may not fit under --gpu_gb: marked, retried only with --redo
            cap.pos = None; cap.resid.clear(); cap.mlp.clear(); torch.cuda.empty_cache()
            od.mkdir(parents=True, exist_ok=True); (od / f"oom_{target}").write_text(f"{a.gpu_gb} GB\n")
            print(f"OOM {task} (cap {a.gpu_gb} GB)", flush=True)
            continue
        finally:
            torch.cuda.empty_cache()
        chk = [(r["n_in"], r["vllm_prompt_tokens"]) for r in rows if "vllm_prompt_tokens" in r]
        if any(h != v for h, v in chk):
            print(f"MISMATCH {task}: HF vs vLLM prompt tokens {chk}", flush=True)
        print(f"{od.relative_to(out)} steps={len(rows)} n_in={rows[0]['n_in']}..{rows[-1]['n_in']} "
              f"lp_action={np.mean([r['lp_action'] for r in rows]):.3f} hf_vs_vllm={chk} {time.time() - t0:.0f}s", flush=True)


if __name__ == "__main__":
    main()
