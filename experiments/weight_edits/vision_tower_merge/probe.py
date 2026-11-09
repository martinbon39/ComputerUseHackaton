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

ROOT = Path("/home/orbit/projects/ComputerUseHackaton/holo-neurochir")
sys.path[:0] = [str(ROOT), str(ROOT / "osworld")]
import astra_cohort_probe as canonical
from holo.osw_replay import check_traj, rebuild, to_openai
from holo.osw_taxonomy import load_task

STATE = Path(__file__).resolve().parent
MODEL_ROOTS = {
    "A": "/workspace/hf/hub/models--Hcompany--Holo-3.1-4B/snapshots/8c88265a5a159bfd1492db9243733dd2e6e04a6e",
    "V05": "/dev/shm/moon-vision/cua_b050",
    "V10": "/dev/shm/moon-vision/cua_b100",
    "E025": "/dev/shm/moon-vision/holo_g025",
}

CLIENT_FOR = canonical.client_for
canonical.client_for = lambda url, auth: CLIENT_FOR(url, auth).with_options(max_retries=0)


def digest(data):
    return hashlib.sha256(data).hexdigest()


def now():
    return datetime.datetime.now(datetime.timezone.utc).isoformat()


def write_json(path, value):
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n")


def check_runner():
    contract = json.loads((STATE / "WORKFLOW_FREEZE.json").read_text())
    assert digest(Path(__file__).read_bytes()) == contract["runner_sha256"]
    assert digest((STATE / "FROZEN.json").read_bytes()) == contract["frozen_sha256"]
    assert digest((STATE / "PROTOCOL.md").read_bytes()) == contract["protocol_sha256"]
    return contract


def run(arm, url, limit):
    contract = check_runner()
    frozen_bytes = (STATE / "FROZEN.json").read_bytes()
    frozen = json.loads(frozen_bytes)
    assert digest(json.dumps(canonical.SCHEMA, sort_keys=True).encode()) == frozen["schema_sha256"]
    assert canonical.REQUEST_SETTINGS == frozen["settings"]
    for name, sha in frozen["source_sha256"].items():
        assert digest((ROOT / name).read_bytes()) == sha, name
    model = f"moon_vision_{arm}"
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
    receipt = {"started_utc": now(), "arm": arm, "runner_sha256": contract["runner_sha256"], "frozen_sha256": digest(frozen_bytes), "server": info,
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


TEXT_PROMPTS = [
    "What is 17 + 28? Reply with the number only.",
    "Translate into French: The blue cup is on the table.",
    "Name three common fruits, separated by commas."
]


def texts(arm, url):
    contract = check_runner()
    model = f"moon_vision_{arm}"
    info = canonical.server_info(url, model, None)
    assert info["vllm_version"] == "0.23.0"
    assert info["models"] == [{"id": model, "root": MODEL_ROOTS[arm]}]
    out = STATE / "runs" / arm
    out.mkdir(parents=True, exist_ok=True)
    path = out / "texts.json"
    assert not path.exists()
    rows = []
    for prompt in TEXT_PROMPTS:
        rows.append({"prompt": prompt, "seed": 0, **canonical.call(url, model, None, [{"role": "user", "content": prompt}], 0, False)})
        write_json(path, {"server": info, "runner_sha256": contract["runner_sha256"], "results": rows})
    print(json.dumps(rows), flush=True)


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("command", choices=["run", "texts"])
    ap.add_argument("arm", choices=list(MODEL_ROOTS))
    ap.add_argument("--url", default="http://127.0.0.1:18028/v1")
    ap.add_argument("--limit", type=int)
    args = ap.parse_args()
    if args.command == "run":
        run(args.arm, args.url, args.limit)
    else:
        texts(args.arm, args.url)
