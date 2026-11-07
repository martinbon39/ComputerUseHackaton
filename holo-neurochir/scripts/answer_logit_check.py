"""Positive control for an 'answer'-logit patch: on the final (answer) step of a recorded fs+ trajectory, the
next-token logit of the tool name 'answer' (id 8944, after '"tool_name":"') under the original and the patched
checkpoint, same context as holo.osw_replay (system prompt, last 3 screenshots, recorded reasoning + action prefix).
Usage (pod, GPU): PYTHONPATH=. HOLO_MODEL=Hcompany/Holo-3.1-4B python scripts/answer_logit_check.py <task_dir> <ckpt_dir>
"""
import holo.settings as S
import gc, json, sys
from pathlib import Path
import torch
from huggingface_hub import snapshot_download
from holo.model import Holo
from holo.osw_replay import assistant_json, check_traj, rebuild, to_hf
from holo.osw_taxonomy import load_task

ANSWER = 8944


def context(holo, d, false_success=True):
    """Inputs up to the tool name of the final `answer` step (a false success unless false_success=False)."""
    meta, score, steps = load_task(d)
    check_traj(d, steps)
    assert steps[-1]["tool_name"] == "answer", f"{d}: no final answer step"
    assert not false_success or not score, f"{d}: not a false-success answer step"
    t = len(steps) - 1
    msgs = rebuild(d, steps, (d / "system_prompt.txt").read_text(encoding="utf-8"), t)
    tok = holo.processor.tokenizer
    inputs = holo.build_inputs(to_hf(msgs), None, enable_thinking=True)
    action = assistant_json(steps[t])
    head = action[: action.index('"tool_name":"answer"') + len('"tool_name":"')]
    r_ids = tok((steps[t].get("reasoning") or "").strip() + "\n</think>\n\n", add_special_tokens=False,
                return_tensors="pt")["input_ids"]
    h_ids = tok(head, add_special_tokens=False, return_tensors="pt")["input_ids"]
    full_action = tok(action, add_special_tokens=False)["input_ids"]
    assert full_action[: h_ids.shape[1]] == h_ids[0].tolist() and full_action[h_ids.shape[1]] == ANSWER, \
        "the action prefix does not tokenize to <prefix> + 'answer'"
    return inputs, r_ids, h_ids, {"task": f"{d.parent.name}/{d.name}", "t": t, "head_tail": head[-40:]}


def stacked(inputs, r_ids, h_ids):
    ids = inputs["input_ids"]; dev = ids.device
    full = torch.cat([ids, r_ids.to(dev), h_ids.to(dev)], 1)
    kw = {k: v for k, v in inputs.items() if k not in ("input_ids", "attention_mask")}
    for k, v in kw.items():
        if torch.is_tensor(v) and v.dim() == 2 and v.shape == ids.shape:
            kw[k] = torch.cat([v, torch.zeros((1, full.shape[1] - ids.shape[1]), dtype=v.dtype, device=dev)], 1)
    return full, kw


@torch.no_grad()
def answer_logit(holo, inputs, r_ids, h_ids):
    full, kw = stacked(inputs, r_ids, h_ids)
    logits = holo.model(input_ids=full, attention_mask=torch.ones_like(full), logits_to_keep=1, **kw).logits[0, -1].float()
    lp = torch.log_softmax(logits, -1)
    return {"logit": float(logits[ANSWER]), "logprob": float(lp[ANSWER]), "rank": int((logits > logits[ANSWER]).sum()),
            "top": holo.processor.tokenizer.convert_ids_to_tokens(int(logits.argmax()))}


def main():
    d, ckpt = Path(sys.argv[1]), sys.argv[2]
    res = {}
    for name, path in (("orig", str(Path(snapshot_download(S.MODEL_ID, local_files_only=True)))), ("patched", ckpt)):
        holo = Holo(path)
        inputs, r_ids, h_ids, info = context(holo, d)
        res[name] = answer_logit(holo, inputs, r_ids, h_ids)
        del holo; gc.collect(); torch.cuda.empty_cache()
    res.update(info, delta_logit=res["patched"]["logit"] - res["orig"]["logit"])
    print(json.dumps(res))


if __name__ == "__main__":
    main()
