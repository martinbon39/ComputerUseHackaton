"""Power of the frozen primary criterion against a random refuser (placebo arm D), independent re-derivation.

Question: if arm C were a verifier that refuses at random with probability r (no judgment), how often would the frozen
primary criterion of PREREG_GUARD_ATTRIBUTION.md (per-task false "done" averaged over 3 seeds, paired C - B over 120
tasks, bootstrap percentile 95 %, upper bound < 0) be met? Written without reading the lab's simulation code.

Model (each input from the earlier runs, see INPUTS):
- Task t has outcome probabilities (T answered and right, F answered and wrong = false "done", N never answers) drawn
  from a Dirichlet with mean (0.588, 0.233, 0.179) and concentration c. c sets the intra-task correlation (ICC = 1/(c+1));
  F's ICC between the two runs of the original loop is 0.53, so c = 0.89.
- Seeds hold: B and the refuser arm reach the same first answer for a (task, seed) with probability phi (else the
  refuser arm draws its own outcome from the task's probabilities).
- A refuser refuses an answer with probability rho_F if it is wrong and rho_T if it is right (real guard 0.68 / 0.10,
  random refuser r / r). After a refusal the episode ends: repaired (T), wrong again (F, may be refused again), or step
  cap (no false "done"). After 2 refusals the next answer passes (the frozen rule).
- Post-refusal transitions, from the 17 refused episodes of the earlier guarded run, split by the tasks' outcome in
  both original runs: after refusing a wrong answer 1/5 repaired, 1/5 wrong again, 3/5 cap; after refusing a right
  answer 3/5 right again, 1/5 wrong, 1/5 cap. Small n: the grid varies them.
Simplifications: one Dirichlet concentration for all three outcomes (measured ICC: F 0.53, T 0.78, N 0.63); the
empirical transitions already include second refusals (2 of the 10 episodes) and a second round is simulated on top;
infeasible answers are treated as checkable. The point is the order of magnitude, not a precise power.
Usage: ~/osw/venv/bin/python placebo_power.py [--reps 1000] [--out placebo_power.json]
"""
from __future__ import annotations

import argparse
import itertools
import json

import numpy as np

INPUTS = {"mean_TFN": (0.588, 0.233, 0.179), "icc_F": 0.53,
          "source": "results_test_gh_orig_modal_test and results_test_gh_orig (120 tasks each); refused episodes of "
                    "results_test_gh_orig_guard_claude (17)"}


def simulate(rng, n_tasks, n_seeds, conc, phi, rho_F, rho_T, after_F, after_T):
    """Returns per-task mean false-done in B and in the refuser arm, shape (n_tasks,) each."""
    alpha = np.array(INPUTS["mean_TFN"]) * conc
    p = rng.dirichlet(alpha, size=n_tasks)                                  # (tasks, 3)
    u = rng.random((n_tasks, n_seeds))
    cdf = np.cumsum(p, axis=1)[:, None, :]
    base = (u[..., None] > cdf).sum(-1)                                     # 0=T, 1=F, 2=N
    own = (rng.random((n_tasks, n_seeds))[..., None] > cdf).sum(-1)
    x = np.where(rng.random((n_tasks, n_seeds)) < phi, base, own)
    return (base == 1).mean(1), (refuse_rounds(rng, x, rho_F, rho_T, after_F, after_T) == 1).mean(1)


def refuse_rounds(rng, x, rho_F, rho_T, after_F, after_T):
    """At most 2 refusals: the first answer is checked; only an answer given after a refusal is checked again; an
    accepted answer ends the episode. 0 = right, 1 = wrong (false done), 2 = never answered, 3 = step cap."""
    checkable = (x == 0) | (x == 1)
    for _ in range(2):
        refused = checkable & (((x == 1) & (rng.random(x.shape) < rho_F)) | ((x == 0) & (rng.random(x.shape) < rho_T)))
        v = rng.random(x.shape)
        nxt_F = np.where(v < after_F[0], 0, np.where(v < after_F[0] + after_F[1], 1, 3))
        nxt_T = np.where(v < after_T[0], 0, np.where(v < after_T[0] + after_T[1], 1, 3))
        x = np.where(refused & (x == 1), nxt_F, np.where(refused & (x == 0), nxt_T, x))
        checkable = refused & ((x == 0) | (x == 1))
    return x


def simulate_c_vs_d(rng, n_tasks, n_seeds, conc, phi, guard, r, after_F, after_T):
    """Per-task mean false done in C (real guard, rho_F/rho_T = guard) and D (random r), both coupled to B."""
    alpha = np.array(INPUTS["mean_TFN"]) * conc
    p = rng.dirichlet(alpha, size=n_tasks)
    cdf = np.cumsum(p, axis=1)[:, None, :]
    base = (rng.random((n_tasks, n_seeds))[..., None] > cdf).sum(-1)
    out = []
    for rho_F, rho_T in (guard, (r, r)):
        own = (rng.random((n_tasks, n_seeds))[..., None] > cdf).sum(-1)
        x = np.where(rng.random((n_tasks, n_seeds)) < phi, base, own)
        out.append((refuse_rounds(rng, x, rho_F, rho_T, after_F, after_T) == 1).mean(1))
    return out[0], out[1]


def power_c_vs_d(reps, seed=1, n_boot=2000, **kw):
    rng = np.random.default_rng(seed)
    met, eff = 0, []
    for _ in range(reps):
        c, d = simulate_c_vs_d(rng, 120, 3, **kw)
        lo, hi = boot_upper(c - d, rng, n_boot)
        met += hi < 0
        eff.append((c - d).mean())
    return met / reps, float(np.mean(eff))


def boot_upper(d, rng, n_boot):
    idx = rng.integers(0, len(d), size=(n_boot, len(d)))
    m = np.sort(d[idx].mean(1))
    return m[int(0.025 * n_boot)], m[int(0.975 * n_boot) - 1]


def power(reps, seed=0, n_boot=2000, **kw):
    rng = np.random.default_rng(seed)
    met, eff = 0, []
    for _ in range(reps):
        b, x = simulate(rng, 120, 3, **kw)
        d = x - b
        lo, hi = boot_upper(d, rng, n_boot)
        met += hi < 0
        eff.append(d.mean())
    return met / reps, float(np.mean(eff))


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--reps", type=int, default=1000)
    ap.add_argument("--out", default=None, help="write all rows as JSON")
    a = ap.parse_args()
    base = dict(conc=0.89, phi=1.0, after_F=(0.2, 0.2), after_T=(0.6, 0.2))
    rows = []
    print("arm             r     conc phi  after_F(rep,F) after_T(T,F)  effect_pts  P(criterion met)")
    scen = [("real guard", dict(rho_F=0.68, rho_T=0.10))] + [(f"random r={r}", dict(rho_F=r, rho_T=r))
                                                             for r in (0.18, 0.23, 0.25)]
    for name, rho in scen:
        pw, ef = power(a.reps, **base, **rho)
        rows.append({"arm": name, **base, **rho, "effect": ef, "power": pw})
        print(f"{name:15s} {rho['rho_F']:.2f}  {base['conc']:.2f} {base['phi']:.1f}  {base['after_F']}     "
              f"{base['after_T']}   {100*ef:+6.2f}     {pw:.3f}")
    print("\nsensitivity, random refuser r = 0.23:")
    grid = itertools.product((0.5, 0.89, 1.5), (1.0, 0.7, 0.4), ((0.1, 0.2), (0.2, 0.2), (0.2, 0.4)),
                             ((0.6, 0.2), (0.8, 0.1), (0.4, 0.3)))
    for conc, phi, aF, aT in grid:
        pw, ef = power(max(a.reps // 4, 200), conc=conc, phi=phi, after_F=aF, after_T=aT, rho_F=0.23, rho_T=0.23)
        rows.append({"arm": "random r=0.23", "conc": conc, "phi": phi, "after_F": aF, "after_T": aT,
                     "effect": ef, "power": pw})
        print(f"  conc {conc:4.2f} phi {phi:.1f} after_F {aF} after_T {aT}: effect {100*ef:+5.2f} pts, "
              f"P(met) {pw:.2f}")
    print("\nsupplement primary C - D (real guard vs random r = 0.23), central transitions:")
    for name, g in (("guard as offline (0.68, 0.10)", (0.68, 0.10)), ("weaker guard (0.45, 0.10)", (0.45, 0.10)),
                    ("weak guard (0.30, 0.10)", (0.30, 0.10))):
        for phi in (1.0, 0.7):
            pw, ef = power_c_vs_d(max(a.reps // 2, 200), conc=0.89, phi=phi, guard=g, r=0.23,
                                  after_F=(0.2, 0.2), after_T=(0.6, 0.2))
            rows.append({"arm": "C-D", "guard": g, "phi": phi, "effect": ef, "power": pw})
            print(f"  {name:30s} phi {phi:.1f}: effect {100*ef:+6.2f} pts, P(upper < 0) {pw:.2f}")
    if a.out:
        json.dump({"inputs": INPUTS, "rows": rows}, open(a.out, "w"), indent=1)
