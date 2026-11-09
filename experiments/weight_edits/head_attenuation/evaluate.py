#!/usr/bin/env python3
import os

os.environ.update(OMP_NUM_THREADS="2", MKL_NUM_THREADS="2", OPENBLAS_NUM_THREADS="2")

import argparse
import concurrent.futures
import datetime as dt
import fcntl
import gzip
import hashlib
import json
import re
import sys
import time
import urllib.request
from pathlib import Path

import jsonschema
import torch
from openai import OpenAI

torch.set_num_threads(2)

POWER = Path("/workspace/astra/astra-power")
OUTPUT_ROOT = Path("/workspace/astra/moon-leak/runs")
EXPECTED_COHORT_SHA256 = "2faee8f1af5a1243b8c8bacbf0369e4e035ab9dc336307c9f6678c0d134c24d0"
EXPECTED_FROZEN_SHA256 = "9bf07af1f630ffbee0f628347270dff9c3abe068aa9fb76c9c8c747e47585839"
EXPECTED_SCHEMA_SHA256 = "16409e28c825ef787ae55ab13fdcb49f4b4f91c5274b98d2f36ae6cdff551304"
EXPECTED_SEEDS = [17000, 17001, 17002, 17003]
EXPECTED_SETTINGS = {
    "temperature": 0.8,
    "top_p": 0.9,
    "top_k": 20,
    "max_tokens": 3072,
    "reasoning_effort": "medium",
    "enable_thinking": True,
    "structured_outputs": "holo_agent step schema (build_schema(make_step_model(TOOLS)))",
    "seed": "per request",
    "text_prompts": {"temperature": 0.0, "max_tokens": 256, "enable_thinking": False},
}
TEXT_PROMPTS = [
    {"id": "translation_fr_en", "prompt": "Translate into English: Le dossier a été renommé avec succès."},
    {"id": "arithmetic_17x19", "prompt": "What is 17 * 19? Reply with only the number."},
    {
        "id": "linux_rename_three_steps",
        "prompt": "Give exactly three short, practical steps to rename old.txt to new.txt on Linux.",
    },
]
DEADLINE = dt.datetime(2026, 11, 8, 9, 40, tzinfo=dt.timezone.utc)
WORKERS = 8
TIMEOUT_SECONDS = 180.0


class DeadlineReached(RuntimeError):
    pass


def now():
    return dt.datetime.now(dt.timezone.utc)


def iso(value=None):
    return (value or now()).isoformat()


def sha256(data):
    return hashlib.sha256(data).hexdigest()


def write_json(path, value):
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n")


def append_jsonl(stream, value):
    stream.write(json.dumps(value, ensure_ascii=False) + "\n")
    stream.flush()
    os.fsync(stream.fileno())


def load_frozen_inputs():
    frozen_bytes = (POWER / "FROZEN.json").read_bytes()
    if sha256(frozen_bytes) != EXPECTED_FROZEN_SHA256:
        raise RuntimeError("FROZEN.json does not match the registered power freeze")
    frozen = json.loads(frozen_bytes)
    schema = json.loads((POWER / "schema.json").read_text())
    schema_sha = sha256(json.dumps(schema, sort_keys=True).encode())
    if frozen.get("cohort_sha256") != EXPECTED_COHORT_SHA256:
        raise RuntimeError("unexpected frozen cohort hash")
    if frozen.get("schema_sha256") != EXPECTED_SCHEMA_SHA256 or schema_sha != EXPECTED_SCHEMA_SHA256:
        raise RuntimeError("unexpected structured-output schema")
    if frozen.get("seeds") != EXPECTED_SEEDS or frozen.get("settings") != EXPECTED_SETTINGS:
        raise RuntimeError("unexpected power seeds or request settings")
    contexts = frozen.get("contexts", [])
    counts = {}
    for context in contexts:
        label = context["row"]["label"]
        counts[label] = counts.get(label, 0) + 1
    if len(contexts) != 55 or counts != {"fs+": 19, "fs-": 20, "healthy": 16}:
        raise RuntimeError(f"unexpected frozen cohort composition: {counts}")
    if len({context["row"]["task_id"] for context in contexts}) != len(contexts):
        raise RuntimeError("frozen task IDs are not unique")
    return frozen_bytes, frozen, schema


def load_messages(context):
    payload_sha = context["payload_sha256"]
    payload_path = POWER / "payloads" / f"{payload_sha}.json.gz"
    blob = gzip.decompress(payload_path.read_bytes())
    if sha256(blob) != payload_sha:
        raise RuntimeError(f"payload hash mismatch: {payload_sha}")
    return json.loads(blob)


def make_client(url):
    return OpenAI(base_url=url, api_key="EMPTY", timeout=TIMEOUT_SECONDS, max_retries=0)


def ensure_before_deadline():
    if now() >= DEADLINE:
        raise DeadlineReached("deadline reached; request was not dispatched")


def server_info(url, client):
    base = url[:-3] if url.endswith("/v1") else url.rstrip("/")
    ensure_before_deadline()
    with urllib.request.urlopen(f"{base}/version", timeout=30) as response:
        version = json.load(response).get("version")
    ensure_before_deadline()
    models = [{"id": item.id, "root": getattr(item, "root", None)} for item in client.models.list().data]
    return {"url": url, "vllm_version": version, "models": models}


def validate_server(info, model, checkpoint):
    if info["vllm_version"] != "0.23.0":
        raise RuntimeError(f"expected vLLM 0.23.0, got {info['vllm_version']!r}")
    if info["models"] != [{"id": model, "root": checkpoint}]:
        raise RuntimeError(f"server model mismatch: {info['models']!r}")


def call(client, model, messages, seed, schema=None):
    structured = schema is not None
    extra = {
        "top_k": 20,
        "chat_template_kwargs": {"enable_thinking": structured},
        "return_tokens_as_token_ids": True,
    }
    kwargs = {
        "temperature": 0.8,
        "top_p": 0.9,
        "max_tokens": 3072,
        "seed": seed,
        "logprobs": True,
        "top_logprobs": 0,
    }
    if structured:
        extra["structured_outputs"] = {"json": schema}
        kwargs["reasoning_effort"] = "medium"
    else:
        kwargs.update(temperature=0.0, max_tokens=256)
    ensure_before_deadline()
    try:
        response = client.chat.completions.create(
            model=model,
            messages=messages,
            extra_body=extra,
            **kwargs,
        )
    except Exception as exc:
        return {"error": repr(exc)[:500]}
    choice = response.choices[0]
    message = choice.message
    reasoning = getattr(message, "reasoning", None) or (message.model_extra or {}).get("reasoning", "") or ""
    content = message.content or ""
    token_ids = []
    if choice.logprobs:
        token_ids = [int(token.token.split(":", 1)[1]) for token in (choice.logprobs.content or [])]
    result = {
        "reasoning": reasoning,
        "content": content,
        "text": (reasoning + "\n</think>\n\n" if reasoning else "") + content,
        "token_ids": token_ids,
        "n_out": response.usage.completion_tokens if response.usage else len(token_ids),
        "finish_reason": choice.finish_reason,
        "stop_reason": getattr(choice, "stop_reason", None) or (choice.model_extra or {}).get("stop_reason"),
        "truncated": choice.finish_reason == "length",
        "error": None,
    }
    if structured:
        try:
            parsed = json.loads(content)
            tool = parsed["tool_call"]["tool_name"]
        except Exception:
            parsed, tool = None, None
        result.update(
            parsed=parsed,
            tool=tool,
            answer=tool == "answer",
            valid_nonanswer=tool is not None and tool != "answer",
        )
    return result


def validate_existing_gui(rows, arm, model, checkpoint, frozen, schema):
    expected = {context["row"]["task_id"]: context for context in frozen["contexts"]}
    seen = set()
    for value in rows:
        task_id = value.get("row", {}).get("task_id")
        key = (task_id, value.get("seed"))
        if key in seen or task_id not in expected:
            raise RuntimeError(f"invalid or duplicate resumed GUI key: {key}")
        context = expected[task_id]
        if any(
            [
                value.get("kind") != "gui",
                value.get("arm") != arm,
                value.get("model") != model,
                value.get("checkpoint") != checkpoint,
                value.get("frozen_sha256") != EXPECTED_FROZEN_SHA256,
                value.get("row") != context["row"],
                value.get("payload_sha256") != context["payload_sha256"],
                value.get("seed") not in EXPECTED_SEEDS,
            ]
        ):
            raise RuntimeError(f"resumed GUI metadata mismatch: {key}")
        valid = False
        if value.get("parsed") is not None:
            try:
                jsonschema.validate(value["parsed"], schema)
                valid = True
            except jsonschema.ValidationError:
                pass
        expected_tool = value.get("tool") if valid else None
        if any(
            [
                valid and expected_tool != value["parsed"]["tool_call"]["tool_name"],
                value.get("schema_valid") is not valid,
                value.get("invalid") is valid,
                value.get("answer") is not (valid and expected_tool == "answer"),
                value.get("valid_nonanswer") is not (valid and expected_tool != "answer"),
            ]
        ):
            raise RuntimeError(f"resumed GUI derived fields mismatch: {key}")
        seen.add(key)
    return seen


def validate_existing_text(rows, arm, model, checkpoint):
    prompts = {item["id"]: item["prompt"] for item in TEXT_PROMPTS}
    seen = set()
    for value in rows:
        prompt_id = value.get("prompt_id")
        if prompt_id in seen or prompt_id not in prompts:
            raise RuntimeError(f"invalid or duplicate resumed text control: {prompt_id}")
        if any(
            [
                value.get("kind") != "text_control",
                value.get("arm") != arm,
                value.get("model") != model,
                value.get("checkpoint") != checkpoint,
                value.get("frozen_sha256") != EXPECTED_FROZEN_SHA256,
                value.get("prompt") != prompts[prompt_id],
                value.get("seed") != 0,
            ]
        ):
            raise RuntimeError(f"resumed text metadata mismatch: {prompt_id}")
        seen.add(prompt_id)
    return seen


def read_jsonl(path):
    if not path.exists():
        return []
    return [json.loads(line) for line in path.read_text().splitlines() if line.strip()]


def run_gui_jobs(client, model, checkpoint, arm, frozen, schema, path, done):
    jobs = []
    for context in frozen["contexts"]:
        messages = load_messages(context)
        for seed in EXPECTED_SEEDS:
            if (context["row"]["task_id"], seed) not in done:
                jobs.append((context, messages, seed))

    def one(job):
        if now() >= DEADLINE:
            return None
        context, messages, seed = job
        started = iso()
        tic = time.monotonic()
        try:
            result = call(client, model, messages, seed, schema)
        except DeadlineReached:
            return None
        valid = False
        validation_error = None
        if result.get("parsed") is not None:
            try:
                jsonschema.validate(result["parsed"], schema)
                valid = True
            except jsonschema.ValidationError as exc:
                validation_error = str(exc)[:500]
        return {
            "kind": "gui",
            "arm": arm,
            "model": model,
            "checkpoint": checkpoint,
            "frozen_sha256": EXPECTED_FROZEN_SHA256,
            "row": context["row"],
            "seed": seed,
            "payload_sha256": context["payload_sha256"],
            "started_utc": started,
            "ended_utc": iso(),
            "elapsed_s": time.monotonic() - tic,
            **result,
            "schema_valid": valid,
            "schema_error": validation_error,
            "invalid": not valid,
            "answer": valid and result.get("tool") == "answer",
            "valid_nonanswer": valid and result.get("tool") != "answer",
        }

    with path.open("a") as stream, concurrent.futures.ThreadPoolExecutor(max_workers=WORKERS) as pool:
        futures = [pool.submit(one, job) for job in jobs]
        for future in concurrent.futures.as_completed(futures):
            value = future.result()
            if value is not None:
                append_jsonl(stream, value)


def run_text_controls(client, model, checkpoint, arm, path, done):
    with path.open("a") as stream:
        for item in TEXT_PROMPTS:
            if item["id"] in done or now() >= DEADLINE:
                continue
            started = iso()
            tic = time.monotonic()
            try:
                result = call(client, model, [{"role": "user", "content": item["prompt"]}], 0)
            except DeadlineReached:
                break
            append_jsonl(
                stream,
                {
                    "kind": "text_control",
                    "arm": arm,
                    "model": model,
                    "checkpoint": checkpoint,
                    "frozen_sha256": EXPECTED_FROZEN_SHA256,
                    "prompt_id": item["id"],
                    "prompt": item["prompt"],
                    "seed": 0,
                    "started_utc": started,
                    "ended_utc": iso(),
                    "elapsed_s": time.monotonic() - tic,
                    **result,
                },
            )


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("checkpoint")
    parser.add_argument("arm")
    parser.add_argument("url", nargs="?", default="http://127.0.0.1:8030/v1")
    parser.add_argument("--model")
    args = parser.parse_args()
    if not re.fullmatch(r"[A-Za-z0-9_.-]+", args.arm):
        parser.error("arm must contain only letters, digits, dot, underscore, or hyphen")
    if now() >= DEADLINE:
        raise SystemExit("deadline reached; no server requests were made")

    checkpoint = str(Path(args.checkpoint).resolve(strict=True))
    model = args.model or f"moon_leak_{args.arm}"
    frozen_bytes, frozen, schema = load_frozen_inputs()
    output = OUTPUT_ROOT / args.arm
    output.mkdir(parents=True, exist_ok=True)
    lock_stream = (output / ".evaluate.lock").open("w")
    try:
        fcntl.flock(lock_stream, fcntl.LOCK_EX | fcntl.LOCK_NB)
    except BlockingIOError as exc:
        raise SystemExit(f"another evaluator is already running for arm {args.arm}") from exc
    receipts = output / "receipts"
    receipts.mkdir(exist_ok=True)
    spec = {
        "arm": args.arm,
        "model": model,
        "checkpoint": checkpoint,
        "url": args.url,
        "vllm_version": "0.23.0",
        "cohort_sha256": EXPECTED_COHORT_SHA256,
        "frozen_sha256": sha256(frozen_bytes),
        "schema_sha256": EXPECTED_SCHEMA_SHA256,
        "evaluator_sha256": sha256(Path(__file__).read_bytes()),
        "seeds": EXPECTED_SEEDS,
        "settings": EXPECTED_SETTINGS,
        "text_prompts": TEXT_PROMPTS,
        "workers": WORKERS,
        "timeout_seconds": TIMEOUT_SECONDS,
        "deadline_utc": DEADLINE.isoformat(),
    }
    spec_path = output / "run_spec.json"
    if spec_path.exists():
        if json.loads(spec_path.read_text()) != spec:
            raise RuntimeError("resume refused: run_spec.json does not exactly match this invocation")
    else:
        write_json(spec_path, spec)

    gui_path = output / "generations.jsonl"
    text_path = output / "text_controls.jsonl"
    gui_done = validate_existing_gui(read_jsonl(gui_path), args.arm, model, checkpoint, frozen, schema)
    text_done = validate_existing_text(read_jsonl(text_path), args.arm, model, checkpoint)
    client = make_client(args.url)
    info = server_info(args.url, client)
    validate_server(info, model, checkpoint)
    invocation = now().strftime("%Y%m%dT%H%M%S%fZ")
    write_json(
        receipts / f"start_{invocation}.json",
        {
            "started_utc": iso(),
            "spec": spec,
            "server": info,
            "previous_gui": len(gui_done),
            "previous_text_controls": len(text_done),
        },
    )
    run_gui_jobs(client, model, checkpoint, args.arm, frozen, schema, gui_path, gui_done)
    gui_rows = read_jsonl(gui_path)
    gui_done = validate_existing_gui(gui_rows, args.arm, model, checkpoint, frozen, schema)
    run_text_controls(client, model, checkpoint, args.arm, text_path, text_done)
    text_rows = read_jsonl(text_path)
    text_done = validate_existing_text(text_rows, args.arm, model, checkpoint)
    complete = len(gui_done) == 220 and len(text_done) == len(TEXT_PROMPTS)
    receipt = {
        "ended_utc": iso(),
        "status": "COMPLETE" if complete else "PARTIAL_DEADLINE",
        "gui_completed": len(gui_done),
        "gui_expected": 220,
        "text_controls_completed": len(text_done),
        "text_controls_expected": len(TEXT_PROMPTS),
        "deadline_utc": DEADLINE.isoformat(),
        "generations_sha256": sha256(gui_path.read_bytes()) if gui_path.exists() else None,
        "text_controls_sha256": sha256(text_path.read_bytes()) if text_path.exists() else None,
    }
    write_json(receipts / f"end_{invocation}.json", receipt)
    print(json.dumps(receipt, indent=2))
    raise SystemExit(0 if complete else 2)


if __name__ == "__main__":
    main()
