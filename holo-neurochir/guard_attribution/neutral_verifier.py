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
import json
import math
import os
import random
import time

HERE = os.path.dirname(os.path.abspath(__file__))
LATENCIES = os.path.join(HERE, "recorded_latencies.json")
VERIFIER_SHA = "neutral-" + hashlib.sha256(open(__file__, "rb").read()).hexdigest()[:8]


def recorded() -> list[float]:
    return list(json.load(open(LATENCIES))["values_s"])


_VALUES = recorded()


def draw_latency(seed: int, task_id: str, step: int, values: list[float] | None = None) -> float:
    vals = values or _VALUES
    h = hashlib.sha256(f"neutral-latency|{int(seed)}|{task_id}|{int(step)}".encode()).digest()
    return random.Random(int.from_bytes(h[:8], "big")).choice(vals)


class NeutralFeci:
    """Drop-in for the feci_guard module inside run_holo_guard: same check() signature and return shape."""

    VERIFIER_SHA = VERIFIER_SHA

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
