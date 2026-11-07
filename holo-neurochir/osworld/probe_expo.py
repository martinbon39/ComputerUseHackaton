"""Offline sanity of one served checkpoint (ExPO arms): 3 text prompts at T=0, then the harness call of
probe_answer_rate.py on recorded final answer steps, keeping per sample: tool name, strict-JSON validity, finish
reason, completion tokens and reasoning length.
Usage: PYTHONPATH=. ~/osw/venv/bin/python osworld/probe_expo.py <url> <model> <out.json> <task_dir> [...] [--n 8]
"""
import argparse, json, sys
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from openai import OpenAI

sys.path.insert(0, str(Path(__file__).resolve().parent))
from probe_answer_rate import SCHEMA, check_traj, load_task, rebuild, to_openai  # noqa: E402

TEXT = ["Explain in a short paragraph why the sky is blue.",
        "List the steps to rename a file in a Linux terminal.",
        "A shop sells pens at 3 euros each. How much do 7 pens cost? Answer with the computation."]


def text_probe(client, model, prompt):
    r = client.chat.completions.create(model=model, messages=[{"role": "user", "content": prompt}], temperature=0,
                                       seed=0, max_tokens=200,
                                       extra_body={"chat_template_kwargs": {"enable_thinking": False}})
    return r.choices[0].message.content


def harness_sample(client, model, messages):
    r = client.chat.completions.create(model=model, messages=messages, temperature=0.8, top_p=0.9, max_tokens=3072,
                                       reasoning_effort="medium",
                                       extra_body={"structured_outputs": {"json": SCHEMA},
                                                   "chat_template_kwargs": {"enable_thinking": True}})
    c = r.choices[0]
    reasoning = getattr(c.message, "reasoning_content", None) or getattr(c.message, "reasoning", None) or ""
    try:
        tool = json.loads(c.message.content)["tool_call"]["tool_name"]
        valid = True
    except Exception:  # noqa: BLE001 - an unparsable answer is itself the measurement
        tool, valid = "<unparsable>", False
    return {"tool": tool, "valid_json": valid, "finish": c.finish_reason, "completion_tokens": r.usage.completion_tokens,
            "reasoning_chars": len(reasoning), "content_chars": len(c.message.content or "")}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("url"); ap.add_argument("model"); ap.add_argument("out"); ap.add_argument("tasks", nargs="+")
    ap.add_argument("--n", type=int, default=8)
    a = ap.parse_args()
    client = OpenAI(base_url=a.url, api_key="EMPTY", timeout=600)
    out = {"model": a.model, "url": a.url, "text": [{"prompt": p, "answer": text_probe(client, a.model, p)} for p in TEXT]}
    jobs = []
    for t in a.tasks:
        d = Path(t)
        meta, score, steps = load_task(d)
        check_traj(d, steps)
        assert steps[-1]["tool_name"] == "answer", f"{d}: final step is not answer"
        msgs = to_openai(rebuild(d, steps, (d / "system_prompt.txt").read_text(encoding="utf-8"), len(steps) - 1))
        jobs += [(f"{d.parent.name}/{d.name}", score, msgs) for _ in range(a.n)]
    with ThreadPoolExecutor(8) as ex:
        res = list(ex.map(lambda j: harness_sample(client, a.model, j[2]), jobs))
    per = {}
    for (task, score, _), r in zip(jobs, res):
        per.setdefault(task, {"score": score, "samples": []})["samples"].append(r)
    for task, v in per.items():
        s = v["samples"]
        v["summary"] = {"answer": sum(x["tool"] == "answer" for x in s), "invalid_json": sum(not x["valid_json"] for x in s),
                        "truncated": sum(x["finish"] == "length" for x in s), "n": len(s),
                        "tools": {t: sum(x["tool"] == t for x in s) for t in sorted({x["tool"] for x in s})},
                        "mean_completion_tokens": sum(x["completion_tokens"] for x in s) / len(s),
                        "mean_reasoning_chars": sum(x["reasoning_chars"] for x in s) / len(s)}
    out["tasks"] = per
    Path(a.out).write_text(json.dumps(out, indent=1, ensure_ascii=False))
    for p in out["text"]:
        print("TEXT", json.dumps(p["answer"][:300], ensure_ascii=False))
    for task, v in per.items():
        print(json.dumps({"task": task, "score": v["score"], **v["summary"]}))


if __name__ == "__main__":
    main()
