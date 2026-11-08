#!/usr/bin/env python3
"""Level 1: recompute the paired comparisons from results/scores.csv (standard library only).

Bootstrap: 10,000 resamples of the paired per-task differences, seed 0, 95% percentile interval.
Prints the numbers and checks them against the values published in the paper (tolerance 0.05 point).
"""
import csv, pathlib, random, sys

CSV = pathlib.Path(__file__).resolve().parent / "results" / "scores.csv"


def load():
    runs = {}
    for r in csv.DictReader(CSV.open()):
        runs.setdefault((r["arm"], r["split"]), {})[r["task_id"]] = float(r["score"])
    return runs


def boot(d, n=10000, seed=0):
    rng, k = random.Random(seed), len(d)
    m = sorted(sum(rng.choice(d) for _ in range(k)) / k for _ in range(n))
    return m[int(0.025 * n)], m[int(0.975 * n) - 1]


def merged(runs, arm, splits):
    out = {}
    for s in splits:
        assert not set(out) & set(runs[(arm, s)]), "task id overlap between splits"
        out.update(runs[(arm, s)])
    return out


def paired(a, b):
    t = sorted(set(a) & set(b))
    d = [a[x] - b[x] for x in t]
    lo, hi = boot(d)
    return dict(n=len(t), arm=sum(a[x] for x in t), base=sum(b[x] for x in t), delta=100 * sum(d) / len(t),
                lo=100 * lo, hi=100 * hi, wins=sum(x > 0 for x in d), losses=sum(x < 0 for x in d))


CHECKS = []


def report(label, res, expected=None):
    print(f"{label:<58} n={res['n']:<4} {res['arm']:6.1f} vs {res['base']:6.1f}  "
          f"delta {res['delta']:+5.2f} pt  CI95 [{res['lo']:+5.1f} ; {res['hi']:+5.1f}]  "
          f"{res['wins']} wins / {res['losses']} losses")
    if expected is not None:
        CHECKS.append((label, res["delta"], expected, res["n"]))


def main():
    R = load()
    print("== PRIMARY VERDICT (rule fixed before reading results): merge vs Modal-served original, Modal vs Modal ==")
    cua, om = merged(R, "merge_cua_b050", ["confirm", "test"]), merged(R, "orig_modal", ["confirm", "test"])
    primary = paired(cua, om)
    report("merge_cua_b050 vs orig_modal, reserve + test", primary, 1.94)
    report("  test only (120)", paired(R[("merge_cua_b050", "test")], R[("orig_modal", "test")]), 0.18)
    report("  reserve only (45)", paired(R[("merge_cua_b050", "confirm")], R[("orig_modal", "confirm")]), 6.64)
    print("\n== Other arms and noise references ==")
    report("AlphaEdit broad_residual_p100 vs orig_modal, reserve", paired(R[("alphaedit_broad_residual_p100", "confirm")], R[("orig_modal", "confirm")]))
    report("ExPO lambda=1.25 vs orig_pod, test", paired(R[("expo125", "test")], R[("orig_pod", "test")]))
    report("merge_cua_b050 vs orig_pod, test", paired(R[("merge_cua_b050", "test")], R[("orig_pod", "test")]))
    print("-- noise: the same original model served by two backends --")
    report("orig_pod vs orig_modal, test", paired(R[("orig_pod", "test")], R[("orig_modal", "test")]))
    report("orig_pod vs orig_modal, reserve", paired(R[("orig_pod", "confirm")], R[("orig_modal", "confirm")]))
    bad = [c for c in CHECKS if abs(c[1] - c[2]) > 0.05]
    print("\nchecks against the published values:")
    for l, d, e, n in CHECKS:
        print(f"  {'OK ' if abs(d - e) <= 0.05 else 'BAD'} {l}: {d:+.2f} (expected {e:+.2f}, n={n})")
    print(f"\nVerdict rule: a gain is claimed only if the CI95 lower bound is > 0. Lower bound = {primary['lo']:+.1f} pt -> "
          + ("GAIN" if primary["lo"] > 0 else "NO DETECTABLE GAIN"))
    sys.exit(1 if bad else 0)


if __name__ == "__main__":
    main()
