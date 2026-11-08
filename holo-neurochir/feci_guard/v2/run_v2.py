"""Run one verifier-v2 variant on one half of the judge_bench corpus (SPLIT.json). At most 3 concurrent claude calls.
Usage: python run_v2.py --variant a|b|c|<combo> --half dev|holdout
Variants: v1 = frozen v1 (no call: read from judge_bench/claude_responses.jsonl), a = history (2 previous screens +
actions), b = opus, c = strict file-evidence prompt; combos like "ac", "bc", "abc".
Output: v2/runs/<variant>_<half>.jsonl (resumable), one line per episode."""
import argparse, concurrent.futures, json, os, sys, threading
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))
import verifier_v2  # noqa: E402

STUDY = HERE.parent.parent / "verif_study"
LOCK = threading.Lock()
MAX_CONCURRENT = 3


def history(ep, n_prev=2):
    steps = [json.loads(l) for l in open(Path(ep["source_dir"]) / "traj.jsonl") if l.strip()]
    last = steps[-1]
    assert last["tool_name"] == "answer"
    prev = [s for s in steps[:-1] if s.get("screenshot_file")][-n_prev:]
    imgs = [str(Path(ep["source_dir"]) / s["screenshot_file"]) for s in prev]
    acts = []
    for s in steps[:-1]:
        tc = {k: v for k, v in (s.get("tool_call") or {}).items() if k != "tool_name"}
        acts.append(f"{s['tool_name']}({json.dumps(tc, ensure_ascii=False)[:160]})")
    return imgs, acts


def one(ep, variant, out):
    kw = {"model": "opus" if "b" in variant else "sonnet", "strict": "c" in variant, "timeout": 120}
    if "a" in variant:
        kw["history_images"], kw["actions"] = history(ep)
    v = verifier_v2.verify_v2(ep["instruction"], str(STUDY / ep["image_path"]), **kw)
    with LOCK, open(out, "a") as f:
        f.write(json.dumps({"episode_id": ep["episode_id"], "label": ep["label"], "variant": variant, "result": v},
                           ensure_ascii=False) + "\n")
    print(json.dumps({"id": ep["episode_id"][-12:], "v": v["verdict"], "err": v["error"], "s": v["latency_s"]}), flush=True)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--variant", required=True)
    ap.add_argument("--half", choices=["dev", "holdout"], required=True)
    a = ap.parse_args()
    split = json.loads((HERE / "SPLIT.json").read_text())
    ids = set(split[a.half])
    eps = [e for e in json.loads((STUDY / "manifest.json").read_text()) if e["episode_id"] in ids]
    (HERE / "runs").mkdir(exist_ok=True)
    out = HERE / "runs" / f"{a.variant}_{a.half}.jsonl"
    done = {json.loads(l)["episode_id"] for l in open(out)} if out.exists() else set()
    jobs = [e for e in eps if e["episode_id"] not in done]
    print(json.dumps({"variant": a.variant, "half": a.half, "jobs": len(jobs), "done": len(done)}), flush=True)
    with concurrent.futures.ThreadPoolExecutor(MAX_CONCURRENT) as pool:
        for f in [pool.submit(one, e, a.variant, out) for e in jobs]:
            f.result()


if __name__ == "__main__":
    main()
