import os
os.environ.update(OMP_NUM_THREADS="2", MKL_NUM_THREADS="2", OPENBLAS_NUM_THREADS="2")
import argparse
import concurrent.futures
import datetime
import gzip
import hashlib
import json
import sys
import time
from pathlib import Path

import torch
torch.set_num_threads(2)
import jsonschema

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT), str(ROOT / "osworld")]
import astra_cohort_probe as canonical
from holo.osw_replay import check_traj, rebuild, to_openai
from holo.osw_taxonomy import load_task

STATE = Path(__file__).resolve().parent
MODEL_ROOTS = {
    "A": "/workspace/hf/hub/models--Hcompany--Holo-3.1-4B/snapshots/8c88265a5a159bfd1492db9243733dd2e6e04a6e",
    "B": "/dev/shm/release_merge_cua_b050",
    "C": "/dev/shm/power_broad_residual_p100/broad_residual_p100",
    "D": "/dev/shm/power_broad_residual_random100/broad_residual_random100",
}
CLIENT_FOR = canonical.client_for
canonical.client_for = lambda url, auth: CLIENT_FOR(url, auth).with_options(max_retries=0)


def digest(data):
    return hashlib.sha256(data).hexdigest()


def now():
    return datetime.datetime.now(datetime.timezone.utc).isoformat()


def write_json(path, value):
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n")


def prepare(cohort_path):
    co = json.loads(cohort_path.read_text())
    assert len(co["seeds"]) == 4 and len(set(co["seeds"])) == 4
    assert len({r["task_id"] for r in co["train"]}) == len(co["train"])
    for row in co["train"]:
        assert row["feasible"] and "infeasible" not in json.dumps(row["evaluator_func"]).lower()
        assert row["score"] == (0.0 if row["label"] == "fs+" else 1.0), row["task_id"]
    payload_dir = STATE / "payloads"
    payload_dir.mkdir(exist_ok=False)
    contexts = []
    for row in co["train"]:
        d = Path(row["task_dir"])
        meta, score, steps = load_task(d)
        check_traj(d, steps)
        assert steps[row["t"]]["tool_name"] == row["tool"]
        msgs = to_openai(rebuild(d, steps, (d / "system_prompt.txt").read_text(), row["t"], image_budget=3))
        n_images = sum(ch["type"] == "image_url" for m in msgs if isinstance(m["content"], list) for ch in m["content"])
        assert n_images == min(row["t"] + 1, 3)
        blob = json.dumps(msgs, ensure_ascii=False, separators=(",", ":")).encode()
        sha = digest(blob)
        (payload_dir / f"{sha}.json.gz").write_bytes(gzip.compress(blob, mtime=0))
        contexts.append({"row": row, "payload_sha256": sha, "n_images": n_images, "payload_bytes": len(blob)})
    schema_bytes = json.dumps(canonical.SCHEMA, sort_keys=True).encode()
    write_json(STATE / "schema.json", canonical.SCHEMA)
    frozen = {"created_utc": now(), "cohort_sha256": digest(cohort_path.read_bytes()), "seeds": co["seeds"],
              "settings": canonical.REQUEST_SETTINGS, "schema_sha256": digest(schema_bytes),
              "source_sha256": {str(p.relative_to(ROOT)): digest(p.read_bytes()) for p in
                                [ROOT / "osworld/astra_cohort_probe.py", ROOT / "osworld/probe_answer_rate.py",
                                 ROOT / "holo/osw_replay.py", ROOT / "holo/osw_taxonomy.py", Path(__file__).resolve()]},
              "contexts": contexts}
    write_json(STATE / "FROZEN.json", frozen)
    print(json.dumps({"contexts": len(contexts), "requests_per_arm": 4 * len(contexts), "created_utc": frozen["created_utc"]}), flush=True)


def run(arm, url, limit):
    frozen_bytes = (STATE / "FROZEN.json").read_bytes()
    frozen = json.loads(frozen_bytes)
    assert digest(json.dumps(canonical.SCHEMA, sort_keys=True).encode()) == frozen["schema_sha256"]
    for name, sha in frozen["source_sha256"].items():
        assert digest((ROOT / name).read_bytes()) == sha, name
    model = f"power_{arm}"
    info = canonical.server_info(url, model, None)
    assert info["vllm_version"] == "0.23.0", info
    assert [m["id"] for m in info["models"]] == [model], info
    assert info["models"][0]["root"] == MODEL_ROOTS[arm], info
    out = STATE / "runs" / arm
    out.mkdir(parents=True, exist_ok=True)
    path = out / "generations.jsonl"
    existing = [json.loads(x) for x in path.read_text().splitlines()] if path.exists() else []
    done = {(r["row"]["task_id"], r["seed"]) for r in existing}
    assert len(done) == len(existing)
    expected = {c["row"]["task_id"]: c for c in frozen["contexts"]}
    for r in existing:
        assert r["arm"] == arm and r["model"] == model
        assert r["seed"] in frozen["seeds"]
        assert r["row"] == expected[r["row"]["task_id"]]["row"]
        assert r["payload_sha256"] == expected[r["row"]["task_id"]]["payload_sha256"]
    jobs = []
    for context in frozen["contexts"]:
        sha = context["payload_sha256"]
        blob = gzip.decompress((STATE / "payloads" / f"{sha}.json.gz").read_bytes())
        assert digest(blob) == sha
        msgs = json.loads(blob)
        for seed in frozen["seeds"]:
            if (context["row"]["task_id"], seed) not in done:
                jobs.append((context, msgs, seed))
    if limit:
        jobs = jobs[:limit]
    receipt = {"started_utc": now(), "arm": arm, "frozen_sha256": digest(frozen_bytes), "server": info,
               "scheduled": len(jobs), "previously_completed": len(done), "max_retries": 0, "workers": 8}
    write_json(out / f"start_{len(done):04d}.json", receipt)

    def one(job):
        context, msgs, seed = job
        started = now()
        tic = time.monotonic()
        result = canonical.call(url, model, None, msgs, seed, True)
        valid = False
        validation_error = None
        if result.get("parsed") is not None:
            try:
                jsonschema.validate(result["parsed"], canonical.SCHEMA)
                valid = True
            except jsonschema.ValidationError as exc:
                validation_error = str(exc)[:500]
        return {"arm": arm, "model": model, "row": context["row"], "seed": seed,
                "payload_sha256": context["payload_sha256"], "started_utc": started, "ended_utc": now(),
                "elapsed_s": time.monotonic() - tic, **result, "schema_valid": valid,
                "schema_error": validation_error, "invalid": not valid,
                "answer": valid and result.get("tool") == "answer",
                "valid_nonanswer": valid and result.get("tool") != "answer"}

    with path.open("a") as stream, concurrent.futures.ThreadPoolExecutor(max_workers=8) as pool:
        futures = [pool.submit(one, job) for job in jobs]
        for i, future in enumerate(concurrent.futures.as_completed(futures), 1):
            result = future.result()
            stream.write(json.dumps(result, ensure_ascii=False) + "\n")
            stream.flush()
            os.fsync(stream.fileno())
            print(json.dumps({"utc": now(), "arm": arm, "completed": len(done) + i,
                              "total": len(done) + len(jobs), "task": result["row"]["task_id"],
                              "error": result.get("error"), "invalid": result["invalid"]}), flush=True)
    write_json(out / f"complete_{len(done):04d}.json", {**receipt, "ended_utc": now(), "completed": len(jobs)})


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="command", required=True)
    prep = sub.add_parser("prepare")
    prep.add_argument("cohort", type=Path)
    launch = sub.add_parser("run")
    launch.add_argument("arm", choices=list("ABCD"))
    launch.add_argument("--url", default="http://127.0.0.1:18024/v1")
    launch.add_argument("--limit", type=int)
    args = ap.parse_args()
    if args.command == "prepare":
        prepare(args.cohort)
    else:
        run(args.arm, args.url, args.limit)
