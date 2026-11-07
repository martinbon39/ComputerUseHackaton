"""'IRM' dashboard backend. Launch:  .venv\\Scripts\\python -m uvicorn dashboard.server:app --port 8000
Then open http://127.0.0.1:8000
- Replay mode (default, reliable): streams a precomputed demo/<name>.json over WebSocket.
- Live mode: runs original then patched Holo on the chosen task/seed, streaming each step as it happens.
"""
import holo.settings as S
import asyncio, json, threading
from pathlib import Path
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.responses import FileResponse, JSONResponse

app = FastAPI()
HERE = Path(__file__).parent
DEMO_DIR = S.ROOT / "demo"
_models = {}


@app.get("/")
def index():
    return FileResponse(HERE / "index.html")


@app.get("/api/demos")
def demos():
    return sorted(p.stem for p in DEMO_DIR.glob("*.json"))


@app.get("/api/meta")
def meta():
    out = {}
    for name in ["results.json", "patch_spec.json"]:
        p = S.ROOT / name
        if p.exists():
            out[name.split(".")[0]] = json.loads(p.read_text(encoding="utf-8"))
    return JSONResponse(out)


def _interleave(demo):
    o, p = demo["original"]["steps"], demo["patched"]["steps"]
    for t in range(max(len(o), len(p))):
        if t < len(o): yield o[t]
        if t < len(p): yield p[t]
    yield {"arm": "original", "done": True, **demo["original"]["outcome"]}
    yield {"arm": "patched", "done": True, **demo["patched"]["outcome"]}


@app.websocket("/ws/replay/{name}")
async def ws_replay(ws: WebSocket, name: str, speed: float = 1.0):
    await ws.accept()
    demo = json.loads((DEMO_DIR / f"{name}.json").read_text(encoding="utf-8"))
    head = {k: demo[k] for k in ("name", "task", "seed", "goal", "threshold", "spec", "n_layers")}
    try:
        await ws.send_json({"type": "header", **head})
        for ev in _interleave(demo):
            await ws.send_json({"type": "step", **ev})
            await asyncio.sleep(1.2 / max(speed, 0.1))
        await ws.send_json({"type": "end"})
    except WebSocketDisconnect:
        pass


@app.websocket("/ws/live/{task}/{seed}")
async def ws_live(ws: WebSocket, task: str, seed: int):
    await ws.accept()
    from holo.model import Holo
    from holo.surgery import load_spec, apply_patch_inplace
    from holo.demo_record import record, make_gauge
    spec_path = S.ROOT / "patch_spec.json"
    spec = load_spec(spec_path)
    if "orig" not in _models:
        _models["orig"] = Holo()
        hp = Holo(); apply_patch_inplace(hp.model, spec); _models["patched"] = hp
    _, thr = make_gauge(spec)
    q: asyncio.Queue = asyncio.Queue()
    loop = asyncio.get_running_loop()
    emit = lambda ev: loop.call_soon_threadsafe(q.put_nowait, ev)

    def worker():
        try:
            record(task, seed, spec_path, f"live_{task}_s{seed}", holo_orig=_models["orig"],
                   holo_patched=_models["patched"], emit=emit)
        except Exception as e:  # surfaced to the UI
            emit({"error": repr(e)})
        emit({"end": True})
    await ws.send_json({"type": "header", "name": "live", "task": task, "seed": seed, "goal": "",
                        "threshold": thr, "spec": spec, "n_layers": _models["orig"].n_layers})
    threading.Thread(target=worker, daemon=True).start()
    try:
        while True:
            ev = await q.get()
            if ev.get("end"):
                await ws.send_json({"type": "end"}); break
            await ws.send_json({"type": "error" if "error" in ev else "step", **ev})
    except WebSocketDisconnect:
        pass
