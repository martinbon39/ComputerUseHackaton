"""Holo3.1 wrapper on transformers: generation + activation capture + inference-time steering.

Capture: residual stream (output of each decoder layer) and down_proj output, at the LAST prefill
position (just before the model generates its action), for all 24 layers.
"""
from __future__ import annotations

import holo.settings as S
import time
import numpy as np
import torch
from transformers import AutoProcessor, AutoModelForImageTextToText


def pick_device() -> str:
    if torch.cuda.is_available():
        return "cuda"
    if hasattr(torch, "xpu") and torch.xpu.is_available():
        return "xpu"
    if torch.backends.mps.is_available():
        return "mps"
    return "cpu"


class Holo:
    def __init__(self, model_path: str = S.MODEL_ID, device: str | None = None):
        self.device = device or pick_device()
        self.processor = AutoProcessor.from_pretrained(S.MODEL_ID)
        self.model = AutoModelForImageTextToText.from_pretrained(
            model_path, dtype=torch.bfloat16).to(self.device).eval()
        tok = self.processor.tokenizer
        self.eos_ids = [tok.convert_tokens_to_ids("<|im_end|>"), tok.convert_tokens_to_ids("<|endoftext|>")]
        self.layers = self.model.model.language_model.layers
        self.n_layers = len(self.layers)
        self._capture = False
        self._resid = [None] * self.n_layers
        self._mlp = [None] * self.n_layers
        self._steer: dict[int, tuple[torch.Tensor, float]] = {}
        for i, layer in enumerate(self.layers):
            layer.register_forward_hook(self._make_layer_hook(i))
            layer.mlp.down_proj.register_forward_hook(self._make_mlp_hook(i))

    # ---------------- hooks ----------------
    def _make_layer_hook(self, i):
        def hook(mod, inp, out):
            h = out[0] if isinstance(out, tuple) else out
            if i in self._steer:
                u, alpha = self._steer[i]
                h = h - alpha * (h @ u).unsqueeze(-1) * u  # project direction out of the residual stream
                out = (h,) + tuple(out[1:]) if isinstance(out, tuple) else h
            if self._capture and h.shape[1] > 1:
                self._resid[i] = h[0, -1].float().cpu()
            return out
        return hook

    def _make_mlp_hook(self, i):
        def hook(mod, inp, out):
            if self._capture and out.shape[1] > 1:
                self._mlp[i] = out[0, -1].float().cpu()
        return hook

    def set_steering(self, directions: dict[int, np.ndarray] | None, alpha: float = 1.0):
        self._steer = {}
        for l, u in (directions or {}).items():
            t = torch.tensor(u, dtype=torch.bfloat16, device=self.device)
            self._steer[int(l)] = (t / t.norm(), float(alpha))

    # ---------------- generation ----------------
    def build_inputs(self, messages, tools, enable_thinking: bool):
        return self.processor.apply_chat_template(
            messages, tools=tools, add_generation_prompt=True, tokenize=True,
            return_dict=True, return_tensors="pt", enable_thinking=enable_thinking,
        ).to(self.device)

    @torch.no_grad()
    def generate(self, messages, tools, enable_thinking=False, max_new_tokens=S.MAX_NEW_TOKENS,
                 seed: int | None = None, capture: bool = True):
        inputs = self.build_inputs(messages, tools, enable_thinking)
        if seed is not None:
            torch.manual_seed(seed)
        self._capture = capture
        self._resid = [None] * self.n_layers
        self._mlp = [None] * self.n_layers
        t0 = time.time()
        out = self.model.generate(
            **inputs, max_new_tokens=max_new_tokens, do_sample=True,
            temperature=S.TEMPERATURE, top_p=S.TOP_P, top_k=S.TOP_K,
            eos_token_id=self.eos_ids, pad_token_id=self.eos_ids[0],
        )
        dt = time.time() - t0
        self._capture = False
        n_in = inputs["input_ids"].shape[-1]
        gen = out[0][n_in:]
        text = self.processor.decode(gen, skip_special_tokens=False)
        text = text.split("<|im_end|>")[0].replace("<|endoftext|>", "").strip()
        acts = None
        if capture and self._resid[0] is not None:
            acts = {
                "resid": torch.stack(self._resid).numpy().astype(np.float16),
                "mlp": torch.stack(self._mlp).numpy().astype(np.float16),
            }
        return {"text": text, "n_in": n_in, "n_out": int(gen.shape[0]), "gen_s": dt, "acts": acts}
