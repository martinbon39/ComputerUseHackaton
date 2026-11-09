"""The three arms of PREREG_GUARD_ATTRIBUTION.md, each one episode at a time, on the frozen runner code.

A: holo_repro/run_holo.py run_one (RealtimeGUI HoloComputerAgent), no guard.
B: feci_guard/run_holo_guard.py run_one with --guard on, `feci` replaced by NeutralFeci (always COMPLETE, recorded delay).
C: feci_guard/run_holo_guard.py run_one with --guard on and the frozen verifier (sha 0af76fdbacc72317).

Nothing in those files is edited. load() imports both modules and swaps, in their module globals, the agent classes for
seeded subclasses (seeding.seeded); run_episode() sets the episode context and, for B and C, the `feci` object that
GuardedAgent._check calls.
"""
from __future__ import annotations

import json
import os
import sys
import time
import types

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

import neutral_verifier  # noqa: E402
import seeding  # noqa: E402

ARMS = ("A", "B", "C")
FROZEN_VERIFIER_SHA = "0af76fdbacc72317"
FECI_DIR = os.path.join(os.path.dirname(HERE), "feci_guard")


class Modules:
    def __init__(self, run_holo, run_holo_guard, real_feci):
        self.run_holo, self.run_holo_guard, self.real_feci = run_holo, run_holo_guard, real_feci


def load(rtg: str, no_sleep: bool = False) -> Modules:
    """Import run_holo (arm A) and run_holo_guard (arms B, C) and install the seeded agent classes."""
    holo_repro = os.path.join(rtg, "Env", "OSWorld", "holo_repro")
    expected = os.path.expanduser("~/osw/rtg/Env/OSWorld/holo_repro")
    if os.path.realpath(holo_repro) != os.path.realpath(expected):
        raise RuntimeError(f"run_holo_guard.py hard-codes {expected} (run_holo_guard.py:34); --rtg must resolve there")
    for p in (FECI_DIR, os.path.dirname(holo_repro), holo_repro):
        if p not in sys.path:
            sys.path.insert(0, p)
    import run_holo
    import run_holo_guard
    real_feci = run_holo_guard.feci
    if real_feci.VERIFIER_SHA != FROZEN_VERIFIER_SHA:
        raise RuntimeError(f"verifier sha {real_feci.VERIFIER_SHA} != frozen {FROZEN_VERIFIER_SHA}")
    if not getattr(run_holo.HoloComputerAgent, "_guard_attribution_seeded", False):
        run_holo.HoloComputerAgent = seeding.seeded(run_holo.HoloComputerAgent)
        run_holo_guard.HoloComputerAgent = seeding.seeded(run_holo_guard.HoloComputerAgent)
        run_holo_guard.GuardedAgent = seeding.seeded(run_holo_guard.GuardedAgent)
        for c in (run_holo.HoloComputerAgent, run_holo_guard.HoloComputerAgent, run_holo_guard.GuardedAgent):
            c._guard_attribution_seeded = True
    if no_sleep:
        shim = types.SimpleNamespace(**{k: getattr(time, k) for k in dir(time) if not k.startswith("_")})
        shim.sleep = lambda s: None
        import holo_agent.agent as holo_agent_mod
        run_holo.time = run_holo_guard.time = holo_agent_mod.time = shim
    return Modules(run_holo, run_holo_guard, real_feci)


def build_args(mods: Modules, arm: str, root: str, seed: int, c: dict):
    """argv for the frozen parse_args of the arm's runner. c: served_model, max_steps, test_meta, examples_dir,
    guard_model, sleep_after_reset, pause, no_report."""
    argv = ["--model", c["served_model"], "--max_steps", str(c["max_steps"]), "--prompt", "v2",
            "--result_dir", result_dir(root, arm, seed), "--test_meta", c["test_meta"],
            "--examples_dir", c["examples_dir"], "--no_recording",
            "--sleep_after_reset", str(c["sleep_after_reset"]), "--pause", str(c["pause"])]
    if c.get("no_report"):
        argv.append("--no_report")
    if arm == "A":
        return mods.run_holo.parse_args(argv)
    gm = "neutral-stub" if arm == "B" else c["guard_model"]
    return mods.run_holo_guard.parse_args(argv + ["--guard", "on", "--guard_model", gm, "--guard_mode", "passive",
                                                  "--guard_max_refusals", "2"])


def result_dir(root: str, arm: str, seed: int) -> str:
    return os.path.join(root, f"arm{arm}", f"seed{seed}")


def episode_dir(root: str, arm: str, seed: int, served_model: str, domain: str, task: str) -> str:
    return os.path.join(result_dir(root, arm, seed), "pyautogui", "screenshot", served_model, domain, task)


def _guard_stats(ep: str) -> dict:
    """Verifier calls, their cost, verdict kinds and errors, from the episode's guard.jsonl (arms B and C)."""
    p = os.path.join(ep, "guard.jsonl")
    out = {"verifier_calls": 0, "verifier_cost_usd": None, "verifier_errors": 0, "guard_decisions": []}
    if not os.path.exists(p):
        return out
    cost, known = 0.0, False
    for line in open(p, encoding="utf-8"):
        rec = json.loads(line)
        out["guard_decisions"].append(rec.get("decision"))
        if "verifier" in rec:
            out["verifier_calls"] += 1
            out["verifier_errors"] += bool(rec["verifier"].get("error"))
            c = rec["verifier"].get("cost_usd")
            if c is not None:
                cost, known = cost + c, True
    out["verifier_cost_usd"] = cost if known else None
    return out


def _requests(ep: str) -> tuple[int, int]:
    p = os.path.join(ep, "seeds.jsonl")
    if not os.path.exists(p):
        return 0, 0
    rows = [json.loads(x) for x in open(p)]
    return len(rows), sum(1 for r in rows if r.get("failed"))


def run_episode(mods: Modules, arm: str, seed: int, domain: str, task: str, env, client, root: str, c: dict,
                attempt: int = 1, sleep=time.sleep) -> dict:
    """Run one episode; never raises. dead = no result.txt after run_one (0 steps or crash before scoring)."""
    args = build_args(mods, arm, root, seed, c)
    ep = episode_dir(root, arm, seed, c["served_model"], domain, task)
    stale = None
    if os.path.isdir(ep) and not os.path.exists(os.path.join(ep, "result.txt")):
        n = 1
        while os.path.exists(f"{ep}.stale{n}"):
            n += 1
        stale = f"{ep}.stale{n}"
        os.rename(ep, stale)
    os.makedirs(ep, exist_ok=True)
    seeding.EpisodeContext.set(seed, task, ep)
    if arm == "B":
        mods.run_holo_guard.feci = neutral_verifier.NeutralFeci(seed, task, sleep=sleep)
    elif arm == "C":
        mods.run_holo_guard.feci = mods.real_feci
    module = mods.run_holo if arm == "A" else mods.run_holo_guard
    t0, err, score = time.time(), None, None
    try:
        score = module.run_one(args, env, client, domain, task)
    except Exception as e:  # noqa: BLE001 - a crashed episode is recorded as infra-dead, the run goes on
        err = f"{type(e).__name__}: {str(e)[:300]}"
    finally:
        seeding.EpisodeContext.clear()
        mods.run_holo_guard.feci = mods.real_feci
    wall = time.time() - t0
    n_req, n_fail = _requests(ep)
    return {"arm": arm, "seed": seed, "domain": domain, "task": task, "attempt": attempt, "score": score,
            "dead": not os.path.exists(os.path.join(ep, "result.txt")), "error": err, "wall_s": round(wall, 1),
            "model_requests": n_req, "model_request_failures": n_fail, **_guard_stats(ep),
            "stale_moved_to": stale, "started_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime(t0))}
