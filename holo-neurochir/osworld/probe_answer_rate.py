"""Behavioural pre-launch check of an 'answer' lever: on recorded final answer steps (context rebuilt exactly as
holo.osw_replay does), sample the next action from each server with the harness' own call (holo_agent schema under
structured_outputs, thinking on, temperature 0.8, top_p 0.9, max_tokens 3072) and count the tool names.
Usage: PYTHONPATH=. ~/osw/venv/bin/python osworld/probe_answer_rate.py <task_dir> [<task_dir> ...] [--n 8]
       [--server http://127.0.0.1:8000/v1=Holo-3.1-4B] [--server http://127.0.0.1:8001/v1=Holo-3.1-4B-patched]
"""
import argparse, json, os, sys
from collections import Counter
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from openai import OpenAI

sys.path.insert(0, os.path.expanduser("~/osw/rtg/Env/OSWorld/holo_repro"))
from holo_agent.agent import TOOLS, build_schema, make_step_model  # noqa: E402
from holo.osw_replay import check_traj, rebuild, to_openai  # noqa: E402
from holo.osw_taxonomy import load_task  # noqa: E402

SCHEMA = build_schema(make_step_model(TOOLS))


def sample(url, model, messages):
    client = OpenAI(base_url=url, api_key="EMPTY", timeout=300)
    r = client.chat.completions.create(model=model, messages=messages, temperature=0.8, top_p=0.9, max_tokens=3072,
                                       reasoning_effort="medium",
                                       extra_body={"structured_outputs": {"json": SCHEMA},
                                                   "chat_template_kwargs": {"enable_thinking": True}})
    try:
        return json.loads(r.choices[0].message.content)["tool_call"]["tool_name"]
    except Exception:  # noqa: BLE001 - an unparsable answer is itself the measurement
        return "<unparsable>"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("tasks", nargs="+")
    ap.add_argument("--n", type=int, default=8)
    ap.add_argument("--server", action="append")
    a = ap.parse_args()
    servers = [s.split("=", 1) for s in (a.server or ["http://127.0.0.1:8000/v1=Holo-3.1-4B",
                                                       "http://127.0.0.1:8001/v1=Holo-3.1-4B-patched"])]
    jobs = []
    for t in a.tasks:
        d = Path(t)
        meta, score, steps = load_task(d)
        check_traj(d, steps)
        assert steps[-1]["tool_name"] == "answer", f"{d}: final step is not answer"
        msgs = to_openai(rebuild(d, steps, (d / "system_prompt.txt").read_text(encoding="utf-8"), len(steps) - 1))
        for url, model in servers:
            jobs += [(f"{d.parent.name}/{d.name}", model, url, msgs) for _ in range(a.n)]
    with ThreadPoolExecutor(8) as ex:
        names = list(ex.map(lambda j: sample(j[2], j[1], j[3]), jobs))
    out = {}
    for (task, model, _, _), name in zip(jobs, names):
        out.setdefault(task, {}).setdefault(model, Counter())[name] += 1
    for task, per in out.items():
        for model, c in per.items():
            print(json.dumps({"task": task, "model": model, "answer_rate": c["answer"] / sum(c.values()),
                              "tools": dict(c)}))


if __name__ == "__main__":
    main()
