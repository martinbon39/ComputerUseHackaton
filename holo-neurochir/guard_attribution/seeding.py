"""Seed plumbing required by report/PREREG_GUARD_ATTRIBUTION.md ("Seeds").

Every model request carries a vLLM sampling seed that is a fixed function of (study seed s, task id, step index),
identical in the original loop (RealtimeGUI HoloComputerAgent, arm A) and in the guarded loop (GuardedAgent, arms B, C).

step index = the loop's own `steps` counter at the time of the request. Both loops call on_step exactly once per
increment of `steps` (and once on the accepted terminal answer), so counting on_step calls reproduces it without
touching the frozen loops. k = how many requests were already sent at that step index (parse retries and steps
retried after a failed screenshot or env.step); k = 0 on the normal path. Transient HTTP retries inside
_call_model resend the same request, so they keep the same seed.

The agent classes are not edited: `seeded(cls)` returns a subclass that wraps the OpenAI client and the on_step
callback. The runner patches the subclasses into the module globals that run_one() looks up.
"""
from __future__ import annotations

import hashlib
import json
import os
import time

SCHEME = "guard-attribution/v1"


def request_seed(seed: int, task_id: str, step: int, k: int = 0) -> int:
    """Deterministic 31-bit seed for one request. Depends only on its four arguments."""
    msg = f"{SCHEME}|{int(seed)}|{task_id}|{int(step)}|{int(k)}".encode()
    return int.from_bytes(hashlib.sha256(msg).digest()[:4], "big") & 0x7FFFFFFF


class EpisodeContext:
    """Set by the runner before each run_one() call; read by the seeded agent at construction."""
    seed: int | None = None
    task_id: str | None = None
    log_dir: str | None = None

    @classmethod
    def set(cls, seed: int, task_id: str, log_dir: str) -> None:
        cls.seed, cls.task_id, cls.log_dir = int(seed), task_id, log_dir

    @classmethod
    def clear(cls) -> None:
        cls.seed = cls.task_id = cls.log_dir = None


class _SeedingCompletions:
    def __init__(self, inner, agent):
        self._inner, self._agent = inner, agent

    def create(self, *a, **kw):
        kw["seed"] = self._agent._seed_now
        return self._inner.create(*a, **kw)


class _SeedingChat:
    def __init__(self, inner, agent):
        self.completions = _SeedingCompletions(inner.completions, agent)


class _SeedingClient:
    """Proxy of an OpenAI client: identical except that chat.completions.create gets seed=<current request seed>."""

    def __init__(self, inner, agent):
        self._inner = inner
        self.chat = _SeedingChat(inner.chat, agent)

    def __getattr__(self, name):
        return getattr(self._inner, name)


def seeded(cls):
    """Subclass of a HoloComputerAgent-like class whose model requests are seeded from EpisodeContext."""

    class Seeded(cls):
        def __init__(self, *a, **kw):
            super().__init__(*a, **kw)
            if EpisodeContext.seed is None or EpisodeContext.task_id is None:
                raise RuntimeError("EpisodeContext not set: refusing to run an unseeded episode")
            self._seed_base, self._seed_task = EpisodeContext.seed, EpisodeContext.task_id
            self._seed_log = os.path.join(EpisodeContext.log_dir, "seeds.jsonl") if EpisodeContext.log_dir else None
            self._seed_step, self._seed_k, self._seed_now = 0, 0, None
            self.client = _SeedingClient(self.client, self)
            inner = self.on_step

            def on_step(*args, **kwargs):
                self._seed_step += 1
                self._seed_k = 0
                return inner(*args, **kwargs) if inner else None

            self.on_step = on_step

        def _call_model(self, messages):
            step, k = self._seed_step, self._seed_k
            self._seed_k += 1
            self._seed_now = request_seed(self._seed_base, self._seed_task, step, k)
            rec = {"seed_base": self._seed_base, "task": self._seed_task, "step": step, "k": k,
                   "request_seed": self._seed_now, "t": round(time.time(), 3)}
            try:
                out = super()._call_model(messages)
            except Exception as e:
                rec["failed"] = f"{type(e).__name__}: {str(e)[:200]}"
                raise
            finally:
                if self._seed_log:
                    with open(self._seed_log, "a", encoding="utf-8") as f:
                        f.write(json.dumps(rec) + "\n")
            return out

    Seeded.__name__ = Seeded.__qualname__ = f"Seeded{cls.__name__}"
    return Seeded
