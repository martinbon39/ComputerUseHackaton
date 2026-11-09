import os
os.environ.update(OMP_NUM_THREADS="2", MKL_NUM_THREADS="2", OPENBLAS_NUM_THREADS="2", TOKENIZERS_PARALLELISM="false", PYTHONDONTWRITEBYTECODE="1")
import argparse
import hashlib
import json
import re
import sys
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
import jsonschema

ROOT = Path(__file__).resolve().parent
REPO = Path(__file__).resolve().parents[3]  # repository root
sys.dont_write_bytecode = True
sys.path.insert(0, str(REPO / "src"))
sys.path.insert(0, str(REPO / "src" / "osworld"))
from astra_cohort_probe import call, server_info, REQUEST_SETTINGS, SCHEMA
from holo.osw_replay import check_traj, rebuild, to_openai
from holo.osw_taxonomy import load_task

EMAIL = re.compile(r"[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}", re.IGNORECASE)


def redact(value):
    if isinstance(value, str):
        return EMAIL.sub("[REDACTED_EMAIL]", value)
    if isinstance(value, list):
        return [redact(x) for x in value]
    if isinstance(value, dict):
        return {redact(k): redact(v) for k, v in value.items()}
    return value


def output_record(label, model, row, seed, result, schema_valid):
    raw_sha = hashlib.sha256(json.dumps(result, sort_keys=True).encode()).hexdigest()
    safe_row = {k: row[k] for k in ["task_id", "t", "label", "tool", "n_in", "text_prompt"] if k in row}
    safe_result = {k: v for k, v in result.items() if k != "token_ids"}
    record = redact(dict(label=label, model=model, row=safe_row, seed=seed, schema_valid=schema_valid, raw_response_sha256=raw_sha, **safe_result))
    encoded = json.dumps(record, ensure_ascii=False)
    assert EMAIL.search(encoded) is None
    return encoded


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("label")
    ap.add_argument("--server", required=True)
    ap.add_argument("--model", required=True)
    args = ap.parse_args()
    out = ROOT / ("evaluation_" + args.label)
    assert not out.exists()
    co = json.loads((ROOT.parent / "alphaedit_broad/evaluation_cohort.json").read_text())
    manifest = json.loads((ROOT / "manifest.json").read_text())
    assert co["train"] == manifest["evaluation"] and co["seeds"] == list(range(7100, 7108))
    assert not {r["task_id"] for r in co["train"]} & {r["task_id"] for r in manifest["rows"]}
    info = server_info(args.server, args.model, None)
    assert info["vllm_version"].startswith("0.23.") and args.model in [m["id"] for m in info["models"]], info
    jobs = []
    for row in co["train"]:
        d = ROOT.parent / "alphaedit_broad/evaluation_data" / row["task_id"]
        for filename, expected in {**row["sha256"], **row["images_sha256"]}.items():
            assert hashlib.sha256((d / filename).read_bytes()).hexdigest() == expected
        _, _, steps = load_task(d)
        check_traj(d, steps)
        assert steps[row["t"]]["tool_name"] == row["tool"]
        msgs = to_openai(rebuild(d, steps, (d / "system_prompt.txt").read_text(), row["t"]))
        for seed in co["seeds"]:
            jobs.append((row, msgs, seed, True))
    for p in co["text_prompts"]:
        jobs.append((dict(text_prompt=p), [{"role": "user", "content": p}], 0, False))
    assert len(jobs) == 51
    for row, _, seed, _ in jobs:
        output_record(args.label, args.model, row, seed, {}, None)
    out.mkdir()
    record = dict(server=info, settings=REQUEST_SETTINGS, seed_list=co["seeds"], planned_calls=len(jobs),
                  schema_sha256=hashlib.sha256(json.dumps(SCHEMA, sort_keys=True).encode()).hexdigest(),
                  canonical_probe_sha256=hashlib.sha256((REPO / "src/osworld/astra_cohort_probe.py").read_bytes()).hexdigest(),
                  privacy="Email strings redacted after parsing and validation; raw-response hash retained, token IDs omitted.")
    (out / "plan.json").write_text(json.dumps(record, indent=2) + "\n")
    with ThreadPoolExecutor(8) as pool, (out / "generations.jsonl").open("w") as log:
        futures = [pool.submit(call, args.server, args.model, None, messages, seed, structured)
                   for row, messages, seed, structured in jobs]
        for i, ((row, messages, seed, structured), future) in enumerate(zip(jobs, futures)):
            result = future.result()
            schema_valid = None
            if structured:
                try:
                    jsonschema.validate(result.get("parsed"), SCHEMA)
                    schema_valid = True
                except jsonschema.ValidationError:
                    schema_valid = False
            encoded = output_record(args.label, args.model, row, seed, result, schema_valid)
            log.write(encoded + "\n")
            log.flush()
            os.fsync(log.fileno())
            print(json.dumps(dict(label=args.label, completed=i + 1, tool=result.get("tool"), error=bool(result.get("error")), schema_valid=schema_valid)), flush=True)
    print(json.dumps(dict(label=args.label, complete=True, records=len(jobs))), flush=True)


if __name__ == "__main__":
    main()
