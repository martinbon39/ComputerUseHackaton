"""Freeze the recorded latencies of the real verifier (arm C of the earlier online test) into recorded_latencies.json.

Source: <results>/pyautogui/screenshot/*/*/*/meta.json -> feci_guard.verifier_latency_s (one value per verifier call
that returned a latency; written by feci_guard/run_holo_guard.py GuardedAgent.guard_summary).
Usage: python3 extract_latencies.py [--results ~/osw/results_test_gh_orig_guard_claude] [--out recorded_latencies.json]
"""
from __future__ import annotations

import argparse
import glob
import hashlib
import json
import os


def extract(results: str) -> dict:
    files = sorted(glob.glob(os.path.join(results, "pyautogui", "screenshot", "*", "*", "*", "meta.json")))
    values, per_episode, h = [], {}, hashlib.sha256()
    for f in files:
        raw = open(f, "rb").read()
        h.update(raw)
        fg = json.loads(raw).get("feci_guard") or {}
        lat = [x for x in fg.get("verifier_latency_s") or [] if x is not None]
        if lat:
            per_episode["/".join(f.split("/")[-3:-1])] = lat
        values += lat
    return {"source": os.path.basename(os.path.normpath(results)), "n_episodes": len(files),
            "n_episodes_with_latency": len(per_episode), "n_values": len(values),
            "meta_json_sha256": h.hexdigest(), "values_s": values, "per_episode": per_episode}


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--results", default=os.path.expanduser("~/osw/results_test_gh_orig_guard_claude"))
    ap.add_argument("--out", default=os.path.join(os.path.dirname(os.path.abspath(__file__)), "recorded_latencies.json"))
    a = ap.parse_args()
    d = extract(a.results)
    with open(a.out, "w") as f:
        json.dump(d, f, indent=1)
    print(f"{d['n_values']} latencies from {d['n_episodes_with_latency']}/{d['n_episodes']} episodes -> {a.out}")
