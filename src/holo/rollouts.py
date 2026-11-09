"""Batch rollouts with resume: skips rollouts whose summary.json exists; one crash never stops the batch.
Usage: python -m holo.rollouts --tag diag --tasks a,b,c --seeds 0-7 [--impossible] [--arm original|corrective|steer|patched]
"""
import holo.settings as S
import argparse, json, time, traceback
from pathlib import Path

# MiniWoB step budgets (~2x human steps, capped)
BUDGET = {"click-button": 6, "click-link": 6, "enter-text": 8, "click-button-sequence": 8, "click-checkboxes": 10,
          "click-collapsible": 8, "click-dialog": 6, "click-dialog-2": 6, "click-option": 8, "click-tab": 6,
          "click-tab-2": 10, "click-tab-2-easy": 8, "click-widget": 6, "enter-password": 12, "enter-text-2": 8,
          "focus-text": 6, "focus-text-2": 6, "login-user": 12, "login-user-popup": 14, "search-engine": 14,
          "use-autocomplete": 12, "social-media": 10, "click-menu": 8, "click-test-2": 6, "choose-list": 8,
          "multi-layouts": 14, "multi-orderings": 14, "email-inbox": 16, "email-inbox-delete": 10,
          "click-checkboxes-soft": 12, "navigate-tree": 12, "enter-date": 10, "enter-time": 10, "click-shape": 6,
          "click-color": 6, "click-pie": 8, "click-collapsible-2": 12, "click-scroll-list": 10, "grid-coordinate": 6,
          "enter-text-dynamic": 8, "form-sequence": 10, "form-sequence-2": 10, "click-checkboxes-transfer": 10,
          "simple-arithmetic": 8, "click-test": 6, "click-test-transfer": 6, "book-flight": 20, "copy-paste": 10,
          "unicode-test": 6, "identify-shape": 6, "read-table": 10}


def parse_seeds(s):
    out = []
    for part in s.split(","):
        if "-" in part:
            a, b = part.split("-"); out += list(range(int(a), int(b) + 1))
        else:
            out.append(int(part))
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--tag", required=True)
    ap.add_argument("--tasks", required=True)
    ap.add_argument("--seeds", default="0-7")
    ap.add_argument("--impossible", action="store_true")
    ap.add_argument("--arm", default="original")
    ap.add_argument("--patch", default=None, help="patch_spec.json for --arm patched / steer")
    ap.add_argument("--shard", default="0/1", help="i/N: this process runs every N-th rollout starting at i")
    a = ap.parse_args()
    from holo.model import Holo
    from holo.agent import run_episode
    holo = Holo()
    corrective = a.arm == "corrective"
    if a.arm in ("steer", "patched"):
        from holo.surgery import load_spec, apply_patch_inplace, steering_from_spec
        spec = load_spec(a.patch)
        if a.arm == "patched":
            apply_patch_inplace(holo.model, spec)
        else:
            dirs, alpha = steering_from_spec(spec)
            holo.set_steering(dirs, alpha)
    tasks = a.tasks.split(",")
    seeds = parse_seeds(a.seeds)
    base = S.RUNS_DIR / a.tag
    base.mkdir(parents=True, exist_ok=True)
    log = open(base.parent / f"{base.name}.shard{a.shard.replace('/', 'of')}.log", "a", encoding="utf-8")
    t0 = time.time(); n = 0
    si, sn = map(int, a.shard.split("/"))
    jobs = [(seed, task) for seed in seeds for task in tasks]  # seed-major: every task gets coverage early
    for k, (seed, task) in enumerate(jobs):
        if k % sn != si:
            continue
        if True:
            d = base / f"{task}__s{seed}{'__imp' if a.impossible else ''}"
            if (d / "summary.json").exists():
                continue
            try:
                s = run_episode(holo, task, seed, d, max_steps=BUDGET.get(task, 10), impossible=a.impossible,
                                corrective=corrective)
                s["arm"] = a.arm
                (d / "summary.json").write_text(json.dumps(s, indent=1, ensure_ascii=False), encoding="utf-8")
                line = (f"{task} s{seed} imp={a.impossible} R={s['reward']} steps={s['n_steps']} claimed={s['claimed_done']} "
                        f"aband={s['abandoned']} gen={s['gen_s_mean']} wall={s['wall_s']} err={(s['error'] or '')[:120]!r}")
            except Exception as e:
                line = f"{task} s{seed} CRASH {e!r} {traceback.format_exc()[-300:]!r}"
            n += 1
            print(line, flush=True)
            if log:
                log.write(line + "\n"); log.flush()
    print(f"DONE {n} rollouts in {time.time() - t0:.0f}s", flush=True)


if __name__ == "__main__":
    main()
