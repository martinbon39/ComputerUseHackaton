"""Synthetic results tree in the runner's on-disk format, to test analysis.py before any real result exists.

Each task has a latent difficulty u ~ U(0, 1) shared by its seeds and arms. An episode is a false "done" with probability
min(1, 2 u p_arm); otherwise it succeeds (answer, score 1) with probability 0.5, else it never answers (50 steps,
score 0). A and B share their random draws (seeded loops); C shares them with probability 0.7 (seeded until its
first refusal), so the paired design is modelled. A and B share their actions when their outcomes match.
"""
from __future__ import annotations

import json
import os
import random
import zlib

MODEL = "Holo-3.1-4B-modal-orig"


def _write(ep_dir: str, outcome: str, actions_seed: int) -> None:
    os.makedirs(ep_dir, exist_ok=True)
    rng = random.Random(actions_seed)
    n = 50 if outcome == "never" else rng.randrange(2, 20)
    lines = []
    for i in range(n):
        last = i == n - 1 and outcome != "never"
        tc = ({"tool_name": "answer", "content": "done"} if last else
              {"tool_name": "click", "element": "e", "x": rng.randrange(1000), "y": rng.randrange(1000)})
        lines.append(json.dumps({"step_num": i + 1, "tool_name": tc["tool_name"], "tool_call": tc}))
    with open(os.path.join(ep_dir, "traj.jsonl"), "w") as f:
        f.write("\n".join(lines) + "\n")
    with open(os.path.join(ep_dir, "result.txt"), "w") as f:
        f.write("1.0\n" if outcome == "success" else "0.0\n")


def make(root: str, p_fd: dict, n_tasks: int = 120, seeds=(0, 1, 2), gen_seed: int = 0,
         dead: list[tuple[str, int, int]] | None = None, refusal: dict | None = None) -> list[str]:
    """p_fd: {"A": .., "B": .., "C": ..}. dead: (arm, seed, task_index) left without result.txt. Returns task ids."""
    rng = random.Random(gen_seed)
    tasks = [f"dom{t % 5}/task{t:04d}" for t in range(n_tasks)]
    u = {t: rng.random() for t in tasks}
    dead = set(dead or [])
    ledger = []
    for s in seeds:
        for ti, t in enumerate(tasks):
            shared = (rng.random(), rng.random())
            for arm in tuple(p_fd):
                coupled = arm in ("A", "B") or rng.random() < 0.7
                rate = (refusal or {}).get(arm)
                r, r2 = shared if coupled else (rng.random(), rng.random())
                if r < min(1.0, 2 * u[t] * p_fd[arm]):
                    outcome = "false_done"
                else:
                    outcome = "success" if r2 < 0.5 else "never"
                d, i = t.split("/")
                ep = os.path.join(root, f"arm{arm}", f"seed{s}", "pyautogui", "screenshot", MODEL, d, i)
                is_dead = (arm, s, ti) in dead
                if not is_dead and rate is not None:
                    os.makedirs(ep, exist_ok=True)
                    dec = ["refused", "passed_complete"] if rng.random() < rate else ["passed_complete"]
                    with open(os.path.join(ep, "guard.jsonl"), "w") as f:
                        f.write("".join(json.dumps({"decision": x}) + "\n" for x in dec))
                if not is_dead:
                    _write(ep, outcome, zlib.crc32(f"{t}|{s}|{outcome}".encode()) & 0xFFFF if arm in ("A", "B") else rng.randrange(1 << 16))
                ledger.append({"kind": "attempt", "arm": arm, "seed": s, "domain": d, "task": i, "attempt": 1,
                               "dead": is_dead, "score": None if is_dead else 0.0, "error": None, "wall_s": 1.0,
                               "model_requests": 1, "verifier_calls": 0, "verifier_cost_usd": None})
    os.makedirs(root, exist_ok=True)
    with open(os.path.join(root, "ledger.jsonl"), "w") as f:
        f.write("\n".join(json.dumps(x) for x in ledger) + "\n")
    return tasks
