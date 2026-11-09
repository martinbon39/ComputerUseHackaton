"""Runner of the guard attribution study (report/PREREG_GUARD_ATTRIBUTION.md). Dry run by default.

  python3 runner.py plan     [--tasks split_test.json] [--seeds 0,1,2] [--workers N]     print the schedule, no side effect
  python3 runner.py run      --results DIR --base-urls URL[,URL...] --served-model NAME --go [--workers N] [--shard i/n]
  python3 runner.py run      --pilot --go --results DIR --base-urls ...  one real task, 3 arms, seed 99, before seed 0
  python3 runner.py run      --mock --results DIR [--max-tasks 1]        mock model + fake VM, no GPU, no VM, no cost
  python3 runner.py status   --results DIR                               dead / rerun / drop / stop rule from the ledger
  python3 runner.py preflight --base-urls URL --served-model NAME [--probe]   pins and endpoint checks

Schedule: for each seed in order, every task of the split, the three arms back to back, arm order rotated by task
(ABC, BCA, CAB, ...) so that time and server-load drifts hit all arms alike. Workers (one VM each) pull from that
queue in order. After a seed's pass, each infra-dead episode (no result.txt: 0 steps or crash before scoring) is moved
aside and rerun once with the same seed; if still dead, the task is dropped from all three arms for that seed.
After seed 0, if more than 10 % of its first attempts are infra-dead, the run stops (exit 3) before seed 1.
Every attempt is a line of <results>/ledger.jsonl; <results>/cost.json is rewritten after each seed.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import multiprocessing as mp
import os
import shutil
import sys
import time
import urllib.request

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
NEURO = os.path.dirname(HERE)
PINS = json.load(open(os.path.join(HERE, "pins.json")))
DEFAULT_TASKS = os.path.join(NEURO, "osworld", "split_test.json")
DEFAULT_RTG = os.path.expanduser("~/osw/rtg")
REPO = os.path.dirname(NEURO)
PILOT_SEED = 99
STOP_DEAD_RATE = 0.10
EXIT_STOP = 3


def load_tasks(path: str, max_tasks: int = 0) -> list[tuple[str, str]]:
    meta = json.load(open(path))
    tasks = [(d, t) for d in meta for t in meta[d]]
    return tasks[:max_tasks] if max_tasks else tasks


def rotation(i: int) -> tuple[str, ...]:
    arms = ("A", "B", "C")
    r = i % 3
    return arms[r:] + arms[:r]


def schedule(tasks, seeds) -> list[dict]:
    return [{"seed": s, "domain": d, "task": t, "arm": a, "task_index": i}
            for s in seeds for i, (d, t) in enumerate(tasks) for a in rotation(i)]


def shard(tasks, spec: str | None):
    if not spec:
        return tasks
    i, n = (int(x) for x in spec.split("/"))
    return tasks[i::n]


# ---------------------------------------------------------------- ledger / status

def ledger_path(root: str) -> str:
    return os.path.join(root, "ledger.jsonl")


def read_ledger(root: str) -> list[dict]:
    p = ledger_path(root)
    return [json.loads(x) for x in open(p)] if os.path.exists(p) else []


def append_ledger(root: str, rec: dict) -> None:
    with open(ledger_path(root), "a") as f:
        f.write(json.dumps(rec) + "\n")


def status(root: str, seeds=(0, 1, 2), n_tasks: int | None = None) -> dict:
    """Per seed: first-attempt dead rate, reruns, drops; the 10 % stop rule on seed 0."""
    led = [r for r in read_ledger(root) if r.get("kind", "attempt") == "attempt"]
    out = {}
    for s in seeds:
        rs = [r for r in led if r["seed"] == s]
        first = {(r["arm"], r["task"]): r for r in rs if r["attempt"] == 1}
        last = {}
        for r in sorted(rs, key=lambda r: r["attempt"]):
            last[(r["arm"], r["task"])] = r
        dead_first = sorted(k for k, r in first.items() if r["dead"])
        dead_final = sorted(k for k, r in last.items() if r["dead"])
        dropped = sorted({t for _, t in dead_final})
        expected = 3 * n_tasks if n_tasks else len(first)
        out[s] = {"episodes_first_attempt": len(first), "expected": expected,
                  "dead_first_attempt": len(dead_first), "dead_rate_first_attempt": len(dead_first) / max(expected, 1),
                  "reruns": sum(1 for r in rs if r["attempt"] > 1), "dead_after_rerun": dead_final,
                  "dropped_tasks": dropped}
    s0 = out.get(0)
    out["stop_rule"] = {"applies_after": "seed 0 of all three arms", "threshold": STOP_DEAD_RATE,
                        "seed0_complete": bool(s0 and s0["episodes_first_attempt"] >= s0["expected"] > 0),
                        "stop": bool(s0 and s0["dead_rate_first_attempt"] > STOP_DEAD_RATE)}
    return out


def cost_summary(root: str, n_gpus: int, gpu_hour_usd: float | None, t_start: float) -> dict:
    led = [r for r in read_ledger(root) if r.get("kind", "attempt") == "attempt"]
    calls = sum(r["verifier_calls"] for r in led if r["arm"] == "C")
    known = [r["verifier_cost_usd"] for r in led if r["arm"] == "C" and r["verifier_cost_usd"] is not None]
    wall_h = (time.time() - t_start) / 3600
    est_claude = calls * PINS["cost"]["claude_usd_per_call_estimate"]
    return {"attempts": len(led), "episode_wall_h_sum": round(sum(r["wall_s"] for r in led) / 3600, 2),
            "run_wall_h": round(wall_h, 2), "gpus": n_gpus, "gpu_hours": round(wall_h * n_gpus, 2),
            "gpu_usd": round(wall_h * n_gpus * gpu_hour_usd, 2) if gpu_hour_usd else None,
            "claude_calls_C": calls, "claude_usd_recorded": round(sum(known), 4) if known else None,
            "claude_usd_estimate": round(est_claude, 2), "model_requests": sum(r["model_requests"] for r in led)}


# ---------------------------------------------------------------- execution

def _worker(wid, items_q, results_q, cfg):
    import arms
    if cfg["mock"]:
        import mock
        env = mock.FakeDesktopEnv()
    mods = arms.load(cfg["rtg"], no_sleep=cfg["mock"])
    from openai import OpenAI
    clients = {u: OpenAI(base_url=u, api_key=os.environ.get(cfg["api_key_env"], "EMPTY"),
                         **({"max_retries": 0} if cfg["mock"] else {})) for u in cfg["base_urls"]}
    if not cfg["mock"]:
        os.chdir(os.path.join(cfg["rtg"], "Env", "OSWorld"))
        for k, v in PINS["harness"]["env"].items():
            os.environ.setdefault(k, v)
        env = mods.run_holo._make_env(mods.run_holo.parse_args(
            ["--screen_width", "1920", "--screen_height", "1080"]))
    sleep = (lambda s: None) if cfg["mock"] else time.sleep
    try:
        while True:
            it = items_q.get()
            if it is None:
                break
            results_q.put(("start", wid, it, time.time()))
            rec = arms.run_episode(mods, it["arm"], it["seed"], it["domain"], it["task"], env,
                                   clients[it["base_url"]], cfg["results"], cfg["episode"],
                                   attempt=it.get("attempt", 1), sleep=sleep)
            rec.update(worker=wid, base_url=it["base_url"], kind="attempt")
            results_q.put(("done", wid, rec, time.time()))
    finally:
        try:
            env.close()
        except Exception:  # noqa: BLE001
            pass


def _dead_record(it, error):
    return {**{k: it[k] for k in ("arm", "seed", "domain", "task")}, "attempt": it.get("attempt", 1), "score": None,
            "dead": True, "error": error, "wall_s": 0.0, "model_requests": 0, "model_request_failures": 0,
            "verifier_calls": 0, "verifier_cost_usd": None, "verifier_errors": 0, "guard_decisions": [],
            "base_url": it.get("base_url"), "kind": "attempt"}


def _pass(items, cfg) -> list[dict]:
    """Run items on cfg['workers'] workers (one VM each). An episode running longer than cfg['episode_timeout_s'], or
    whose worker dies, is recorded as infra-dead and its worker is replaced. Records are appended to the ledger."""
    if not items:
        return []
    for it in items:
        it["base_url"] = cfg["base_urls"][it["task_index"] % len(cfg["base_urls"])]
    ctx = mp.get_context("spawn")
    iq, rq = ctx.Queue(), ctx.Queue()
    for it in items:
        iq.put(it)
    n = min(cfg["workers"], len(items))
    procs, running, out, idle_exits = {}, {}, [], {}

    def spawn(w):
        procs[w] = ctx.Process(target=_worker, args=(w, iq, rq, cfg))
        procs[w].start()

    def record(rec):
        append_ledger(cfg["results"], rec)
        out.append(rec)
        print(f"[{len(out)}/{len(items)}] seed{rec['seed']} arm{rec['arm']} {rec['domain']}/{rec['task'][:8]} "
              f"score={rec['score']} dead={rec['dead']} {rec['wall_s']}s {rec.get('error') or ''}", flush=True)

    for w in range(n):
        spawn(w)
        if not cfg["mock"] and w < n - 1:
            time.sleep(8)
    while len(out) < len(items):
        try:
            kind, w, payload, t = rq.get(timeout=5)
            if kind == "start":
                running[w] = (payload, t)
                idle_exits[w] = 0
            else:
                running.pop(w, None)
                record(payload)
            continue
        except Exception:  # noqa: BLE001
            pass
        for w, p in list(procs.items()):
            job = running.get(w)
            timed_out = job and time.time() - job[1] > cfg["episode_timeout_s"]
            if timed_out or not p.is_alive():
                if p.is_alive():
                    p.terminate()
                    p.join(10)
                if job:
                    running.pop(w)
                    record(_dead_record(job[0], "episode timeout" if timed_out else f"worker exit {p.exitcode}"))
                else:
                    idle_exits[w] = idle_exits.get(w, 0) + 1
                if len(out) + len(running) < len(items) and idle_exits.get(w, 0) < 3:
                    spawn(w)
                else:
                    procs.pop(w)
        if not procs:
            break
    seen = {(r["arm"], r["seed"], r["task"], r["attempt"]) for r in out}
    for it in items:
        if (it["arm"], it["seed"], it["task"], it.get("attempt", 1)) not in seen:
            record(_dead_record(it, "no worker could start (VM or harness failure)"))
    for _ in procs:
        iq.put(None)
    for p in procs.values():
        p.join(60)
        if p.is_alive():
            p.terminate()
    return out


def _move_aside(root, rec, served_model):
    import arms
    ep = arms.episode_dir(root, rec["arm"], rec["seed"], served_model, rec["domain"], rec["task"])
    if os.path.isdir(ep):
        dst = f"{ep}.dead{rec['attempt']}"
        shutil.move(ep, dst)


def run(a) -> int:
    tasks_all = load_tasks(a.tasks, a.max_tasks)
    tasks = shard(tasks_all, a.shard)
    seeds = [int(s) for s in a.seeds.split(",")]
    if a.shard and len(seeds) != 1:
        print("REFUSED: a sharded job runs exactly one seed (the 10 % stop rule is checked between seeds).")
        return 2
    results = os.path.abspath(a.results)
    if a.pilot:
        tasks, seeds, results = tasks_all[:1], [PILOT_SEED], os.path.join(results, "pilot")
    os.makedirs(results, exist_ok=True)
    cfg = {"mock": a.mock, "rtg": a.rtg, "results": results, "workers": a.workers,
           "episode_timeout_s": a.episode_timeout_min * 60,
           "api_key_env": a.api_key_env, "base_urls": a.base_urls.split(",") if a.base_urls else [],
           "episode": {"served_model": a.served_model, "max_steps": PINS["harness"]["max_steps"],
                       "test_meta": os.path.abspath(a.tasks), "examples_dir": os.path.abspath(a.examples_dir),
                       "guard_model": a.guard_model, "sleep_after_reset": 0 if a.mock else 60, "pause": 0 if a.mock else 1.0,
                       "no_report": a.mock}}
    server = None
    if a.mock:
        import mock
        server = mock.MockServer(served_model=a.served_model, verifier_model=a.guard_model,
                                 log_path=os.path.join(cfg["results"], "mock_requests.jsonl"),
                                 fail_substring=a.mock_fail_task, hang_substring=a.mock_hang_task).start()
        cfg["base_urls"] = [server.base_url]
        os.environ.update(GUARD_BACKEND="openai", GUARD_BASE_URL=server.base_url, GUARD_API_KEY_ENV="")
        _write_mock_examples(tasks, cfg["episode"]["examples_dir"])
    elif not a.go:
        print("DRY RUN: this would start real episodes (GPU, VMs, Claude calls). Re-run with --go. Plan:")
        print(json.dumps(plan_summary(tasks, seeds, a.workers), indent=1))
        return 0
    else:
        if not a.pilot and (a.max_tasks or (a.tasks != DEFAULT_TASKS and not a.allow_other_tasks)):
            print("REFUSED: the preregistration runs all 120 TEST tasks or none (no sub-sample).")
            return 2
        missing = preflight_errors(a)
        if missing:
            print("REFUSED, preflight failed:\n  " + "\n  ".join(missing))
            return 2
    append_ledger(cfg["results"], {"kind": "pilot" if a.pilot else "start", "t": time.time(), "argv": sys.argv,
                                   "pins": PINS, "code": code_state(), "shard": a.shard, "seeds": seeds,
                                   "n_tasks": len(tasks)})
    t0, code = time.time(), 0
    index = {t: i for i, (_, t) in enumerate(tasks)}
    try:
        for s in seeds:
            tried = {(r["arm"], r["task"]) for r in read_ledger(cfg["results"])
                     if r.get("kind") == "attempt" and r["seed"] == s}
            items = [it for it in schedule(tasks, [s]) if (it["arm"], it["task"]) not in tried]
            _pass(items, cfg)
            led = [r for r in read_ledger(cfg["results"]) if r.get("kind") == "attempt" and r["seed"] == s]
            attempts = {}
            for r in led:
                attempts.setdefault((r["arm"], r["task"]), []).append(r)
            rerun = []
            for (arm, task), rs in attempts.items():
                last = max(rs, key=lambda r: r["attempt"])
                if last["dead"] and last["attempt"] == 1:
                    _move_aside(cfg["results"], last, a.served_model)
                    rerun.append({"seed": s, "domain": last["domain"], "task": task, "arm": arm, "attempt": 2,
                                  "task_index": index[task]})
            _pass(rerun, cfg)
            st = status(cfg["results"], seeds=[s], n_tasks=len(tasks))
            json.dump(cost_summary(cfg["results"], a.n_gpus, a.gpu_hour_usd, t0),
                      open(os.path.join(cfg["results"], "cost.json"), "w"), indent=1)
            print(json.dumps({"seed": s, **st[s]}, indent=1))
            if s == 0 and not a.shard and not a.pilot and st[0]["dead_rate_first_attempt"] > STOP_DEAD_RATE:
                append_ledger(cfg["results"], {"kind": "stop", "seed": 0, "t": time.time(), **st[0]})
                print(f"HARD STOP: {st[0]['dead_first_attempt']} infra-dead first attempts in seed 0 "
                      f"(> {STOP_DEAD_RATE:.0%}). Fix the infrastructure before seed 1.")
                code = EXIT_STOP
                break
            if s == 0 and a.shard:
                print("Sharded run: the 10 % stop rule is applied by `runner.py status` on the collected seed-0 results.")
    finally:
        if server:
            server.stop()
    return code


def _write_mock_examples(tasks, examples_dir):
    for d, t in tasks:
        os.makedirs(os.path.join(examples_dir, d), exist_ok=True)
        p = os.path.join(examples_dir, d, f"{t}.json")
        if not os.path.exists(p):
            json.dump({"id": t, "instruction": f"Mock instruction for {d}/{t}.", "evaluator": {"func": "mock"}},
                      open(p, "w"))


def plan_summary(tasks, seeds, workers) -> dict:
    sch = schedule(tasks, seeds)
    ep_min = PINS["cost"]["episode_minutes_estimate"]
    return {"episodes": len(sch), "tasks": len(tasks), "seeds": seeds, "first_items": [
        f"seed{x['seed']} arm{x['arm']} {x['domain']}/{x['task'][:8]}" for x in sch[:9]],
        "workers": workers, "episode_minutes_estimate": ep_min,
        "wall_hours_estimate": round(len(sch) * ep_min / 60 / max(workers, 1), 1),
        "claude_calls_estimate_C": PINS["cost"]["claude_calls_per_seed_estimate"] * len(seeds),
        "claude_usd_estimate": round(PINS["cost"]["claude_calls_per_seed_estimate"] * len(seeds)
                                     * PINS["cost"]["claude_usd_per_call_estimate"], 2)}


# ---------------------------------------------------------------- preflight

def _get(url, key=None, timeout=10):
    req = urllib.request.Request(url, headers={"Authorization": f"Bearer {key}"} if key else {})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return json.loads(r.read())


def _sha(path):
    return hashlib.sha256(open(path, "rb").read()).hexdigest() if os.path.exists(path) else None


def code_state() -> dict:
    """Repo HEAD, and whether this folder or the frozen files differ from it (recorded in the ledger)."""
    paths = ["holo-neurochir/guard_attribution"] + list(PINS["frozen_files"]["repo"])
    dirty = os.popen(f"git -C {REPO} status --porcelain -- " + " ".join(paths) + " 2>/dev/null").read().split("\n")
    dirty = [x for x in dirty if x.strip() and "__pycache__" not in x]
    return {"repo_head": os.popen(f"git -C {REPO} rev-parse HEAD 2>/dev/null").read().strip(), "uncommitted": dirty}


def frozen_errors(rtg: str) -> list[str]:
    errs = []
    for rel, want in PINS["frozen_files"]["repo"].items():
        if _sha(os.path.join(REPO, rel)) != want:
            errs.append(f"frozen file changed: {rel}")
    for rel, want in PINS["frozen_files"]["rtg"].items():
        if _sha(os.path.join(rtg, rel)) != want:
            errs.append(f"frozen file changed: <rtg>/{rel}")
    return errs


def preflight_errors(a) -> list[str]:
    errs = frozen_errors(a.rtg)
    cs = code_state()
    if cs["uncommitted"]:
        errs.append("uncommitted changes in the study code (commit before any episode): " + "; ".join(cs["uncommitted"]))
    import arms
    try:
        arms.load(a.rtg)
    except Exception as e:  # noqa: BLE001
        errs.append(f"harness: {e}")
    rtg_head = os.popen(f"git -C {a.rtg} rev-parse HEAD 2>/dev/null").read().strip()
    if rtg_head != PINS["harness"]["realtimegui_commit"]:
        errs.append(f"RealtimeGUI HEAD {rtg_head or 'unknown'} != {PINS['harness']['realtimegui_commit']}")
    if hashlib.sha256(open(a.tasks, "rb").read()).hexdigest() != PINS["tasks"]["split_test_sha256"]:
        errs.append("split_test.json sha256 differs from the pinned one")
    key = os.environ.get(a.api_key_env)
    for u in (a.base_urls or "").split(","):
        if not u:
            errs.append("no --base-urls")
            continue
        try:
            ids = [m["id"] for m in _get(u.rstrip("/") + "/models", key)["data"]]
            if a.served_model not in ids:
                errs.append(f"{u}: served models {ids} lack {a.served_model}")
        except Exception as e:  # noqa: BLE001
            errs.append(f"{u}: /models unreachable ({e})")
        try:
            v = _get(u.rstrip("/").removesuffix("/v1") + "/version", key).get("version")
            if v != PINS["vllm"]["version"]:
                errs.append(f"{u}: vLLM {v} != {PINS['vllm']['version']}")
        except Exception as e:  # noqa: BLE001
            errs.append(f"{u}: /version unreachable ({e})")
    gb = os.environ.get("GUARD_BASE_URL")
    if os.environ.get("GUARD_BACKEND") not in (None, "", "openai"):
        errs.append(f"GUARD_BACKEND={os.environ.get('GUARD_BACKEND')}: arm C must use the relay (openai backend), as before")
    if not gb:
        errs.append("GUARD_BASE_URL unset (arm C needs the verifier relay, e.g. http://127.0.0.1:9911/v1)")
    else:
        try:
            ids = [m["id"] for m in _get(gb.rstrip("/") + "/models")["data"]]
            if a.guard_model not in ids:
                errs.append(f"verifier relay serves {ids}, not {a.guard_model}")
        except Exception as e:  # noqa: BLE001
            errs.append(f"verifier relay {gb}/models unreachable ({e}): arm C would fail open and become arm B")
    if shutil.which("nvidia-smi"):
        names = os.popen("nvidia-smi --query-gpu=name --format=csv,noheader").read().split("\n")
        names = [n.strip() for n in names if n.strip()]
        if not names or any("H100" not in n for n in names):
            errs.append(f"GPUs {names}: the prereg requires H100 (same GPU type as before)")
    if a.probe and not errs:
        errs += determinism_probe(a.base_urls.split(","), a.served_model, key)
    return errs


def determinism_probe(base_urls, model, key) -> list[str]:
    """Same seed twice on every endpoint must give the same text; a different seed should usually differ."""
    from openai import OpenAI
    errs, outs = [], {}
    msgs = [{"role": "user", "content": "Write one random sentence about a desktop computer."}]
    for u in base_urls:
        c = OpenAI(base_url=u, api_key=key or "EMPTY")
        get = lambda s: c.chat.completions.create(model=model, messages=msgs, temperature=0.8, top_p=0.9,  # noqa: E731
                                                  max_tokens=64, seed=s).choices[0].message.content
        a1, a2, b = get(12345), get(12345), get(54321)
        outs[u] = a1
        if a1 != a2:
            errs.append(f"{u}: same seed gave different outputs")
        if a1 == b:
            print(f"note: {u}: two different seeds gave the same output (possible, check)")
    if len(set(outs.values())) > 1:
        errs.append("endpoints disagree for the same seed (different GPU/args/version?)")
    return errs


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("cmd", choices=["plan", "run", "status", "preflight"])
    ap.add_argument("--tasks", default=DEFAULT_TASKS)
    ap.add_argument("--examples-dir", default=os.path.join(DEFAULT_RTG, "Env", "OSWorld", "evaluation_examples", "examples"))
    ap.add_argument("--seeds", default="0,1,2")
    ap.add_argument("--results", default=None)
    ap.add_argument("--rtg", default=DEFAULT_RTG)
    ap.add_argument("--base-urls", default=None, help="comma-separated vLLM /v1 endpoints, one per GPU")
    ap.add_argument("--api-key-env", default="HOLO_VLLM_KEY", help="NAME of the env var holding the vLLM key")
    ap.add_argument("--served-model", default=PINS["model"]["study_served_model_name"])
    ap.add_argument("--guard-model", default=PINS["verifier"]["guard_model"])
    ap.add_argument("--workers", type=int, default=1)
    ap.add_argument("--shard", default=None, help="i/n: this job runs tasks[i::n] (GitHub-runner mode)")
    ap.add_argument("--n-gpus", type=int, default=8)
    ap.add_argument("--gpu-hour-usd", type=float, default=None)
    ap.add_argument("--max-tasks", type=int, default=0, help="mock only")
    ap.add_argument("--episode-timeout-min", type=float, default=45.0,
                    help="an episode running longer is killed and recorded as infra-dead")
    ap.add_argument("--pilot", action="store_true",
                    help=f"one real task, 3 arms, seed {PILOT_SEED} (not a study seed), into <results>/pilot")
    ap.add_argument("--allow-other-tasks", action="store_true", help=argparse.SUPPRESS)
    ap.add_argument("--mock", action="store_true")
    ap.add_argument("--mock-fail-task", default=None, help=argparse.SUPPRESS)
    ap.add_argument("--mock-hang-task", default=None, help=argparse.SUPPRESS)
    ap.add_argument("--probe", action="store_true", help="preflight: send 3 short seeded requests per endpoint")
    ap.add_argument("--go", action="store_true", help="really run (GPU, VMs, Claude calls)")
    a = ap.parse_args(argv)
    if a.cmd == "plan":
        print(json.dumps(plan_summary(shard(load_tasks(a.tasks, a.max_tasks), a.shard),
                                      [int(s) for s in a.seeds.split(",")], a.workers), indent=1))
        return 0
    if a.cmd == "status":
        starts = [r for r in read_ledger(a.results) if r.get("kind") == "start" and not r.get("shard")]
        n = starts[-1]["n_tasks"] if starts else len(load_tasks(a.tasks))
        st = status(a.results, n_tasks=n)
        print(json.dumps(st, indent=1))
        return EXIT_STOP if st["stop_rule"]["stop"] else 0
    if a.cmd == "preflight":
        errs = preflight_errors(a)
        print("PREFLIGHT OK" if not errs else "PREFLIGHT FAILED:\n  " + "\n  ".join(errs))
        return 0 if not errs else 2
    if not a.results:
        ap.error("--results is required")
    if a.mock:
        a.examples_dir = os.path.join(os.path.abspath(a.results), "mock_examples")
    return run(a)


if __name__ == "__main__":
    sys.exit(main())
