"""Arm B's neutral verifier (PREREG_GUARD_ATTRIBUTION.md, "Arms", B): always COMPLETE, after a delay drawn from the
recorded latencies of the real verifier (recorded_latencies.json, frozen from
results_test_gh_orig_guard_claude meta.json feci_guard.verifier_latency_s by extract_latencies.py).

It replaces the `feci` module seen by GuardedAgent (run_holo_guard.py:108 calls feci.check, :191 reads
feci.VERIFIER_SHA), so the guarded loop, the fresh screenshot at answer time and the guard logs are unchanged; only
the verdict and its source differ from arm C. The delay is drawn by resampling the recorded values with an RNG seeded
from (study seed, task id, index of the verifier call in the episode), so it is reproducible.

CLI: python3 neutral_verifier.py --report [--draws 10000]   (prints quantiles of draws vs recorded, and a KS test)
"""
from __future__ import annotations

import argparse
import hashlib
import inspect
import json
import math
import os
import random
import time

HERE = os.path.dirname(os.path.abspath(__file__))
LATENCIES = os.path.join(HERE, "recorded_latencies.json")


def recorded() -> list[float]:
    return list(json.load(open(LATENCIES))["values_s"])


_VALUES = recorded()


def _code_sha(*objs) -> str:
    """sha of the latency data and of the given functions/classes only, so that editing another stub in this file
    does not change it."""
    h = hashlib.sha256(open(LATENCIES, "rb").read())
    for o in objs:
        h.update(inspect.getsource(o).encode())
    return h.hexdigest()[:8]


def draw_latency(seed: int, task_id: str, step: int, values: list[float] | None = None) -> float:
    vals = values or _VALUES
    h = hashlib.sha256(f"neutral-latency|{int(seed)}|{task_id}|{int(step)}".encode()).digest()
    return random.Random(int.from_bytes(h[:8], "big")).choice(vals)


class NeutralFeci:
    """Drop-in for the feci_guard module inside run_holo_guard: same check() signature and return shape."""

    VERIFIER_SHA = None

    def __init__(self, seed: int, task_id: str, sleep=time.sleep):
        self.seed, self.task_id, self.sleep, self.calls = int(seed), task_id, sleep, 0

    def check(self, instruction, screenshot_png, answer="", history=None, mode=None, model=None) -> dict:
        lat = draw_latency(self.seed, self.task_id, self.calls)
        self.calls += 1
        self.sleep(lat)
        detail = {"ok": True, "verdict": "COMPLETE", "requirements": [], "missing_requirement": "", "evidence": "",
                  "next_action": "", "model": "neutral-stub", "backend": "neutral_stub", "mode": mode or "passive",
                  "error": None, "cost_usd": 0.0, "latency_s": lat, "verifier_sha": VERIFIER_SHA,
                  "screenshot_received": bool(screenshot_png)}
        return {"verdict": "accept", "kind": "complete", "requirements": [], "feedback": "", "detail": detail}


NeutralFeci.VERIFIER_SHA = VERIFIER_SHA = "neutral-" + _code_sha(draw_latency, NeutralFeci)

PLACEBO_RATE = 0.23
PLACEBO_MESSAGE = ("Verifier: the task is not complete yet. Check on the screen that every requirement of the task is "
                   "met before answering. Continue the task.")


def placebo_refuses(seed: int, task_id: str, call: int, rate: float = PLACEBO_RATE) -> bool:
    h = hashlib.sha256(f"placebo-refusal|{int(seed)}|{task_id}|{int(call)}".encode()).digest()
    return int.from_bytes(h[:8], "big") / 2 ** 64 < rate


class PlaceboFeci(NeutralFeci):
    """Arm D (supplementary prereg PREREG_GUARD_PLACEBO.md): refuses each checked answer with probability PLACEBO_RATE,
    drawn from (study seed, task id, index of the verifier call in the episode), with one fixed generic message;
    otherwise COMPLETE. Same latency draw as arm B for the same call. Reruns of an episode draw the same refusals.
    Like the real guard (feci_guard.check), a failed fresh screenshot gives no verdict and the answer passes."""

    VERIFIER_SHA = None

    def __init__(self, seed: int, task_id: str, sleep=time.sleep, rate: float = PLACEBO_RATE):
        super().__init__(seed, task_id, sleep=sleep)
        self.rate = rate

    def check(self, instruction, screenshot_png, answer="", history=None, mode=None, model=None) -> dict:
        call = self.calls
        r = super().check(instruction, screenshot_png, answer, history, mode, model)
        r["detail"].update(model="placebo-stub", backend="placebo_stub", verifier_sha=self.VERIFIER_SHA,
                           placebo_rate=self.rate)
        if not screenshot_png:
            r["detail"].update(ok=False, verdict=None, error="no screenshot")
            r.update(kind="no_verdict")
            return r
        if placebo_refuses(self.seed, self.task_id, call, self.rate):
            r["detail"].update(verdict="INCOMPLETE", missing_requirement="(placebo)", next_action="")
            r.update(verdict="reject", kind="incomplete", feedback=PLACEBO_MESSAGE)
        return r


PlaceboFeci.VERIFIER_SHA = "placebo-" + _code_sha(draw_latency, NeutralFeci, placebo_refuses, PlaceboFeci)


def ks_two_sample(a: list[float], b: list[float]) -> tuple[float, float]:
    """Two-sample Kolmogorov-Smirnov statistic and asymptotic p-value (stdlib)."""
    a, b = sorted(a), sorted(b)
    na, nb, i, j, d = len(a), len(b), 0, 0, 0.0
    while i < na and j < nb:
        x = min(a[i], b[j])
        while i < na and a[i] <= x:
            i += 1
        while j < nb and b[j] <= x:
            j += 1
        d = max(d, abs(i / na - j / nb))
    en = math.sqrt(na * nb / (na + nb))
    lam = (en + 0.12 + 0.11 / en) * d
    p = 2 * sum((-1) ** (k - 1) * math.exp(-2 * k * k * lam * lam) for k in range(1, 101))
    return d, min(1.0, max(0.0, p))


def quantiles(v: list[float], qs=(0.05, 0.1, 0.25, 0.5, 0.75, 0.9, 0.95)) -> dict:
    s = sorted(v)
    return {q: s[min(len(s) - 1, int(q * len(s)))] for q in qs}


def report(draws: int = 10000) -> dict:
    rec = recorded()
    sim = [draw_latency(s, f"task{t}", st) for s in range(3) for t in range(draws // 30 + 1) for st in range(10)][:draws]
    d, p = ks_two_sample(sim, rec)
    return {"n_recorded": len(rec), "n_draws": len(sim), "quantiles_recorded": quantiles(rec),
            "quantiles_drawn": quantiles(sim), "mean_recorded": sum(rec) / len(rec), "mean_drawn": sum(sim) / len(sim),
            "ks_D": d, "ks_p": p}


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--report", action="store_true")
    ap.add_argument("--draws", type=int, default=10000)
    a = ap.parse_args()
    r = report(a.draws)
    print(f"recorded n={r['n_recorded']}  drawn n={r['n_draws']}")
    print("quantile  recorded  drawn")
    for q in r["quantiles_recorded"]:
        print(f"  {q:>5}   {r['quantiles_recorded'][q]:7.2f}  {r['quantiles_drawn'][q]:7.2f}")
    print(f"mean      {r['mean_recorded']:7.2f}  {r['mean_drawn']:7.2f}")
    print(f"KS two-sample D={r['ks_D']:.4f} p={r['ks_p']:.3f}")
