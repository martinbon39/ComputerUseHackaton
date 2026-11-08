"""Measure a served checkpoint on an Astra construction cohort (train entries only), paired with the original.
For every cohort row (task_dir, step t) and seed in seed0..seed0+k-1: the next action under the harness-exact call
(holo_agent schema under structured_outputs, thinking on, T=0.8, top_p=0.9, top_k=20, max_tokens 3072, seed),
plus the cohort text prompts at T=0. One JSON line per generation, in the row format of astra-free's baseline.jsonl
(row, text, reasoning, content, token_ids, tool, parsed, answer, valid_nonanswer, error, truncated, n_out, seed,
finish_reason, stop_reason) plus server/model. Context rebuilt with holo.osw_replay from the local results copy.
Usage: PYTHONPATH=. ~/osw/venv/bin/python osworld/astra_cohort_probe.py <cohort.json> <results_root> <out_dir>
       --server URL=NAME[=ENVVAR] [--k 8] [--label <checkpoint>]
"""
import argparse, json, sys, urllib.request
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from probe_answer_rate import SCHEMA, client_for  # noqa: E402
from holo.osw_replay import check_traj, rebuild, to_openai  # noqa: E402
from holo.osw_taxonomy import load_task  # noqa: E402


def call(url, model, auth, messages, seed, structured):
    client = client_for(url, auth)
    extra = {"top_k": 20, "chat_template_kwargs": {"enable_thinking": structured}, "return_tokens_as_token_ids": True}
    kw = dict(temperature=0.8, top_p=0.9, max_tokens=3072, seed=seed, logprobs=True, top_logprobs=0)
    if structured:
        extra["structured_outputs"] = {"json": SCHEMA}
        kw["reasoning_effort"] = "medium"
    else:
        kw.update(temperature=0.0, max_tokens=256)
    try:
        r = client.chat.completions.create(model=model, messages=messages, extra_body=extra, **kw)
    except Exception as e:  # noqa: BLE001 - a failed request is recorded, not retried silently
        return {"error": repr(e)[:300]}
    ch = r.choices[0]; msg = ch.message
    reasoning = getattr(msg, "reasoning", None) or (msg.model_extra or {}).get("reasoning", "") or ""
    content = msg.content or ""
    ids = [int(t.token.split(":")[1]) for t in (ch.logprobs.content or [])] if ch.logprobs else []
    out = {"reasoning": reasoning, "content": content, "text": (reasoning + "\n</think>\n\n" if reasoning else "") + content,
           "token_ids": ids, "n_out": r.usage.completion_tokens if r.usage else len(ids),
           "finish_reason": ch.finish_reason, "stop_reason": getattr(ch, "stop_reason", None) or (ch.model_extra or {}).get("stop_reason"),
           "truncated": ch.finish_reason == "length", "error": None}
    if structured:
        try:
            parsed = json.loads(content)
            tool = parsed["tool_call"]["tool_name"]
        except Exception:  # noqa: BLE001 - an unparsable action is itself the measurement
            parsed, tool = None, None
        out.update(parsed=parsed, tool=tool, answer=tool == "answer", valid_nonanswer=tool is not None and tool != "answer")
    return out


REQUEST_SETTINGS = {"temperature": 0.8, "top_p": 0.9, "top_k": 20, "max_tokens": 3072, "reasoning_effort": "medium",
                    "enable_thinking": True, "structured_outputs": "holo_agent step schema (build_schema(make_step_model(TOOLS)))",
                    "seed": "per request", "text_prompts": {"temperature": 0.0, "max_tokens": 256, "enable_thinking": False}}


def server_info(url, model, auth):
    """vLLM version (/version, no auth) and the served model's root (/v1/models)."""
    info = {"url": url, "model": model}
    base = url[: -len("/v1")] if url.endswith("/v1") else url
    try:
        with urllib.request.urlopen(f"{base}/version", timeout=60) as r:
            info["vllm_version"] = json.load(r).get("version")
    except Exception as e:  # noqa: BLE001 - recorded, the measurement goes on
        info["vllm_version_error"] = repr(e)[:200]
    try:
        info["models"] = [{"id": m.id, "root": getattr(m, "root", None)} for m in client_for(url, auth).models.list().data]
    except Exception as e:  # noqa: BLE001
        info["models_error"] = repr(e)[:200]
    return info


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("cohort"); ap.add_argument("results_root"); ap.add_argument("out_dir")
    ap.add_argument("--server", action="append", required=True)
    ap.add_argument("--k", type=int, default=8)
    ap.add_argument("--label", default="")
    a = ap.parse_args()
    co = json.loads(Path(a.cohort).read_text())
    seeds = [co["seeds"][0] + i for i in range(a.k)]
    assert seeds[:len(co["seeds"])] == co["seeds"], "cohort seeds are not consecutive"
    servers = [(s.split("=", 2) + [None])[:3] for s in a.server]
    jobs = []
    for row in co["train"]:
        d = Path(a.results_root) / row["task_id"]
        meta, score, steps = load_task(d)
        check_traj(d, steps)
        assert steps[row["t"]]["tool_name"] == row["tool"], f"{row['task_id']}@{row['t']}: recorded tool differs"
        msgs = to_openai(rebuild(d, steps, (d / "system_prompt.txt").read_text(encoding="utf-8"), row["t"]))
        for url, model, auth in servers:
            jobs += [(row, url, model, auth, msgs, s, True) for s in seeds]
    for p in co["text_prompts"]:
        for url, model, auth in servers:
            jobs.append(({"text_prompt": p}, url, model, auth, [{"role": "user", "content": p}], 0, False))
    with ThreadPoolExecutor(8) as ex:
        res = list(ex.map(lambda j: call(j[1], j[2], j[3], j[4], j[5], j[6]), jobs))
    out = Path(a.out_dir); out.mkdir(parents=True, exist_ok=True)
    summary = {}
    with open(out / "generations.jsonl", "w") as f:
        for (row, url, model, _, _, seed, structured), r in zip(jobs, res):
            f.write(json.dumps({"label": a.label, "server": url, "model": model, "row": row, "seed": seed, **r},
                               ensure_ascii=False) + "\n")
            if structured:
                key = f"{model} | {row['label']} | {row['task_id']}@{row['t']}"
                s = summary.setdefault(key, {"answer": 0, "valid_nonanswer": 0, "invalid": 0, "error": 0, "n": 0})
                s["n"] += 1
                s["error" if r.get("error") else "answer" if r["answer"] else "valid_nonanswer" if r["valid_nonanswer"] else "invalid"] += 1
    (out / "summary.json").write_text(json.dumps({"label": a.label, "seeds": seeds, "request_settings": REQUEST_SETTINGS,
                                                  "servers": [server_info(*s) for s in servers], "per_row": summary}, indent=1))
    for k, v in summary.items():
        print(k, v)


if __name__ == "__main__":
    main()
