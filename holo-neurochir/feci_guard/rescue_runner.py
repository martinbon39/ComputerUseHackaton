"""Frozen-harness replay and single-gate Holo4 rescue with an unconditional control."""
from __future__ import annotations

import argparse
import hashlib
import json
import logging
import os
from pathlib import Path
import signal
import subprocess
import sys
import time
from datetime import datetime, timezone
from types import SimpleNamespace

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))
sys.path.insert(0, str(HERE.parent / "osworld"))
sys.path.insert(0, str(HERE))
import repair_runner as RR

BR, RG = RR.BR, RR.RG
log = logging.getLogger("rescue")


def digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True).encode()).hexdigest()


def write_json(path, value):
    path.write_text(json.dumps(value, indent=2, ensure_ascii=False, default=str) + "\n")


def append_json(path, value):
    with path.open("a") as stream:
        stream.write(json.dumps(value, ensure_ascii=False, default=str) + "\n")
        stream.flush()
        os.fsync(stream.fileno())


def validate_episode(path, rh_args):
    d, steps, meta, score = BR.recorded(path)
    example = json.loads((Path(rh_args.examples_dir) / d.parent.name / f"{d.name}.json").read_text())
    assert score == 0, f"not a recorded failure: {d}"
    assert steps and steps[-1]["tool_call"]["tool_name"] == "answer", f"no terminal answer: {d}"
    assert not RG._INFEASIBLE_RE.search(steps[-1]["tool_call"].get("content", "")), f"declined: {d}"
    assert not RG._task_feasibility(example)[0], f"officially infeasible: {d}"
    return d, steps, meta, score, example


class RescueAgent(BR.BranchAgent, RG.GuardedAgent):
    def __init__(self, *args, arm, recording, recorded_steps, **kwargs):
        super().__init__(*args, **kwargs)
        self.arm = arm
        self.recording = recording
        self.recorded_steps = recorded_steps
        self.boundary_checked = False
        self.gate = None
        self.boundary_diff = None
        self.model_calls = 0
        self.valid_calls = 0
        self.call_errors = 0
        self.frame_dir = Path(self.guard_dir) / "frames"
        self.frame_dir.mkdir(exist_ok=True)

    def _call_model(self, messages):
        if not self.boundary_checked:
            self.boundary_checked = True
            original = self.recorded_steps[-1]
            image = self.env.screenshot()
            image.save(Path(self.guard_dir) / "boundary.png")
            self.boundary_diff = BR.pixel_diff(image, BR.Image.open(self.recording / original["screenshot_file"]))
            write_json(Path(self.guard_dir) / "boundary_context.json", messages)
            if self.arm == "guard":
                self.gate = self._check(len(self.recorded_steps) - 1, original["tool_call"]["content"])
                if self.gate["decision"] == "refused":
                    original_step = RR.parse_step(json.dumps({key: original[key] for key in ("note", "thought", "tool_call")}), self.step_model)
                    messages.append({"role": "assistant", "content": original_step.model_dump_json()})
                    messages.append({"role": "user", "content": f'<tool_output tool="answer">\n{self.gate["feedback"]}\n</tool_output>'})
                    messages.append(self._observation_message(self.env.screenshot()))
                    RR.trim_to_last_n_images(messages, self.image_budget)
        if self.arm == "guard" and self.gate["decision"] != "refused":
            original = self.recorded_steps[-1]
            return json.dumps({key: original[key] for key in ("note", "thought", "tool_call")}), ""
        call = self.model_calls
        self.model_calls += 1
        self.env.screenshot().save(self.frame_dir / f"call_{call:02d}.png")
        rec = {"call": call, "model": self.model, "input_sha256": digest(messages)}
        started = time.time()
        try:
            content, reasoning = super()._call_model(messages)
            rec.update(content=content, reasoning=reasoning)
            parsed = RR.parse_step(content, self.step_model)
            rec.update(valid=True, step=json.loads(parsed.model_dump_json()))
            self.valid_calls += 1
            return content, reasoning
        except Exception as exc:
            self.call_errors += 1
            rec.update(valid=False, error=type(exc).__name__)
            raise
        finally:
            rec["seconds"] = round(time.time() - started, 3)
            append_json(self.frame_dir / "calls.jsonl", rec)
            log.info("CALL %s", json.dumps({key: rec.get(key) for key in ("call", "valid", "seconds", "error")}))


def available_gib():
    fields = {line.split(":")[0]: line.split(":")[1].strip() for line in Path("/proc/meminfo").read_text().splitlines()}
    return int(fields["MemAvailable"].split()[0]) / 1024 ** 2


def vm_count():
    proc = subprocess.run(["docker", "ps", "--format", "{{.Image}}"], capture_output=True, text=True, check=True)
    return sum("happysixd/osworld" in line for line in proc.stdout.splitlines())


class BranchTimeout(BaseException):
    pass


def alarm_handler(signum, frame):
    raise BranchTimeout("rescue branch exceeded registered time budget")


def one_branch(env, args, rh_args, episode, arm, k):
    d, steps, meta, score, example = validate_episode(episode, rh_args)
    slot = args.out / arm / f"{d.parent.name}_{d.name}_k{k}"
    slot.mkdir(parents=True, exist_ok=True)
    attempts = sorted(slot.glob("attempt_*"))
    assert len(attempts) < 2, "registered infrastructure retry cap reached"
    branch_dir = slot / f"attempt_{len(attempts) + 1}"
    branch_dir.mkdir(exist_ok=False)
    started = time.time()
    env.reset(task_config=example)
    time.sleep(rh_args.sleep_after_reset)
    client = BR.client_for(args.base_url, "RESCUE_AUTH")
    agent = RescueAgent(client=client, model=args.model,
        env=RR.OSWorldComputerEnv(env, example["instruction"], pause=rh_args.pause),
        max_steps=rh_args.max_steps, temperature=rh_args.temperature,
        reasoning_effort=rh_args.reasoning_effort, image_budget=rh_args.image_budget,
        system_prompt_template=RR.SYSTEM_PROMPTS[rh_args.prompt],
        guard_dir=str(branch_dir), instruction=example["instruction"],
        guard_model=args.guard_model, guard_mode="passive", max_refusals=2,
        arm=arm, recording=d, recorded_steps=steps)
    summary = agent.run_branch(d, steps, len(steps) - 1, False, args.max_new)
    declined = bool(summary["answer"] is not None and RG._INFEASIBLE_RE.search(summary["answer"]))
    if summary["answer"] is not None:
        env.step("FAIL" if declined else "DONE", rh_args.pause)
    time.sleep(20)
    evaluated = float(env.evaluate())
    diffs = summary["replay_diffs"]
    row = {"task": f"{d.parent.name}/{d.name}", "arm": arm, "k": k,
        "model": args.model, "attempt": len(attempts) + 1, "recorded_score": score, "recorded_steps": len(steps),
        "branch_at": len(steps) - 1, "score": evaluated, "declined": declined,
        "seconds": round(time.time() - started, 2), "replay_diff_max": max(diffs, default=0),
        "replay_valid": max(diffs, default=0) <= args.max_replay_diff,
        "boundary_diff": agent.boundary_diff,
        "strict_replay_valid": max(diffs + [agent.boundary_diff or 0]) <= args.max_replay_diff,
        "gate": agent.gate, "escalated": bool(agent.gate and agent.gate["decision"] == "refused"),
        "model_calls": agent.model_calls, "valid_model_calls": agent.valid_calls,
        "model_call_errors": agent.call_errors, "guard_summary": agent.guard_summary() if arm == "guard" else None,
        "prompt": rh_args.prompt, "prompt_sha256": hashlib.sha256(agent.system_prompt().encode()).hexdigest(),
        "max_new": args.max_new, **summary}
    assert row["valid_model_calls"] <= args.max_new
    assert arm != "control" or row["gate"] is None
    write_json(branch_dir / "result.json", row)
    return row


def compatibility(args, rh_args, episode):
    from holo.osw_replay import rebuild, to_openai
    d, steps, meta, score, example = validate_episode(episode, rh_args)
    agent = BR.HoloComputerAgent(client=BR.client_for(args.base_url, "RESCUE_AUTH"), model=args.model,
        env=SimpleNamespace(task=example["instruction"]), temperature=rh_args.temperature,
        reasoning_effort=rh_args.reasoning_effort, image_budget=rh_args.image_budget,
        system_prompt_template=RR.SYSTEM_PROMPTS[rh_args.prompt])
    messages = to_openai(rebuild(d, steps, agent.system_prompt(), len(steps) - 1))
    started = time.time()
    content, reasoning = agent._call_model(messages)
    step = RR.parse_step(content, agent.step_model)
    row = {"kind": "recorded_OSWorld_one_step_schema_check", "live_execution": False,
        "task": f"{d.parent.name}/{d.name}", "model": args.model, "base_url": args.base_url,
        "valid": True, "step": json.loads(step.model_dump_json()), "content": content,
        "reasoning": reasoning, "seconds": time.time() - started,
        "input_sha256": digest(messages), "prompt": rh_args.prompt}
    write_json(args.out / "compatibility.json", row)
    log.info("COMPATIBLE tool=%s latency=%.1fs", step.tool_call.tool_name, row["seconds"])


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--episodes", type=Path, default=HERE.parent / "rescue_bench/episodes.txt")
    ap.add_argument("--out", type=Path, required=True)
    ap.add_argument("--base_url", default="https://martinbon39--holo-judge-serve.us-east.modal.run/v1")
    ap.add_argument("--model", default="Holo4-27B")
    ap.add_argument("--guard_model", default="sonnet")
    ap.add_argument("--key_file", type=Path, default=Path.home() / ".holo_modal_key")
    ap.add_argument("--max_new", type=int, default=20, choices=range(1, 21))
    ap.add_argument("--max_replay_diff", type=float, default=.05)
    ap.add_argument("--phase", choices=["compatibility", "pilot", "full"], required=True)
    ap.add_argument("--shards", type=int, default=1, choices=[1, 2])
    ap.add_argument("--shard", type=int, default=0, choices=[0, 1])
    ap.add_argument("--stop_launch", default="2026-11-08T11:20:00+00:00")
    ap.add_argument("--hard_stop", default="2026-11-08T11:29:50+00:00")
    args = ap.parse_args()
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s %(message)s")
    args.out = args.out.expanduser().resolve()
    args.episodes = args.episodes.expanduser().resolve()
    args.key_file = args.key_file.expanduser().resolve()
    os.chdir(Path(BR.HOLO_REPRO).parent)
    frozen = json.loads((HERE.parent / "rescue_bench/FROZEN.json").read_text())
    for path, expected in frozen.items():
        assert hashlib.sha256(Path(path).read_bytes()).hexdigest() == expected, f"frozen source changed: {path}"
    os.environ["RESCUE_AUTH"] = "Authorization: Bearer " + args.key_file.read_text().strip()
    os.environ["GUARD_BACKEND"] = "claude"
    rh_args = BR.RH.parse_args(["--max_steps", "50"])
    args.out.mkdir(parents=True, exist_ok=True)
    episodes = [line.strip() for line in args.episodes.read_text().splitlines() if line.strip()]
    assert len(episodes) == 12 and len(set(episodes)) == 12
    assert args.shard < args.shards
    assert args.phase == "full" or args.shards == 1
    assigned = {"/".join(Path(ep).parts[-2:]) for i, ep in enumerate(episodes) if i % args.shards == args.shard}
    journal = args.out / (f"branches.s{args.shard}-of-{args.shards}.jsonl" if args.shards > 1 else "branches.jsonl")
    for episode in episodes:
        validate_episode(episode, rh_args)
    if args.phase == "compatibility":
        compatibility(args, rh_args, episodes[0])
        return
    compatible = json.loads((args.out / "compatibility.json").read_text())
    assert compatible["valid"] and compatible["model"] == args.model and compatible["base_url"] == args.base_url
    old = [json.loads(line) for path in sorted(args.out.glob("branches*.jsonl")) for line in path.read_text().splitlines() if line.strip()]
    completed = {(row["task"], row["arm"], row["k"]) for row in old if "error" not in row}
    for saved in sorted(args.out.glob("*/*/attempt_*/result.json")):
        row = json.loads(saved.read_text())
        key = row["task"], row["arm"], row["k"]
        if key not in completed and row["task"] in assigned:
            row["recovered_from"] = str(saved)
            append_json(journal, row)
            old.append(row)
            completed.add(key)
    if args.phase == "full":
        first = "/".join(Path(episodes[0]).parts[-2:])
        pilot = [row for row in old if row["task"] == first and "error" not in row]
        assert len(pilot) == 4 and all("error" not in row for row in pilot), "paired pilot must complete before scaling"
        assert any(row["valid_model_calls"] for row in pilot), "pilot produced no valid Holo4 tool"
    else:
        episodes = episodes[:1]
    assert available_gib() >= 10, "fewer than 10 GiB MemAvailable"
    assert vm_count() < 2, "fleet already has two OSWorld VMs"
    stop_launch = datetime.fromisoformat(args.stop_launch).timestamp()
    hard_stop = datetime.fromisoformat(args.hard_stop).timestamp()
    signal.signal(signal.SIGALRM, alarm_handler)
    env = BR.RH._make_env(rh_args)
    failures = 0
    try:
        for episode in episodes:
            task = "/".join(Path(episode).parts[-2:])
            if task not in assigned:
                continue
            for k in range(2):
                for arm in (["guard", "control"] if k == 0 else ["control", "guard"]):
                    if (task, arm, k) in completed:
                        continue
                    if time.time() >= stop_launch or failures >= 2:
                        log.warning("registered stop condition reached")
                        return
                    if available_gib() < 10 or vm_count() > 2:
                        log.warning("resource gate closed; resume explicitly after coordination")
                        return
                    signal.alarm(max(1, min(600, int(hard_stop - time.time()))))
                    try:
                        row = one_branch(env, args, rh_args, episode, arm, k)
                        failures = 0
                    except (Exception, BranchTimeout) as exc:
                        failures += 1
                        log.exception("branch failed")
                        row = {"task": task, "arm": arm, "k": k, "error": str(exc)[:300], "error_type": type(exc).__name__}
                    finally:
                        signal.alarm(0)
                    row["completed_utc"] = datetime.now(timezone.utc).isoformat()
                    append_json(journal, row)
                    log.info("BRANCH %s", json.dumps({key: row.get(key) for key in ("task", "arm", "k", "score", "seconds", "escalated", "replay_valid", "valid_model_calls", "error")}))
    finally:
        signal.alarm(0)
        env.close()


if __name__ == "__main__":
    main()
