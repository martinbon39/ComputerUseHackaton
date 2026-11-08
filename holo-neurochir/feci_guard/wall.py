"""Live wall: GitHub runners push each OSWorld step (screenshot + event) through the same tunnel as the judge relay;
the wall page polls /wall/state and shows every VM moving in real time.

POST /wall/event  JSON {tile, task, domain, step, png_b64?, kind: start|step|answer|guard|done, text?, verdict?, score?}
GET  /wall/state  JSON {tiles: {tile: {...latest...}}, events: [last 200], t}
GET  /wall/frame/<tile>.png  latest screenshot of that tile
GET  /wall/       the page (holo-neurochir/demo_live/wall/index.html)
"""
from __future__ import annotations

import base64
import json
import os
import threading
import time

PAGE_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "demo_live", "wall")
LOG = os.path.expanduser(os.environ.get("WALL_LOG", "~/osw/wall_events.jsonl"))
_lock = threading.Lock()
_tiles: dict[str, dict] = {}
_frames: dict[str, bytes] = {}
_events: list[dict] = []


def post_event(obj: dict) -> None:
    tile = str(obj.get("tile", "?"))[:64]
    png = obj.pop("png_b64", None)
    obj["t"] = time.time()
    with _lock:
        if png:
            _frames[tile] = base64.b64decode(png)
            obj["has_frame"] = True
        cur = _tiles.setdefault(tile, {})
        cur.update({k: v for k, v in obj.items() if v is not None})
        _events.append(obj)
        del _events[:-200]
    with open(LOG, "a") as f:
        f.write(json.dumps(obj) + "\n")


def state() -> dict:
    with _lock:
        return {"tiles": dict(_tiles), "events": list(_events[-60:]), "t": time.time()}


def frame(tile: str) -> bytes | None:
    with _lock:
        return _frames.get(tile)


def reset() -> None:
    with _lock:
        _tiles.clear(), _frames.clear(), _events.clear()


def page(path: str) -> tuple[bytes, str] | None:
    name = path.split("/wall/", 1)[-1] or "index.html"
    full = os.path.realpath(os.path.join(PAGE_DIR, name))
    if not full.startswith(os.path.realpath(PAGE_DIR)) or not os.path.isfile(full):
        return None
    ctype = {"html": "text/html", "js": "text/javascript", "css": "text/css", "png": "image/png",
             "json": "application/json", "mp4": "video/mp4"}.get(full.rsplit(".", 1)[-1], "application/octet-stream")
    with open(full, "rb") as f:
        return f.read(), ctype
