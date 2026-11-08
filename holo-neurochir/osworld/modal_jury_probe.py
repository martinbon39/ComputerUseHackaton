"""Public jury endpoint 'holo-jury-probe' (CPU only, Modal account 2): replays one PRE-RECORDED OSWorld context
(jury_kit/contexts, chosen by id; no free text is accepted) on the original Holo-3.1-4B (account 1) and on the merge
(account 2), server side with the Bearer key, and returns each model's sampled action with the raw probability of the
first token of its tool name.

Request: GET /probe/<context_id> (or POST /probe {"context": "<id>"}); GET /contexts lists the ids; GET /health.
Sampling is the harness call of our OSWorld runs (holo_agent schema under structured_outputs, thinking on, T=0.8,
top_p=0.9, max_tokens=3072); one sample per model and request.
Guards: CORS open, 1 probe per IP every 5 s, 4 probes in flight, 120 s upstream timeout, and a gate (modal.Dict
holo-jury-gate, key "open") that is CLOSED by default so that no public call can wake an H100 outside the judging
window: osworld/modal_jury_gate.sh open|close|status.
Deploy: MODAL_PROFILE=martinbon39 modal deploy osworld/modal_jury_probe.py
"""
import asyncio, base64, json, math, os, re, time
from pathlib import Path

import modal

HERE = Path(__file__).resolve().parent
CONTEXTS_SRC = HERE.parent.parent / "jury_kit" / "contexts"
UPSTREAMS = {
    "original": ("https://emilejouannet--holo-vllm-serve.us-east.modal.run/v1", "Holo-3.1-4B-modal-orig"),
    "merge": ("https://martinbon39--holo-vllm-serve.us-east.modal.run/v1", "Holo-3.1-4B-merge_cua_b050"),
}
RATE_S, MAX_IN_FLIGHT, UPSTREAM_TIMEOUT_S, TOP_LOGPROBS = 5.0, 4, 120.0, 20
EVICTED = "[screenshot evicted]"

app = modal.App("holo-jury-probe")
image = (modal.Image.debian_slim(python_version="3.12").pip_install("fastapi[standard]==0.115.12", "httpx==0.28.1")
         .add_local_file(HERE / "jury_schema.json", "/app/jury_schema.json")
         .add_local_dir(CONTEXTS_SRC, "/app/contexts", ignore=["**/__pycache__"]))
gate = modal.Dict.from_name("holo-jury-gate", create_if_missing=True)


def load_contexts(root):
    out = {}
    for d in sorted(p for p in Path(root).iterdir() if (p / "context.json").exists()):
        c = json.loads((d / "context.json").read_text())
        msgs = []
        for m in c["messages"]:
            if "observation" not in m:
                msgs.append({"role": m["role"], "content": m["text"]})
                continue
            o = m["observation"]
            mid = ({"type": "text", "text": EVICTED} if o.get("evicted") else
                   {"type": "image_url", "image_url": {"url": "data:image/png;base64," +
                                                       base64.b64encode((d / o["image"]).read_bytes()).decode()}})
            msgs.append({"role": "user", "content": [{"type": "text", "text": "<observation>\n"}, mid,
                                                     {"type": "text", "text": "\n</observation>"}]})
        rec = c["recorded_final_step"]["json"]
        out[c["id"]] = {"messages": msgs, "public": {
            "id": c["id"], "task": c["task"], "step": c["step_t"], "kind": c["kind"], "episode_score": c["episode_score"],
            "images": [m["observation"]["image"] for m in c["messages"] if m.get("observation", {}).get("image")],
            "recorded": {"tool": rec["tool_call"]["tool_name"], "note": rec["note"], "thought": rec["thought"]},
            "recorded_answer_rate_8_samples_T0.8": c["recorded_answer_rate_8_samples_T0.8"]}}
    return out


def tool_token(logprobs, tool_names):
    """Raw probability of the first token of the tool name in the generated JSON, with its top alternatives."""
    toks = (logprobs or {}).get("content") or []
    text, starts = "", []
    for t in toks:
        starts.append(len(text)); text += t["token"]
    hits = list(re.finditer(r'"tool_name"\s*:\s*"', text))
    if not hits:
        return None
    end = hits[-1].end()
    i = next((k for k, st in enumerate(starts) if st <= end < st + len(toks[k]["token"])), None)
    if i is None:
        return None
    off = end - starts[i]
    chosen = toks[i]["token"]

    def tools_of(tok):
        part = tok[off:].split('"')[0] if tok[:off] == chosen[:off] else ""
        return [n for n in tool_names if part and n.startswith(part)]

    p = lambda lp: round(math.exp(lp), 4)
    alts = [{"token": a["token"], "p": p(a["logprob"]), "tools": tools_of(a["token"])}
            for a in toks[i].get("top_logprobs") or []]
    return {"token": chosen, "p": p(toks[i]["logprob"]), "tools": tools_of(chosen),
            "p_answer_token": next((a["p"] for a in alts if a["tools"] == ["answer"]), None), "top": alts[:8]}


async def ask(client, key, label, messages, schema, tool_names):
    url, model = UPSTREAMS[label]
    body = {"model": model, "messages": messages, "temperature": 0.8, "top_p": 0.9, "max_tokens": 3072,
            "reasoning_effort": "medium", "structured_outputs": {"json": schema},
            "chat_template_kwargs": {"enable_thinking": True}, "logprobs": True, "top_logprobs": TOP_LOGPROBS}
    t = time.time()
    try:
        r = await client.post(url + "/chat/completions", json=body, headers={"Authorization": f"Bearer {key}"},
                              timeout=UPSTREAM_TIMEOUT_S)
        r.raise_for_status()
        ch = r.json()["choices"][0]
        step = json.loads(ch["message"]["content"])
        call = dict(step.get("tool_call") or {})
        return {"model": model, "tool": call.pop("tool_name", None), "args": call, "note": step.get("note"),
                "thought": step.get("thought"), "reasoning": ch["message"].get("reasoning_content"),
                "finish": ch.get("finish_reason"), "latency_s": round(time.time() - t, 2),
                "tool_first_token": tool_token(ch.get("logprobs"), tool_names)}
    except Exception as e:  # noqa: BLE001 - one model failing must not hide the other's answer
        return {"model": model, "error": f"{type(e).__name__}: {str(e)[:200]}", "latency_s": round(time.time() - t, 2)}


@app.function(image=image, secrets=[modal.Secret.from_name("holo-vllm-key")], max_containers=1, min_containers=0,
              scaledown_window=300, timeout=180)
@modal.concurrent(max_inputs=32)
@modal.asgi_app()
def web():
    import httpx
    from fastapi import FastAPI, Request
    from fastapi.middleware.cors import CORSMiddleware
    from fastapi.responses import JSONResponse

    ctxs = load_contexts("/app/contexts")
    schema = json.loads(Path("/app/jury_schema.json").read_text())
    tool_names = sorted(d["properties"]["tool_name"]["const"] for d in schema["$defs"].values()
                        if "tool_name" in d.get("properties", {}))
    key = os.environ["VLLM_API_KEY"]
    last_seen, in_flight = {}, asyncio.Semaphore(MAX_IN_FLIGHT)
    client = httpx.AsyncClient()
    api = FastAPI(title="holo-jury-probe")
    api.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["GET", "POST"], allow_headers=["Content-Type"])

    def client_ip(req):
        return (req.headers.get("x-forwarded-for") or "").split(",")[0].strip() or (req.client.host if req.client else "?")

    @api.get("/health")
    async def health():
        return {"ok": True, "open": bool(await gate.get.aio("open", False)), "contexts": sorted(ctxs)}

    @api.get("/contexts")
    async def contexts():
        return [c["public"] for c in ctxs.values()]

    @api.get("/contexts/{cid}/{img}")
    async def screenshot(cid: str, img: str):
        from fastapi.responses import FileResponse
        if cid not in ctxs or f"images/{img}" not in ctxs[cid]["public"]["images"]:
            return JSONResponse({"error": "unknown context or image"}, 404)
        return FileResponse(f"/app/contexts/{cid}/images/{img}", media_type="image/png")

    async def probe(cid, req):
        if cid not in ctxs:
            return JSONResponse({"error": "unknown context id", "contexts": sorted(ctxs)}, 400)
        ip, now = client_ip(req), time.time()
        if now - last_seen.get(ip, 0) < RATE_S:
            return JSONResponse({"error": f"one probe every {RATE_S:.0f} s per IP"}, 429)
        last_seen[ip] = now
        for k in [k for k, v in last_seen.items() if now - v > 60]:
            del last_seen[k]
        print(f"probe {cid} from {ip}")
        if not await gate.get.aio("open", False):
            return JSONResponse({"error": "closed: the models are only served during the judging window"}, 503)
        if in_flight.locked():
            return JSONResponse({"error": "busy, retry in a few seconds"}, 429)
        async with in_flight:
            t = time.time()
            orig, merge = await asyncio.gather(*(ask(client, key, lab, ctxs[cid]["messages"], schema, tool_names)
                                                 for lab in ("original", "merge")))
        return {"context": ctxs[cid]["public"], "original": orig, "merge": merge, "latency_s": round(time.time() - t, 2)}

    @api.get("/probe/{cid}")
    async def probe_get(cid: str, request: Request):
        return await probe(cid, request)

    @api.post("/probe")
    async def probe_post(request: Request):
        if int(request.headers.get("content-length") or 0) > 1024:
            return JSONResponse({"error": "body too large"}, 413)
        try:
            body = await request.json()
            assert isinstance(body, dict) and set(body) == {"context"} and isinstance(body["context"], str)
        except Exception:  # noqa: BLE001 - any malformed body gets the same answer
            return JSONResponse({"error": 'body must be exactly {"context": "<id>"}'}, 400)
        return await probe(body["context"], request)

    return api
