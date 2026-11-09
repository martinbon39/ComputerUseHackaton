#!/usr/bin/env python3
"""Level 3: replay a recorded context and read the model's tool decision (answer vs the other tools).

For each context in contexts/ and each model, this prints
  (a) P(answer) among the tool names at the tool-name position, teacher-forced on the RECORDED reasoning, note and
      thought of the original model (one forward pass). This position comes AFTER the text that already says
      "the task is done": it measures confidence in copying a conclusion that is already written, not the decision.
  (b) optionally (--sample N) the fraction of N free samples (T=0.8, top_p=0.9, top_k=20, the settings of our runs)
      whose tool is `answer`. This is the measure behind the 8/8 -> 3/8 figures; it needs GPU time and is noisy at small N.

Honest reading (recorded samples, n=8 per context): the merged model lowers `answer` on one feasible false-success context (8/8 -> 3/8) AND on two true-finish contexts (8/8 -> 1/8); on the infeasible context, where `answer` is correct, it stays 8/8. The effect
is a lever on the stopping decision, not a selective repair (see RESULTS.md).

    python probe_decision.py --models Hcompany/Holo-3.1-4B@8c88265a5a159bfd1492db9243733dd2e6e04a6e  HF_REPO_ID
    python probe_decision.py --dry-run                      # no model: checks the message construction only
"""
import argparse, json, pathlib, re, sys

HERE = pathlib.Path(__file__).resolve().parent
HOLO = "Hcompany/Holo-3.1-4B@8c88265a5a159bfd1492db9243733dd2e6e04a6e"
MERGED_PLACEHOLDER = "HF_REPO_ID@main"  # replace by the published repo id once the checkpoint is on the Hub
EVICTED = "[screenshot evicted]"


def load_context(cdir):
    c = json.loads((cdir / "context.json").read_text())
    return c


def to_hf_messages(c, cdir):
    """Rebuild the exact message list sent before the decision step (same format as our replay harness)."""
    from PIL import Image
    msgs = []
    for m in c["messages"]:
        if m["role"] != "user" or "observation" not in m:
            msgs.append({"role": m["role"], "content": m["text"]})
            continue
        o = m["observation"]
        mid = ({"type": "text", "text": EVICTED} if o.get("evicted")
               else {"type": "image", "image": Image.open(cdir / o["image"]).convert("RGB")})
        msgs.append({"role": "user", "content": [{"type": "text", "text": "<observation>\n"}, mid,
                                                  {"type": "text", "text": "\n</observation>"}]})
    return msgs


def tool_names(c):
    sys_prompt = c["messages"][0]["text"]
    return sorted(set(re.findall(r'"tool_name": \{"const": "(\w+)"', sys_prompt)))


def forced_suffix(c):
    """Recorded reasoning + JSON up to the opening quote of the tool name."""
    r = c["recorded_final_step"]
    j = json.dumps(r["json"], ensure_ascii=False, separators=(",", ":"))
    cut = j.index('"tool_call":{"tool_name":"') + len('"tool_call":{"tool_name":"')
    return (r["reasoning"] or "").strip() + "\n</think>\n\n", j[:cut]


def dry_run(ctxs):
    for cdir in ctxs:
        c = load_context(cdir)
        msgs = to_hf_messages(c, cdir)
        n_img = sum(1 for m in msgs if isinstance(m["content"], list) for ch in m["content"] if ch["type"] == "image")
        n_ev = sum(1 for m in msgs if isinstance(m["content"], list) for ch in m["content"] if ch.get("text") == EVICTED)
        think, prefix = forced_suffix(c)
        assert c["messages"][-1]["role"] == "user" and n_img == min(3, c["step_t"] + 1) and n_img + n_ev == c["step_t"] + 1
        assert sum(m["role"] == "assistant" for m in msgs) == c["step_t"]
        print(f"{cdir.name}: {len(msgs)} messages, {n_img} images + {n_ev} evicted, tools={tool_names(c)}, "
              f"forced prefix ends with ...{prefix[-40:]!r}  [{c['kind']}]")


def load_model(spec, dtype):
    import torch
    from transformers import AutoModelForImageTextToText
    repo, _, rev = spec.partition("@")
    m = AutoModelForImageTextToText.from_pretrained(repo, revision=rev or None, dtype=getattr(torch, dtype), device_map="auto").eval()
    return m


def first_tokens(tok, prefix_ids, prefix_text, names):
    out = {}
    for n in names:
        ids = tok(prefix_text + n, add_special_tokens=False)["input_ids"]
        assert ids[: len(prefix_ids)] == prefix_ids, "tokenisation boundary changed: " + n
        out[n] = ids[len(prefix_ids)]
    assert len(set(out.values())) == len(out), f"tool names share a first token: {out}"
    return out


def probe(model, proc, c, cdir, sample, dtype):
    import torch
    tok = proc.tokenizer
    msgs = to_hf_messages(c, cdir)
    inputs = proc.apply_chat_template(msgs, add_generation_prompt=True, tokenize=True, return_dict=True,
                                      return_tensors="pt", enable_thinking=True).to(model.device)
    think, prefix = forced_suffix(c)
    p_ids = tok(prefix, add_special_tokens=False)["input_ids"]
    names = tool_names(c)
    ft = first_tokens(tok, p_ids, prefix, names)
    t_ids = tok(think, add_special_tokens=False, return_tensors="pt")["input_ids"].to(model.device)
    pre = torch.tensor([p_ids], device=model.device)
    full = torch.cat([inputs["input_ids"], t_ids, pre], 1)
    kw = {k: v for k, v in inputs.items() if k not in ("input_ids", "attention_mask")}
    for k, v in kw.items():  # per-token side inputs: appended text tokens are type 0
        if torch.is_tensor(v) and v.dim() == 2 and v.shape == inputs["input_ids"].shape:
            kw[k] = torch.cat([v, torch.zeros((1, full.shape[1] - v.shape[1]), dtype=v.dtype, device=v.device)], 1)
    with torch.no_grad():
        logits = model(input_ids=full, attention_mask=torch.ones_like(full), logits_to_keep=1, **kw).logits[0, -1].float()
    lp = torch.log_softmax(logits, -1)
    cand = torch.tensor([ft[n] for n in names], device=lp.device)
    mass = float(lp[cand].exp().sum())
    probs = torch.softmax(lp[cand], -1)
    res = {"p_answer": float(probs[names.index("answer")]), "candidate_mass": mass,
           "top_other": max(((n, float(p)) for n, p in zip(names, probs) if n != "answer"), key=lambda x: x[1]),
           "n_tokens": int(full.shape[1])}
    if sample:
        out = model.generate(**inputs, do_sample=True, temperature=0.8, top_p=0.9, top_k=20, max_new_tokens=1500,
                             num_return_sequences=sample)
        texts = tok.batch_decode(out[:, inputs["input_ids"].shape[1]:], skip_special_tokens=True)
        tools = [(re.findall(r'"tool_call"\s*:\s*\{\s*"tool_name"\s*:\s*"(\w+)"', t) or ["<none>"])[-1] for t in texts]
        res["sampled_answer"] = f"{sum(t == 'answer' for t in tools)}/{len(tools)}"
        res["sampled_tools"] = tools
    return res


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--models", nargs="+", default=[HOLO, MERGED_PLACEHOLDER], help="repo[@revision] ...; first is the reference")
    ap.add_argument("--contexts", nargs="*", help="context directory names (default: all in contexts/)")
    ap.add_argument("--sample", type=int, default=0, help="also sample N generations per context and model")
    ap.add_argument("--dtype", default="float16")
    ap.add_argument("--dry-run", action="store_true")
    a = ap.parse_args()
    ctxs = sorted(p for p in (HERE / "contexts").iterdir() if p.is_dir() and (not a.contexts or p.name in a.contexts))
    if a.dry_run:
        return dry_run(ctxs)
    if any(m.startswith("HF_REPO_ID") for m in a.models):
        sys.exit("The merged checkpoint is not published yet: pass --models with its repo id, or build it with rebuild_merge.py --build DIR and pass DIR.")
    from transformers import AutoProcessor
    proc = AutoProcessor.from_pretrained(HOLO.split("@")[0], revision=HOLO.split("@")[1])
    table = {}
    for spec in a.models:
        model = load_model(spec, a.dtype)
        for cdir in ctxs:
            c = load_context(cdir)
            table[(cdir.name, spec)] = probe(model, proc, c, cdir, a.sample, a.dtype)
            r = table[(cdir.name, spec)]
            print(f"{cdir.name:<32} {spec[:48]:<48} P(answer)={r['p_answer']:.3f} (candidate mass {r['candidate_mass']:.2f})"
                  + (f"  sampled answer {r['sampled_answer']}" if a.sample else ""), flush=True)
        del model
    print("\nRecorded in our runs (8 samples, T=0.8, original / beta=0.25 / beta=0.5): answer rate per context")
    for cdir in ctxs:
        c = load_context(cdir)
        rr = c["recorded_answer_rate_8_samples_T0.8"]
        print(f"  {cdir.name:<32} [{c['kind']}]  " + "  ".join(f"{k.split('_full')[0]}={v['answer']}/{v['n']}" for k, v in rr.items()))


if __name__ == "__main__":
    main()
