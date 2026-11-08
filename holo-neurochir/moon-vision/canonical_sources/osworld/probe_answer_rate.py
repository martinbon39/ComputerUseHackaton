"""Behavioural pre-launch check of an 'answer' lever: on recorded steps (context rebuilt exactly as holo.osw_replay
does), sample the next action from each server with the harness' own call (holo_agent schema under
structured_outputs, thinking on, temperature 0.8, top_p 0.9, max_tokens 3072) and count the tool names; the
sampled x,y (0-1000 grid) are kept next to the recorded action for pointing tools.
A step is <task_dir> (its final answer step) or <task_dir>@<t> (step t, e.g. a healthy mid-trajectory step).
A server is URL=MODEL or URL=MODEL=ENVVAR, where the environment variable ENVVAR holds the auth headers, one
"Name: value" per line (kept out of the command line and the logs); "Authorization: Bearer X" becomes the api key.
Usage: PYTHONPATH=. ~/osw/venv/bin/python osworld/probe_answer_rate.py <step> [<step> ...] [--n 8] [--out f.json]
       [--server http://127.0.0.1:8000/v1=Holo-3.1-4B] [--server https://…modal.run/v1=NAME=MODAL_HEADERS]
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


def client_for(url, auth_env):
    headers = {}
    if auth_env:
        for line in os.environ[auth_env].splitlines():
            if line.strip():
                k, v = line.split(":", 1)
                headers[k.strip()] = v.strip()
    auth = headers.pop("Authorization", "")
    key = auth[len("Bearer "):] if auth.startswith("Bearer ") else "EMPTY"
    assert not auth or key != "EMPTY", "Authorization header must be 'Bearer <token>'"
    return OpenAI(base_url=url, api_key=key, default_headers=headers or None, timeout=300)


def sample(url, model, messages, auth_env=None):
    client = client_for(url, auth_env)
    r = client.chat.completions.create(model=model, messages=messages, temperature=0.8, top_p=0.9, max_tokens=3072,
                                       reasoning_effort="medium",
                                       extra_body={"structured_outputs": {"json": SCHEMA},
                                                   "chat_template_kwargs": {"enable_thinking": True}})
    try:
        return json.loads(r.choices[0].message.content)["tool_call"]
    except Exception:  # noqa: BLE001 - an unparsable answer is itself the measurement
        return {"tool_name": "<unparsable>"}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("tasks", nargs="+")
    ap.add_argument("--n", type=int, default=8)
    ap.add_argument("--server", action="append")
    ap.add_argument("--out")
    a = ap.parse_args()
    servers = [(s.split("=", 2) + [None])[:3] for s in (a.server or ["http://127.0.0.1:8000/v1=Holo-3.1-4B",
                                                                      "http://127.0.0.1:8001/v1=Holo-3.1-4B-patched"])]
    jobs = []
    for spec in a.tasks:
        path, _, t = spec.partition("@")
        d = Path(path)
        meta, score, steps = load_task(d)
        check_traj(d, steps)
        if not t:
            assert steps[-1]["tool_name"] == "answer", f"{d}: final step is not answer (give <task_dir>@<t>)"
        t = int(t) if t else len(steps) - 1
        msgs = to_openai(rebuild(d, steps, (d / "system_prompt.txt").read_text(encoding="utf-8"), t))
        rec = steps[t]["tool_call"]
        label = f"{d.parent.name}/{d.name}@{t}({rec['tool_name']}" + (f" {rec['x']},{rec['y']})" if "x" in rec else ")")
        for url, model, auth in servers:
            jobs += [(label, model, url, msgs, auth) for _ in range(a.n)]
    with ThreadPoolExecutor(8) as ex:
        calls = list(ex.map(lambda j: sample(j[2], j[1], j[3], j[4]), jobs))
    out, pts = {}, {}
    for (task, model, *_), tc in zip(jobs, calls):
        out.setdefault(task, {}).setdefault(model, Counter())[tc["tool_name"]] += 1
        if "x" in tc:
            pts.setdefault((task, model), []).append([tc["x"], tc["y"]])
    rows = [{"step": task, "model": model, "answer_rate": c["answer"] / sum(c.values()), "tools": dict(c),
             "points": pts.get((task, model), [])} for task, per in out.items() for model, c in per.items()]
    for r in rows:
        print(json.dumps(r))
    if a.out:
        Path(a.out).write_text(json.dumps(rows, indent=1))


if __name__ == "__main__":
    main()
