"""One side of a live duel: one OSWorld VM, one model, the exact run_holo harness (v2 prompt, T=0.8, top_p 0.9,
image budget 3, 60 s settle, answer -> DONE/FAIL, 20 s settle, official evaluator).
Everything the page shows is appended to <out>/events.jsonl (one JSON object per line, field t = unix time):
  phase    {phase: booting|settling|thinking|acting|evaluating|done|stopped|error, ...}
  frame    {file}             live VM screenshot (every --live_every s, JPEG 960x540, from the VM's own HTTP server)
  step     {i, note, thought, action, tool, file}   one agent step (file = the observation the model saw)
  verdict  {score, claimed_done, answer, declined, steps}
Feci Guard (--guard): the agent is feci_guard/run_holo_guard.GuardedAgent (its exact policy: a non-infeasible
answer is checked by the external verifier on a screenshot; INCOMPLETE -> refused, the feedback is the answer's tool
output and the episode goes on; at most 2 refusals). Extra events: phase guard_checking, guard {decision, verdict,
requirements [{text, mark, evidence}], feedback, latency_s, error, file}.
Stop: create <out>/STOP (the episode ends at the next step boundary, no evaluation), or SIGTERM (immediate). The VM
is closed in every case. Run through ~/osw/osh (docker + kvm), from the OSWorld root (duel_server.py does it).
Usage: python duel_side.py --task domain/example_id --server URL=NAME[=ENVVAR] --out DIR [--max_steps 50]
"""
import argparse, json, logging, os, signal, sys, threading, time
from io import BytesIO
from pathlib import Path

HOLO_REPRO = os.path.expanduser("~/osw/rtg/Env/OSWorld/holo_repro")
sys.path.insert(0, HOLO_REPRO); sys.path.insert(0, os.path.dirname(HOLO_REPRO))
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from PIL import Image  # noqa: E402
import run_holo as RH  # noqa: E402
from holo_agent import SYSTEM_PROMPTS, HoloComputerAgent  # noqa: E402
from osworld_computer_env import OSWorldComputerEnv  # noqa: E402
from probe_answer_rate import client_for  # noqa: E402
from desktop_env.providers.docker.provider import DockerProvider  # noqa: E402

log = logging.getLogger("duel")


class Events:
    def __init__(self, out):
        self.out, self.lock, self.n_frames = Path(out), threading.Lock(), 0
        (self.out / "frames").mkdir(parents=True, exist_ok=True)

    def emit(self, kind, **kw):
        with self.lock, open(self.out / "events.jsonl", "a") as f:
            f.write(json.dumps({"t": round(time.time(), 3), "kind": kind, **kw}, ensure_ascii=False, default=str) + "\n")

    def save(self, image, prefix):
        with self.lock:
            self.n_frames += 1
            name = f"frames/{prefix}_{self.n_frames:05d}.jpg"
        image.convert("RGB").resize((960, 540)).save(self.out / name, quality=80)
        return name


class StopFile(Exception):
    pass


class DuelEnv(OSWorldComputerEnv):
    stop_path = None
    def is_done(self):
        return super().is_done() or (self.stop_path is not None and self.stop_path.exists())


def agent_class(guard):
    base = HoloComputerAgent
    if guard:
        sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "feci_guard"))
        import run_holo_guard
        base = run_holo_guard.GuardedAgent

    class DuelAgent(base):
        events, pending_guard = None, None

        def _call_model(self, messages):
            self.events.emit("phase", phase="thinking")
            out = super()._call_model(messages)
            self.events.emit("phase", phase="acting")
            return out

        def _check(self, step_idx, answer):  # GuardedAgent only
            self.events.emit("phase", phase="guard_checking", answer=answer)
            rec = super()._check(step_idx, answer)
            v = rec.get("verifier") or {}  # the verifier's detail; the record's own fields come from GuardedAgent
            shot = Path(self.guard_dir) / rec["screenshot"] if rec.get("screenshot") else None
            self.pending_guard = dict(
                decision=rec["decision"], verdict=v.get("verdict"), answer=answer, guard_kind=rec.get("kind"),
                requirements=[{"text": r.get("requirement") or r.get("text"),
                               "mark": {"yes": "✓", "no": "✗"}.get(r.get("status"), "?"),
                               "evidence": r.get("evidence")} for r in v.get("requirements") or []],
                feedback=rec.get("feedback", "") if rec["decision"] == "refused" else "",
                latency_s=v.get("latency_s"), error=v.get("error"), verifier_sha=v.get("verifier_sha"),
                file=self.events.save(Image.open(shot), "guard") if shot and shot.exists() else None)
            return rec

        def flush_guard(self):  # after the answer's step event, so the page lists the answer, then the check
            if self.pending_guard:
                self.events.emit("guard", **self.pending_guard); self.pending_guard = None
    return DuelAgent


def serialize_screenshots(env):
    """The VM's HTTP server returns broken PNGs to concurrent /screenshot calls (seen: both sides of the first duel
    crashed), so the live thread and the agent take turns."""
    lock, inner = threading.Lock(), env.controller.get_screenshot
    def get_screenshot(*a, **kw):
        with lock:
            return inner(*a, **kw)
    env.controller.get_screenshot = get_screenshot


def remove_container_on_interrupt(ev):
    """OSWorld cleans a half-started container only on Exception: a STOP (SystemExit) during the VM boot would leave
    it running. Remove it on any BaseException, and record each container id so the server can remove it too."""
    inner = DockerProvider.start_emulator
    def start_emulator(self, *a, **kw):
        try:
            inner(self, *a, **kw)
        except BaseException:
            if self.container is not None:
                self.container.remove(force=True); self.container = None
            raise
        ev.emit("phase", phase="vm_started", container=self.container.id)
    DockerProvider.start_emulator = start_emulator


def live_frames(env, ev, every, stop):
    while not stop.wait(every):
        try:
            raw = env.controller.get_screenshot()
            if raw:
                ev.emit("frame", file=ev.save(Image.open(BytesIO(raw)), "live"))
        except Exception as e:  # noqa: BLE001 - a missed live frame is harmless
            log.debug("live frame failed: %s", e)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--task", required=True)
    ap.add_argument("--server", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--max_steps", type=int, default=50)
    ap.add_argument("--live_every", type=float, default=2.0)
    ap.add_argument("--guard", action="store_true", help="Feci Guard on this side (feci_guard/run_holo_guard.GuardedAgent)")
    args = ap.parse_args()
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s %(message)s")
    out = Path(args.out); ev = Events(out)
    stop_path = out / "STOP"
    url, model, auth = (args.server.split("=", 2) + [None])[:3]
    domain, example_id = args.task.split("/")
    rh = RH.parse_args(["--max_steps", str(args.max_steps)])
    example = json.loads(open(os.path.join(rh.examples_dir, domain, f"{example_id}.json")).read())
    ev.emit("phase", phase="booting", pid=os.getpid(), model=model, task=args.task, instruction=example["instruction"], guard=args.guard)

    def on_term(signum, frame):
        signal.signal(signal.SIGTERM, signal.SIG_IGN)  # a second STOP must not interrupt the VM close
        raise SystemExit(143)
    signal.signal(signal.SIGTERM, on_term)

    env, live_stop = None, threading.Event()
    remove_container_on_interrupt(ev)
    try:
        env = RH._make_env(rh)
        env.reset(task_config=example)
        ev.emit("phase", phase="settling", container=getattr(env.provider.container, "id", None),
                vnc_port=getattr(env.provider, "vnc_port", None))
        serialize_screenshots(env)
        threading.Thread(target=live_frames, args=(env, ev, args.live_every, live_stop), daemon=True).start()
        time.sleep(rh.sleep_after_reset)
        if stop_path.exists():
            raise StopFile()
        cenv = DuelEnv(env, example["instruction"], pause=rh.pause); cenv.stop_path = stop_path

        def on_step(i, image, step, info, reasoning):
            tc = step.tool_call
            try:
                file = ev.save(image, f"step{i + 1:03d}")
            except OSError as e:  # an unreadable observation must not end the episode run_holo would continue
                log.warning("step frame not saved: %s", e); file = None
            ev.emit("step", i=i + 1, note=step.note, thought=step.thought, action=RH._fmt_action(tc),
                    tool=tc.tool_name, file=file)
            agent.flush_guard() if args.guard else None
        DuelAgent = agent_class(args.guard)
        DuelAgent.events = ev
        extra = {}
        if args.guard:
            import verifier
            (out / "guard").mkdir(exist_ok=True)
            extra = dict(guard_dir=str(out / "guard"), instruction=example["instruction"], guard_model=verifier.DEFAULT_MODEL,
                         guard_mode=os.environ.get("GUARD_MODE", "passive"))
        agent = DuelAgent(**extra, client=client_for(url, auth), model=model, env=cenv, max_steps=rh.max_steps,
                          temperature=rh.temperature, reasoning_effort=rh.reasoning_effort,
                          image_budget=rh.image_budget, on_step=on_step,
                          system_prompt_template=SYSTEM_PROMPTS[rh.prompt])
        summary = agent.run()
        if stop_path.exists():
            raise StopFile()
        if summary.get("steps", 0) == 0 and not summary.get("finished_by_agent"):
            raise RuntimeError("0 steps: VM or model endpoint not ready (run_holo leaves such an episode unscored)")
        answer = summary.get("answer")
        live_stop.set()  # run_one sends nothing else to the VM from here on
        declined = bool(answer is not None and RH._INFEASIBLE_RE.search(answer))
        ev.emit("phase", phase="evaluating", answer=answer)
        if answer is not None:
            env.step("FAIL" if declined else "DONE", rh.pause)
        time.sleep(20)
        score = float(env.evaluate())
        try:
            ev.emit("frame", file=ev.save(Image.open(BytesIO(env.controller.get_screenshot())), "final"))
        except Exception:  # noqa: BLE001
            pass
        ev.emit("verdict", guard=agent.guard_summary() if args.guard else None, score=score, claimed_done=answer is not None and not declined, answer=answer,
                declined=declined, steps=summary.get("steps"), finished_by_agent=summary.get("finished_by_agent"))
        ev.emit("phase", phase="done")
    except (StopFile, SystemExit, KeyboardInterrupt):
        ev.emit("phase", phase="stopped")
    except Exception as e:  # noqa: BLE001 - the page must show why the side ended
        log.exception("duel side failed"); ev.emit("phase", phase="error", error=repr(e)[:400])
    finally:
        live_stop.set()
        signal.signal(signal.SIGTERM, signal.SIG_IGN)
        if env is not None:
            try:
                env.close()
                ev.emit("phase", phase="vm_closed")
            except Exception as e:  # noqa: BLE001
                ev.emit("phase", phase="vm_close_failed", error=repr(e)[:200])


if __name__ == "__main__":
    main()
