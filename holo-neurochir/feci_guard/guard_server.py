"""OpenAI-compatible relay in front of the frozen Claude verifier (verifier.verify_claude), so that runs without the
claude CLI (GitHub runners, via an ssh tunnel to the pod) can use the same judge. Bound to 127.0.0.1 only."""
from __future__ import annotations

import base64
import json
import os
import tempfile
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

import verifier
import wall

PORT = int(os.environ.get("GUARD_RELAY_PORT", 9911))
SLOTS = threading.Semaphore(int(os.environ.get("GUARD_RELAY_CONCURRENCY", 4)))
MODEL_ID = "claude-sonnet"


def _split(mode: str) -> tuple[str, str]:
    template = verifier.PROMPTS[mode][0].replace(verifier.READ_LINE, verifier.IMAGE_LINE)
    head, tail = template.split("{instruction}", 1)
    return head.format(), tail.split("{", 1)[0]


def _instruction(text: str, mode: str) -> str:
    head, tail = _split(mode)
    if not text.startswith(head):
        raise ValueError("prompt does not match the frozen verifier template")
    rest = text[len(head):]
    return rest[: rest.index(tail)] if tail and tail in rest else rest.split("\nJSON schema:", 1)[0]


class Handler(BaseHTTPRequestHandler):
    def _send(self, code: int, obj: dict) -> None:
        body = json.dumps(obj).encode()
        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, fmt, *args):  # one line per request, no payloads
        print(f"{self.address_string()} {fmt % args}", flush=True)

    def _raw(self, code: int, body: bytes, ctype: str) -> None:
        self.send_response(code)
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        if self.path.startswith("/wall"):
            if self.path.startswith("/wall/state"):
                return self._send(200, wall.state())
            if self.path.startswith("/wall/frame/"):
                img = wall.frame(self.path.split("/wall/frame/", 1)[1].split("?")[0].removesuffix(".png"))
                return self._raw(200, img, "image/png") if img else self._send(404, {"error": "no frame"})
            got = wall.page(self.path.split("?")[0] if self.path != "/wall" else "/wall/")
            return self._raw(200, *got) if got else self._send(404, {"error": "not found"})
        if self.path.rstrip("/").endswith("/models"):
            return self._send(200, {"object": "list", "data": [{"id": MODEL_ID, "object": "model"}]})
        self._send(404, {"error": "not found"})

    def do_POST(self):
        if self.path.startswith("/wall/"):
            body = json.loads(self.rfile.read(int(self.headers.get("Content-Length", 0))) or b"{}")
            if self.path.startswith("/wall/reset"):
                wall.reset()
            else:
                wall.post_event(body)
            return self._send(200, {"ok": True})
        if not self.path.rstrip("/").endswith("/chat/completions"):
            return self._send(404, {"error": "not found"})
        req = json.loads(self.rfile.read(int(self.headers.get("Content-Length", 0))) or b"{}")
        mode = "active" if str(req.get("model", "")).endswith(":active") else "passive"
        parts = req["messages"][-1]["content"]
        text = next(p["text"] for p in parts if p.get("type") == "text")
        url = next(p["image_url"]["url"] for p in parts if p.get("type") == "image_url")
        ext = ".png" if url.startswith("data:image/png") else ".jpg"
        with tempfile.TemporaryDirectory(prefix="relay_") as work:
            img = os.path.join(work, "screen" + ext)
            with open(img, "wb") as f:
                f.write(base64.b64decode(url.split(",", 1)[1]))
            with SLOTS:
                v = verifier.verify_claude(_instruction(text, mode), img, mode=mode)
        if not v["ok"]:
            return self._send(502, {"error": v["error"]})
        content = json.dumps({k: v[k] for k in ("requirements", "verdict", "missing_requirement", "evidence",
                                                 "next_action")})
        self._send(200, {"id": "relay", "object": "chat.completion", "model": MODEL_ID, "choices": [
            {"index": 0, "finish_reason": "stop", "message": {"role": "assistant", "content": content}}]})


if __name__ == "__main__":
    ThreadingHTTPServer(("127.0.0.1", PORT), Handler).serve_forever()
