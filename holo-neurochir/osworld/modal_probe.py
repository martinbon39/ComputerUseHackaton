"""Three timed requests against the Modal endpoint (modal_vllm.py): a T=0 text prompt, a text prompt with thinking,
then the harness call of probe_answer_rate.py (holo_agent schema, thinking, T=0.8) on the last recorded step of a task.
Usage: PYTHONPATH=. ~/osw/venv/bin/python osworld/modal_probe.py <base_url> <task_dir> [--model Holo-3.1-4B]
The key is read from ~/.holo_modal_key and never printed.
astra-free's checkpoints (served names containing "free_", and modal-orig, its baseline) get NO generative smoke: their
frozen pilot is the control and every request counts in its budget. Use /health, /version, /v1/models for them.
"""
import argparse, json, time
from pathlib import Path
from openai import OpenAI

from probe_answer_rate import SCHEMA, check_traj, load_task, rebuild, to_openai


def timed(client, label, **kw):
    t = time.time()
    r = client.chat.completions.create(**kw)
    dt = time.time() - t
    content = r.choices[0].message.content or ""
    print(json.dumps({"req": label, "latency_s": round(dt, 2), "prompt_tokens": r.usage.prompt_tokens,
                      "completion_tokens": r.usage.completion_tokens, "finish": r.choices[0].finish_reason,
                      "content": content[:200]}, ensure_ascii=False))
    return content


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("url")
    ap.add_argument("task")
    ap.add_argument("--model", default="Holo-3.1-4B")
    a = ap.parse_args()
    if "free_" in a.model or a.model.endswith("modal-orig"):
        raise SystemExit(f"{a.model}: no generative smoke on astra-free checkpoints (read-only /health, /v1/models only)")
    client = OpenAI(base_url=a.url, api_key=Path("~/.holo_modal_key").expanduser().read_text().strip(), timeout=900)
    timed(client, "text_t0", model=a.model, temperature=0, max_tokens=128,
          messages=[{"role": "user", "content": "Explain in one sentence why the sky is blue."}],
          extra_body={"chat_template_kwargs": {"enable_thinking": False}})
    timed(client, "text_thinking", model=a.model, temperature=0.8, top_p=0.9, max_tokens=1024,
          messages=[{"role": "user", "content": "List the steps to rename a file in a Linux terminal."}],
          extra_body={"chat_template_kwargs": {"enable_thinking": True}})
    d = Path(a.task)
    meta, score, steps = load_task(d)
    check_traj(d, steps)
    msgs = to_openai(rebuild(d, steps, (d / "system_prompt.txt").read_text(encoding="utf-8"), len(steps) - 1))
    out = timed(client, f"osworld_step{len(steps) - 1}", model=a.model, messages=msgs, temperature=0.8, top_p=0.9,
                max_tokens=3072, reasoning_effort="medium",
                extra_body={"structured_outputs": {"json": SCHEMA}, "chat_template_kwargs": {"enable_thinking": True}})
    print(json.dumps({"recorded_tool": steps[-1]["tool_name"], "sampled_tool": json.loads(out)["tool_call"]["tool_name"]}))


if __name__ == "__main__":
    main()
