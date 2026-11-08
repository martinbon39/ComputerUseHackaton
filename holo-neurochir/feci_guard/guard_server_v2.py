"""Relay for Feci Guard v2 on 127.0.0.1:9912 (v1 relay: guard_server.py on 9911, untouched). Runs exactly the
offline-evaluated verifier: verifier_v2.verify_v2(instruction, final, history, actions, model="opus").
POST /v1/chat/completions with one user message: a text part "FECI_V2 {json: instruction, actions}" then the images
(history oldest first, the final screen last) as data URLs. Returns the verdict JSON as the message content, or HTTP
502 when there is no verdict (the client then lets the answer pass). GET /v1/models lists "feci-guard-v2".
127.0.0.1 only, no authentication, at most MAX_CONCURRENT claude processes (others wait), one log line per request.
Usage: python guard_server_v2.py [--port 9912] [--log ~/osw/guard_server_v2.jsonl]
"""
from __future__ import annotations

import argparse
import base64
import json
import os
import sys
import tempfile
import threading
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import feci_guard_v2  # noqa: E402
import verifier_v2  # noqa: E402

MODEL_ID = "feci-guard-v2"
MAX_CONCURRENT = 3
SLOTS = threading.BoundedSemaphore(MAX_CONCURRENT)
LOG_LOCK = threading.Lock()


class Handler(BaseHTTPRequestHandler):
    def _send(self, code, obj):
        data = json.dumps(obj, ensure_ascii=False).encode()
        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def log_message(self, *a):
        pass

    def do_GET(self):
        if self.path.rstrip("/").endswith("/models"):
            return self._send(200, {"object": "list", "data": [{"id": MODEL_ID, "object": "model"}]})
        self._send(404, {"error": {"message": "not found"}})

    def do_POST(self):
        if self.path.rstrip("/") != "/v1/chat/completions":
            return self._send(404, {"error": {"message": "not found"}})
        t0, rec = time.time(), {"t": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())}
        try:
            body = json.loads(self.rfile.read(int(self.headers.get("Content-Length", 0))))
            parts = body["messages"][-1]["content"]
            meta = json.loads(next(p["text"] for p in parts if p.get("type") == "text" and p["text"].startswith("FECI_V2 "))[8:])
            images = [base64.b64decode(p["image_url"]["url"].split(",", 1)[1]) for p in parts if p.get("type") == "image_url"]
            assert images, "no image"
        except Exception as e:  # noqa: BLE001
            return self._send(400, {"error": {"message": f"bad request: {type(e).__name__}: {str(e)[:200]}"}})
        rec.update(task=meta["instruction"][:120], images=len(images), unblock=bool(meta.get("unblock")))
        with SLOTS:
            rec["queued_s"] = round(time.time() - t0, 1)
            with tempfile.TemporaryDirectory(prefix="feci2_relay_") as d:
                paths = []
                for i, img in enumerate(images):
                    paths.append(os.path.join(d, f"img_{i}.png"))
                    with open(paths[-1], "wb") as f:
                        f.write(img)
                v = verifier_v2.verify_v2(meta["instruction"], paths[-1], paths[:-1], meta.get("actions", []),
                                          model=feci_guard_v2.MODEL, timeout=feci_guard_v2.SERVER_TIMEOUT_S,
                                          unblock=bool(meta.get("unblock")))
        rec.update(verdict=v.get("verdict"), error=v.get("error"), latency_s=round(time.time() - t0, 1))
        with LOG_LOCK, open(self.server.log_path, "a", encoding="utf-8") as f:
            f.write(json.dumps(rec, ensure_ascii=False) + "\n")
        if not v.get("ok"):
            return self._send(502, {"error": {"message": f"no verdict: {v.get('error')}"}})
        self._send(200, {"id": f"feci2-{int(t0 * 1000)}", "object": "chat.completion", "model": MODEL_ID,
                         "choices": [{"index": 0, "finish_reason": "stop",
                                      "message": {"role": "assistant", "content": json.dumps(v, ensure_ascii=False)}}]})


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--port", type=int, default=9912)
    ap.add_argument("--log", default=os.path.expanduser("~/osw/guard_server_v2.jsonl"))
    a = ap.parse_args()
    srv = ThreadingHTTPServer(("127.0.0.1", a.port), Handler)
    srv.daemon_threads = True
    srv.log_path = a.log
    print(f"feci guard v2 relay on http://127.0.0.1:{a.port}/v1 ({MAX_CONCURRENT} concurrent), log {a.log}", flush=True)
    srv.serve_forever()


if __name__ == "__main__":
    main()
