"""Rebuild the exact model input of any recorded step (mirrors agent.run_episode), and teacher-forced scoring.
Used by: offline patch screening (phase 4) and fidelity checks."""
import holo.settings as S
import json
from pathlib import Path
import numpy as np
import torch
from PIL import Image
from holo.agent import SYSTEM_PROMPT, CORRECTIVE_SUFFIX, obs_message, trim_images, TOOLS


def load(run_dir):
    run_dir = Path(run_dir)
    s = json.loads((run_dir / "summary.json").read_text(encoding="utf-8"))
    steps = [json.loads(l) for l in open(run_dir / "steps.jsonl", encoding="utf-8")]
    return s, steps


def rebuild_messages(run_dir, t, upscale=S.UPSCALE):
    """Messages exactly as seen by the model just before generating step t."""
    run_dir = Path(run_dir)
    s, steps = load(run_dir)
    sysmsg = SYSTEM_PROMPT + (CORRECTIVE_SUFFIX if s.get("corrective") else "")
    messages = [{"role": "system", "content": sysmsg}, {"role": "user", "content": s["goal"]}]
    for i in range(t + 1):
        img = Image.open(run_dir / f"step{i:02d}.png").convert("RGB")
        W, H = img.size
        sent = img.resize((int(W * upscale), int(H * upscale)), Image.LANCZOS) if upscale != 1 else img
        messages.append(obs_message(sent))
        trim_images(messages)
        if i == t:
            break
        r = steps[i]; call = r["call"]
        if call is None or "error" in call:
            messages.append({"role": "assistant", "content": r["content"] or "(no tool call)"})
            messages.append({"role": "user", "content": "No valid tool call was found. Call exactly one tool."})
            continue
        messages.append({"role": "assistant", "content": r["content"],
                         "tool_calls": [{"type": "function", "function": {"name": call["name"], "arguments": call["arguments"]}}]})
        if call["name"] == "answer":
            break
        if r["action"] is None:  # adapter exception
            messages.append({"role": "tool", "content": f"Error: {r['action_error']}"})
            continue
        err = r["action_error"]
        messages.append({"role": "tool", "content": "Action executed." if not err else f"Error: {err[:200]}"})
    return messages


@torch.no_grad()
def score(holo, messages, target_text, capture=False):
    """Teacher-forced log-prob of target_text (+ <|im_end|>) as the model's reply. Returns (sum, mean, n_tok)."""
    inputs = holo.build_inputs(messages, TOOLS, enable_thinking=False)
    tok = holo.processor.tokenizer
    tgt = tok(target_text + "<|im_end|>", add_special_tokens=False, return_tensors="pt")["input_ids"].to(holo.device)
    ids = torch.cat([inputs["input_ids"], tgt], dim=1)
    kw = {k: v for k, v in inputs.items() if k not in ("input_ids", "attention_mask")}
    holo._capture = capture
    out = holo.model(input_ids=ids, attention_mask=torch.ones_like(ids), **kw)
    holo._capture = False
    n_in = inputs["input_ids"].shape[1]
    logits = out.logits[0, n_in - 1: -1].float()
    lp = torch.log_softmax(logits, -1).gather(1, tgt[0].unsqueeze(1)).squeeze(1)
    return float(lp.sum()), float(lp.mean()), int(tgt.shape[1])
