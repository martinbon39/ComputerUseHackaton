"""Test doubles for the dry run: an OpenAI-compatible mock of the vLLM agent server (and of the verifier relay), and a
fake OSWorld DesktopEnv. No GPU, no VM, no network beyond 127.0.0.1.

MockServer records every request (model, seed, number of messages) in `requests` and in an optional jsonl file.
Agent replies are a deterministic function of the request seed only, so two loops that send the same seeds take the
same actions. A request without a seed gets a reply from an unseeded RNG.
Verifier replies (model == verifier_model): per instruction, INCOMPLETE on calls 1, 3, 5, ... and COMPLETE on 2, 4, ...,
so each guarded episode is refused once, then accepted.
"""
from __future__ import annotations

import io
import json
import random
import threading
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer


def agent_reply(seed: int | None, n_assistant: int) -> dict:
    rng = random.Random(seed) if seed is not None else random.Random()
    if n_assistant >= 2 and (rng.random() < 0.4 or n_assistant >= 6):
        tc = {"tool_name": "answer", "content": f"Task completed (mock, seed {seed})."}
    else:
        tc = {"tool_name": "click", "element": "mock element", "x": rng.randrange(1000), "y": rng.randrange(1000)}
    return {"note": None, "thought": f"mock step {n_assistant}", "tool_call": tc}


def verifier_reply(first: bool) -> dict:
    if first:
        return {"requirements": [{"requirement": "mock requirement", "status": "no", "evidence": "mock: not done"}],
                "verdict": "INCOMPLETE", "missing_requirement": "mock requirement", "evidence": "mock: not done",
                "next_action": "Do the mock thing."}
    return {"requirements": [{"requirement": "mock requirement", "status": "yes", "evidence": "mock: done"}],
            "verdict": "COMPLETE", "missing_requirement": "", "evidence": "", "next_action": ""}


class MockServer:
    def __init__(self, served_model: str = "Holo-3.1-4B-mock", verifier_model: str = "claude-sonnet",
                 log_path: str | None = None, port: int = 0, fail_substring: str | None = None,
                 hang_substring: str | None = None):
        self.fail_substring, self.hang_substring = fail_substring, hang_substring
        self.served_model, self.verifier_model, self.log_path = served_model, verifier_model, log_path
        self.requests: list[dict] = []
        self._verifier_calls: dict[str, int] = {}
        self._lock = threading.Lock()
        srv = self

        class H(BaseHTTPRequestHandler):
            def log_message(self, *a):
                pass

            def _send(self, code, obj):
                body = json.dumps(obj).encode()
                self.send_response(code)
                self.send_header("Content-Type", "application/json")
                self.send_header("Content-Length", str(len(body)))
                self.end_headers()
                self.wfile.write(body)

            def do_GET(self):
                if self.path.rstrip("/").endswith("/models"):
                    return self._send(200, {"object": "list", "data": [{"id": srv.served_model, "object": "model"}]})
                if self.path.rstrip("/").endswith("/version"):
                    return self._send(200, {"version": "mock"})
                self._send(404, {"error": "not found"})

            def do_POST(self):
                raw = self.rfile.read(int(self.headers.get("Content-Length", 0))) or b"{}"
                if srv.hang_substring and srv.hang_substring.encode() in raw:
                    time.sleep(120)
                if srv.fail_substring and srv.fail_substring.encode() in raw:
                    return self._send(500, {"error": "mock failure"})
                req = json.loads(raw)
                self._send(200, srv.handle(req))

        self.httpd = ThreadingHTTPServer(("127.0.0.1", port), H)
        self.port = self.httpd.server_address[1]
        self.base_url = f"http://127.0.0.1:{self.port}/v1"
        self._t = threading.Thread(target=self.httpd.serve_forever, daemon=True)

    def handle(self, req: dict) -> dict:
        msgs = req.get("messages", [])
        model = req.get("model")
        if model == self.verifier_model:
            text = "".join(p.get("text", "") for m in msgs for p in (m.get("content") if isinstance(m.get("content"), list) else []))
            with self._lock:
                n = self._verifier_calls.get(text, 0)
                self._verifier_calls[text] = n + 1
                first = n % 2 == 0
            content = json.dumps(verifier_reply(first))
            reasoning = ""
        else:
            n_assist = sum(1 for m in msgs if m.get("role") == "assistant")
            content = json.dumps(agent_reply(req.get("seed"), n_assist))
            reasoning = "mock reasoning"
        rec = {"model": model, "seed": req.get("seed"), "n_messages": len(msgs), "t": time.time()}
        with self._lock:
            self.requests.append(rec)
            if self.log_path:
                with open(self.log_path, "a") as f:
                    f.write(json.dumps(rec) + "\n")
        return {"id": "mock", "object": "chat.completion", "created": int(time.time()), "model": model,
                "choices": [{"index": 0, "finish_reason": "stop",
                             "message": {"role": "assistant", "content": content, "reasoning": reasoning}}],
                "usage": {"prompt_tokens": 1, "completion_tokens": 1, "total_tokens": 2}}

    def start(self) -> "MockServer":
        self._t.start()
        return self

    def stop(self) -> None:
        self.httpd.shutdown()


def _png(w: int = 64, h: int = 36) -> bytes:
    from PIL import Image
    b = io.BytesIO()
    Image.new("RGB", (w, h), (40, 80, 120)).save(b, format="PNG")
    return b.getvalue()


class _Controller:
    def __init__(self, png: bytes):
        self.png = png

    def get_screenshot(self):
        return self.png

    def start_recording(self):
        pass

    def end_recording(self, path):
        pass


class FakeDesktopEnv:
    """The subset of desktop_env.DesktopEnv that run_one() and OSWorldComputerEnv use. evaluate() returns 0.0, so an
    accepted answer is a false "done"."""

    def __init__(self, screen_width: int = 1920, screen_height: int = 1080, score: float = 0.0):
        self.screen_width, self.screen_height, self.score = screen_width, screen_height, score
        self.controller = _Controller(_png())
        self.actions: list[str] = []

    def _get_obs(self):
        return {"screenshot": self.controller.png}

    def reset(self, task_config=None):
        self.actions = []
        return self._get_obs()

    def step(self, action, pause=0.0):
        self.actions.append(action)
        return self._get_obs(), 0.0, action in ("DONE", "FAIL"), {}

    def evaluate(self):
        return self.score

    def close(self):
        pass
