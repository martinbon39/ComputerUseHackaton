"""Live duel page server (orbit): two OSWorld VMs side by side, original Holo-3.1-4B vs the merged model, same task,
at the same time; per-side STOP and global STOP; every duel recorded (events.jsonl + frames) and replayable.
Each side is a duel_side.py process started through ~/osw/osh (docker + kvm), with run_osw.sh's exact environment.
Usage: devcap python duel_server.py [--port 8765] [--root ~/osw/duels] [--preset pod|modal]
  page:   http://127.0.0.1:8765/            replay: http://127.0.0.1:8765/?replay=<duel_id>
Public through a tunnel (cloudflared -> 127.0.0.1:8765): the page, replays and state are read-only for everyone;
starting or stopping VMs needs the key in ~/.duel_key, given once as ?k=<key> (then an HttpOnly SameSite=Strict
cookie, and a redirect drops it from the address bar) or in the cookie; 403 otherwise.
"""
import argparse, hmac, json, os, re, signal, subprocess, threading, time, urllib.request
from http.server import ThreadingHTTPServer, BaseHTTPRequestHandler
from pathlib import Path
from urllib.parse import urlparse, parse_qs

HERE = Path(__file__).resolve().parent
TASKS = [  # original made a false 'done' and the merged model succeeded, in recorded runs
    "libreoffice_calc/1de60575-bb6e-4c3d-9e6a-2fa699f9f197",  # bench-wall: repaired 2/2 with the guard in replay
    "libreoffice_impress/550ce7e7-747b-495f-b122-acdc4d0b8e54",  # demo-director's live rehearsal task
    "libreoffice_impress/b8adbc24-cef2-4b15-99d5-ecbe7ff445eb",
    "chrome/9f935cce-0a9f-435f-8007-817732bfc0a5",
    "os/bedcedc4-4d72-425e-ad62-21960b11fe0d",
]
PRESETS = {
    "pod": {"left": "http://127.0.0.1:8000/v1=Holo-3.1-4B",
            "right": "http://127.0.0.1:8001/v1=Holo-3.1-4B-merge_cua_b050"},
    # Feci Guard demo: the same original model on both sides, only the guard differs (guard=right)
    "pod_guard": {"left": "http://127.0.0.1:8000/v1=Holo-3.1-4B", "right": "http://127.0.0.1:8000/v1=Holo-3.1-4B"},
    # Feci Guard demo on Modal (pod down): the original on account 1 on both sides
    "modal_guard": {"left": "https://emilejouannet--holo-vllm-serve.us-east.modal.run/v1=Holo-3.1-4B-modal-orig=MODAL_HDR",
                    "right": "https://emilejouannet--holo-vllm-serve.us-east.modal.run/v1=Holo-3.1-4B-modal-orig=MODAL_HDR"},
    "modal": {"left": "https://emilejouannet--holo-vllm-serve.us-east.modal.run/v1=Holo-3.1-4B-modal-orig=MODAL_HDR",
              "right": "https://martinbon39--holo-vllm-serve.us-east.modal.run/v1=Holo-3.1-4B-merge_cua_b050=MODAL_HDR"},
}
LABELS = {"left": "Holo-3.1-4B original", "right": "Holo-3.1-4B modifié (fusion des poids)"}
GUARD_LABELS = {"left": "Holo-3.1-4B seul", "right": "Holo-3.1-4B"}  # pod_guard: same model, the badge says + Feci Guard
EXAMPLES = Path.home() / "osw/rtg/Env/OSWorld/evaluation_examples/examples"
MIN_AVAIL_GB = 15  # two 5 GB VMs plus the 5 GB floor of the VPS rules
ENDED = {"done", "stopped", "error", "vm_closed", "vm_close_failed"}


def env_line():
    line = re.search(r"cd ~/osw/rtg/Env/OSWorld && export [^&]*&&", (Path.home() / "osw/run_osw.sh").read_text())
    assert line, "run_osw.sh layout changed"
    return line.group(0)


def guard_available():
    return (HERE.parent.parent / "feci_guard" / "run_holo_guard.py").exists()


def served(server):
    """True when the server lists the model: never boot two VMs against a dead or unready endpoint."""
    url, name, auth = (server.split("=", 2) + [None])[:3]
    req = urllib.request.Request(url.rstrip("/") + "/models")
    if auth:  # MODAL_HDR: the bearer token is read here, never put on a command line or logged
        req.add_header("Authorization", "Bearer " + (Path.home() / ".holo_modal_key").read_text().strip())
    try:
        with urllib.request.urlopen(req, timeout=20) as r:
            return any(m.get("id") == name for m in json.load(r).get("data", []))
    except Exception:  # noqa: BLE001 - unreachable, cold or wrong model: not served
        return False


def mem_available_gb():
    for l in open("/proc/meminfo"):
        if l.startswith("MemAvailable:"):
            return int(l.split()[1]) / 2 ** 20
    return 0.0


def read_events(path, start=0):
    if not path.exists():
        return [], start
    lines = path.read_text().splitlines()
    return [json.loads(l) for l in lines[start:] if l.strip()], len(lines)


def side_pid(side_dir):
    for e in read_events(side_dir / "events.jsonl")[0]:
        if e.get("pid"):
            return e["pid"]
    return None


def alive(pid):
    return pid is not None and Path(f"/proc/{pid}").exists()


class Duels:
    def __init__(self, root, preset):
        self.root, self.preset, self.lock, self.procs = Path(root), preset, threading.Lock(), {}
        self.root.mkdir(parents=True, exist_ok=True)

    def running(self):
        """Duels with a side still alive: the launch (ssh) not returned yet, or a side pid alive (survives a restart)."""
        ids = {d for d, ps in self.procs.items() if any(p.poll() is None for p in ps.values())}
        ids |= {d.name for d in self.root.iterdir() if any(alive(side_pid(d / s)) for s in ("left", "right"))}
        return sorted(ids)

    def start(self, task, preset=None, max_steps=50, guard="none"):
        preset = preset or self.preset
        if guard not in ("none", "left", "right", "both"):
            raise ValueError(f"bad guard {guard}")
        if guard != "none" and not guard_available():
            raise ValueError("Feci Guard module not installed (holo-neurochir/feci_guard)")
        if task not in TASKS and not (EXAMPLES / f"{task}.json").exists():
            raise ValueError(f"unknown task {task}")
        with self.lock:
            if self.running():
                raise RuntimeError(f"a duel is already running: {self.running()[0]}")
            down = [PRESETS[preset][s] for s in ("left", "right") if not served(PRESETS[preset][s])]
            if down:
                raise RuntimeError("model not served: " + ", ".join(sorted({d.split("=")[1] + " @ " + d.split("=")[0] for d in down})))
            avail = mem_available_gb()
            if avail < MIN_AVAIL_GB:
                raise RuntimeError(f"RAM: {avail:.1f} GB available < {MIN_AVAIL_GB} GB needed for two VMs")
            duel_id = time.strftime("%Y%m%d-%H%M%S", time.gmtime()) + "_" + task.replace("/", "_")[:40]
            d = self.root / duel_id
            instruction = json.loads((EXAMPLES / f"{task}.json").read_text())["instruction"]
            meta = {"id": duel_id, "task": task, "instruction": instruction, "t0": time.time(), "preset": preset,
                    "max_steps": max_steps, "sides": {}}
            procs = {}
            for side in ("left", "right"):
                server = PRESETS[preset][side]
                sd = d / side; sd.mkdir(parents=True)
                guarded = guard in (side, "both")
                meta["sides"][side] = {"label": (GUARD_LABELS if preset == "pod_guard" else LABELS)[side],
                                       "model": server.split("=")[1], "server": server.split("=")[0], "guard": guarded}
                key = 'export MODAL_HDR="Authorization: Bearer $(cat ~/.holo_modal_key)" && ' if server.endswith("=MODAL_HDR") else ""
                cmd = (f"{env_line()} {key}PYTHONPATH={HERE.parent.parent} ~/osw/venv/bin/python {HERE / 'duel_side.py'} "
                       f"--task {task} --server '{server}' --out {sd} --max_steps {int(max_steps)}{' --guard' if guarded else ''} > {sd / 'side.log'} 2>&1")
                procs[side] = subprocess.Popen([str(Path.home() / "osw/osh"), cmd], stdin=subprocess.DEVNULL,
                                               stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            (d / "meta.json").write_text(json.dumps(meta, ensure_ascii=False, indent=1))
            self.procs[duel_id] = procs
            return duel_id

    def stop(self, duel_id, sides):
        d = self.root / duel_id
        for side in sides:
            sd = d / side
            phases = [e["phase"] for e in read_events(sd / "events.jsonl")[0] if e["kind"] == "phase"]
            if not sd.exists() or (ENDED | {"stop_requested"}) & set(phases):
                continue
            (sd / "STOP").touch()
            with open(sd / "events.jsonl", "a") as f:
                f.write(json.dumps({"t": round(time.time(), 3), "kind": "phase", "phase": "stop_requested"}) + "\n")
            threading.Thread(target=self._kill, args=(sd,), daemon=True).start()

    def _kill(self, sd):
        """SIGTERM the side at once (it closes its VM in a finally), SIGKILL if it is still alive after 60 s."""
        for _ in range(60):  # the pid is written once the side process has started
            pid = side_pid(sd)
            if pid:
                break
            time.sleep(1)
        if not alive(pid):
            return
        os.kill(pid, signal.SIGTERM)
        for _ in range(60):
            if not alive(pid):
                return
            time.sleep(1)
        os.kill(pid, signal.SIGKILL)
        ids = [e["container"] for e in read_events(sd / "events.jsonl")[0] if e.get("container")]
        if ids:  # killed during its VM close: remove the container it recorded
            subprocess.run([str(Path.home() / "osw/osh"), f"docker rm -f {ids[-1]}"], timeout=120)

    def listing(self):
        out = []
        for d in sorted(self.root.iterdir(), reverse=True):
            if not (d / "meta.json").exists():
                continue
            meta = json.loads((d / "meta.json").read_text())
            res = {}
            for side in ("left", "right"):
                evs = read_events(d / side / "events.jsonl")[0]
                v = [e for e in evs if e["kind"] == "verdict"]
                ph = [e["phase"] for e in evs if e["kind"] == "phase"]
                res[side] = {"verdict": v[-1] if v else None, "last_phase": next((p for p in reversed(ph) if p in ("done", "stopped", "error")), ph[-1] if ph else None),
                             "steps": sum(e["kind"] == "step" for e in evs)}
            out.append({"id": d.name, "task": meta["task"], "t0": meta["t0"], "preset": meta.get("preset"),
                        "running": d.name in self.running(), "sides": res})
        return out


DUEL_ID = re.compile(r"[\w-]+")

# /try: six fixed final screenshots of real OSWorld episodes where the agent said "done" (3 false, 3 true, from the
# frozen verif_study corpus), checked live by the frozen Feci Guard verifier through the judge relay; no key, but one
# check at a time and at most 60 per hour.
STUDY = HERE.parent.parent / "verif_study"
TRY_IDS = ["diag1__libreoffice_calc__1de60575-bb6e-4c3d-9e6a-2fa699f9f197", "diag1__chrome__368d9ba4-203c-40c1-9fa3-da2f1430ce63",
           "diag1__libreoffice_impress__8979838c-54a5-4454-a2b8-3d135a1a5c8f", "diag1__gimp__7b7617bd-57cc-468e-9c91-40c4ec2bcb3d",
           "diag1__chrome__9f3f70fc-5afc-4958-a7b7-3bb4fcb01805", "diag1__libreoffice_calc__0cecd4f3-74de-457b-ba94-29ad6b5dafb6"]
TRY_RELAY, TRY_MODEL, TRY_PER_HOUR = "http://127.0.0.1:9911/v1", "claude-sonnet", 60


class Try:
    def __init__(self):
        man = {e["episode_id"]: e for e in json.loads((STUDY / "manifest.json").read_text())}
        self.cases = [man[i] for i in TRY_IDS]
        self.lock, self.calls, self.jpg = threading.Lock(), [], {}

    def image(self, n):
        if n not in self.jpg:
            from io import BytesIO
            from PIL import Image
            buf = BytesIO(); Image.open(STUDY / self.cases[n]["image_path"]).convert("RGB").save(buf, "JPEG", quality=85)
            self.jpg[n] = buf.getvalue()
        return self.jpg[n]

    def verify(self, n):
        if not self.lock.acquire(blocking=False):
            return 429, {"error": "busy, retry in 30 s"}
        try:
            now = time.time(); self.calls = [t for t in self.calls if now - t < 3600]
            if len(self.calls) >= TRY_PER_HOUR:
                return 429, {"error": "busy, retry in 30 s"}
            self.calls.append(now)
            import sys
            sys.path.insert(0, str(HERE.parent.parent / "feci_guard"))
            import verifier  # the frozen verifier's own OpenAI-compatible client, pointed at the judge relay
            os.environ["GUARD_BASE_URL"] = TRY_RELAY
            c = self.cases[n]
            v = verifier.verify_openai(c["instruction"], str(STUDY / c["image_path"]), TRY_MODEL)
            return 200, {"verdict": v.get("verdict"), "requirements": v.get("requirements") or [], "error": v.get("error"),
                         "latency_s": v.get("latency_s"), "official": c["score"]}
        finally:
            self.lock.release()


class Handler(BaseHTTPRequestHandler):
    duels: Duels = None
    tryer: Try = None
    guard_preset = "modal_guard"  # the page's Run button: Holo-3.1 alone vs Holo-3.1 + Feci Guard

    key = None

    def given_key(self):
        q = {k: v[0] for k, v in parse_qs(urlparse(self.path).query).items()}
        cookies = dict(c.strip().split("=", 1) for c in (self.headers.get("Cookie") or "").split(";") if "=" in c)
        return q.get("k") or cookies.get("duel_key") or ""

    def authorized(self):
        return bool(self.key) and hmac.compare_digest(self.given_key().encode(), self.key.encode())

    def same_origin(self):
        """A POST must come from this page: a page on another site can POST text/plain here (CSRF)."""
        origin = self.headers.get("Origin")
        return origin is None or urlparse(origin).netloc == self.headers.get("Host")

    def log_message(self, fmt, *a):
        pass

    def send(self, code, body, ctype="application/json"):
        data = body if isinstance(body, bytes) else (json.dumps(body, ensure_ascii=False) if ctype == "application/json" else body).encode()
        self.send_response(code); self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(len(data))); self.send_header("Cache-Control", "no-store")
        self.end_headers(); self.wfile.write(data)

    def do_GET(self):
        u = urlparse(self.path); q = {k: v[0] for k, v in parse_qs(u.query).items()}
        root = self.duels.root
        if u.path in ("/try", "/try/"):
            return self.send(200, (HERE / "try.html").read_bytes(), "text/html; charset=utf-8")
        if u.path == "/api/try/cases":  # no label, no score: the official verdict is revealed after the check
            return self.send(200, [{"n": n, "domain": c["domain"], "instruction": c["instruction"]} for n, c in enumerate(self.tryer.cases)])
        m = re.fullmatch(r"/try/img/([0-5])\.jpg", u.path)
        if m:
            return self.send(200, self.tryer.image(int(m.group(1))), "image/jpeg")
        if u.path in ("/", "/index.html"):
            if "k" in q:  # key given in the URL: store it as a cookie and drop it from the address bar (screen sharing)
                rest = "&".join(f"{k}={v}" for k, v in q.items() if k != "k")
                self.send_response(302)
                if self.authorized():
                    self.send_header("Set-Cookie", f"duel_key={q['k']}; Path=/; HttpOnly; Secure; SameSite=Strict; Max-Age=604800")
                self.send_header("Location", "/" + ("?" + rest if rest else "")); self.send_header("Content-Length", "0")
                return self.end_headers()
            return self.send(200, (HERE / "index.html").read_bytes(), "text/html; charset=utf-8")
        if u.path == "/api/config":
            return self.send(200, {"tasks": [{"id": t, "instruction": json.loads((EXAMPLES / f"{t}.json").read_text())["instruction"]} for t in TASKS],
                                   "presets": {k: {s: v.split("=")[1] for s, v in p.items()} for k, p in PRESETS.items()},
                                   "default_preset": self.duels.preset, "guard_preset": self.guard_preset, "guard_available": guard_available(), "labels": LABELS, "running": self.duels.running(),
                                   "control": self.authorized()})
        if u.path == "/api/duels":
            return self.send(200, self.duels.listing())
        if u.path == "/api/events":
            d = root / q.get("duel", "")
            if not DUEL_ID.fullmatch(q.get("duel", "")) or not (d / "meta.json").exists():
                return self.send(404, {"error": "no such duel"})
            out = {"meta": json.loads((d / "meta.json").read_text()), "running": d.name in self.duels.running()}
            for side in ("left", "right"):
                out[side], out[side + "_n"] = read_events(d / side / "events.jsonl", int(q.get(side, 0)))
            return self.send(200, out)
        if u.path.startswith("/duels/"):
            parts = u.path.split("/")[2:]
            if len(parts) == 4 and DUEL_ID.fullmatch(parts[0]) and parts[1] in ("left", "right") and parts[2] == "frames" and re.fullmatch(r"[\w.-]+\.jpg", parts[3]):
                f = root / Path(parts[0]).name / parts[1] / "frames" / parts[3]
                if f.exists():
                    return self.send(200, f.read_bytes(), "image/jpeg")
            return self.send(404, {"error": "not found"})
        return self.send(404, {"error": "not found"})

    def do_POST(self):
        if urlparse(self.path).path == "/api/try/verify":  # public, rate-limited
            if not self.same_origin():
                return self.send(403, {"error": "same origin only"})
            body = json.loads(self.rfile.read(int(self.headers.get("Content-Length") or 0)) or b"{}")
            n = body.get("n")
            if not isinstance(n, int) or not 0 <= n < len(self.tryer.cases):
                return self.send(400, {"error": "bad case"})
            return self.send(*self.tryer.verify(n))
        if not (self.authorized() and self.same_origin()):
            return self.send(403, {"error": "control needs the duel key"})
        u = urlparse(self.path)
        body = json.loads(self.rfile.read(int(self.headers.get("Content-Length") or 0)) or b"{}")
        try:
            if u.path == "/api/start" and body.get("dry_run"):  # auth test: validates the request, starts nothing
                if body.get("preset", self.duels.preset) not in PRESETS or body.get("task") not in TASKS + [None]:
                    raise ValueError("bad preset or task")
                return self.send(200, {"dry_run": True, "authorized": True, "running": self.duels.running()})
            if u.path == "/api/start":
                return self.send(200, {"id": self.duels.start(body["task"], body.get("preset"), int(body.get("max_steps", 50)), body.get("guard", "none"))})
            if u.path == "/api/stop":
                ids = [body["duel"]] if body.get("duel") else self.duels.running()
                sides = ["left", "right"] if body.get("side", "all") == "all" else [body["side"]]
                for i in ids:
                    if not DUEL_ID.fullmatch(i):
                        raise ValueError(f"bad duel id {i}")
                    self.duels.stop(i, sides)
                return self.send(200, {"stopped": ids, "sides": sides})
        except (RuntimeError, ValueError, KeyError) as e:
            return self.send(409, {"error": str(e)})
        return self.send(404, {"error": "not found"})


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--port", type=int, default=8765)
    ap.add_argument("--root", default=str(Path.home() / "osw/duels"))
    ap.add_argument("--preset", choices=sorted(PRESETS), default="pod")
    ap.add_argument("--guard_preset", choices=sorted(PRESETS), default="modal_guard")
    args = ap.parse_args()
    Handler.duels = Duels(args.root, args.preset)
    Handler.guard_preset = args.guard_preset
    Handler.tryer = Try()
    key_file = Path.home() / ".duel_key"
    Handler.key = key_file.read_text().strip() if key_file.exists() else None  # no key file: nobody can start or stop
    print(f"duel page: http://127.0.0.1:{args.port}/  (preset {args.preset}, duels in {args.root})", flush=True)
    ThreadingHTTPServer(("127.0.0.1", args.port), Handler).serve_forever()


if __name__ == "__main__":
    main()
