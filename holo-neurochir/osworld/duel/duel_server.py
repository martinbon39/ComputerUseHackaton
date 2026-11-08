"""Live duel page server (orbit): two OSWorld VMs side by side, original Holo-3.1-4B vs the merged model, same task,
at the same time; per-side STOP and global STOP; every duel recorded (events.jsonl + frames) and replayable.
Each side is a duel_side.py process started through ~/osw/osh (docker + kvm), with run_osw.sh's exact environment.
Usage: devcap python duel_server.py [--port 8765] [--root ~/osw/duels] [--preset pod|modal]
  page:   http://127.0.0.1:8765/            replay: http://127.0.0.1:8765/?replay=<duel_id>
Bound to 127.0.0.1 only: the page starts and stops VMs.
"""
import argparse, json, os, re, signal, subprocess, threading, time
from http.server import ThreadingHTTPServer, BaseHTTPRequestHandler
from pathlib import Path
from urllib.parse import urlparse, parse_qs

HERE = Path(__file__).resolve().parent
TASKS = [  # original made a false 'done' and the merged model succeeded, in recorded runs
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


class Handler(BaseHTTPRequestHandler):
    duels: Duels = None

    def local_origin(self):
        """Reject cross-site requests (CSRF, DNS rebinding): a page on another site can POST text/plain here."""
        ok = {f"127.0.0.1:{self.server.server_port}", f"localhost:{self.server.server_port}"}
        origin = self.headers.get("Origin")
        return self.headers.get("Host") in ok and (origin is None or urlparse(origin).netloc in ok)

    def log_message(self, fmt, *a):
        pass

    def send(self, code, body, ctype="application/json"):
        data = body if isinstance(body, bytes) else (json.dumps(body, ensure_ascii=False) if ctype == "application/json" else body).encode()
        self.send_response(code); self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(len(data))); self.send_header("Cache-Control", "no-store")
        self.end_headers(); self.wfile.write(data)

    def do_GET(self):
        if not self.local_origin():
            return self.send(403, {"error": "local origin only"})
        u = urlparse(self.path); q = {k: v[0] for k, v in parse_qs(u.query).items()}
        root = self.duels.root
        if u.path in ("/", "/index.html"):
            return self.send(200, (HERE / "index.html").read_bytes(), "text/html; charset=utf-8")
        if u.path == "/api/config":
            return self.send(200, {"tasks": [{"id": t, "instruction": json.loads((EXAMPLES / f"{t}.json").read_text())["instruction"]} for t in TASKS],
                                   "presets": {k: {s: v.split("=")[1] for s, v in p.items()} for k, p in PRESETS.items()},
                                   "default_preset": self.duels.preset, "guard_available": guard_available(), "labels": LABELS, "running": self.duels.running()})
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
        if not self.local_origin():
            return self.send(403, {"error": "local origin only"})
        u = urlparse(self.path)
        body = json.loads(self.rfile.read(int(self.headers.get("Content-Length") or 0)) or b"{}")
        try:
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
    args = ap.parse_args()
    Handler.duels = Duels(args.root, args.preset)
    print(f"duel page: http://127.0.0.1:{args.port}/  (preset {args.preset}, duels in {args.root})", flush=True)
    ThreadingHTTPServer(("127.0.0.1", args.port), Handler).serve_forever()


if __name__ == "__main__":
    main()
