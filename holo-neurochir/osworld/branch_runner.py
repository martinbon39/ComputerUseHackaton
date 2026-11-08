"""Paired branching on recorded OSWorld episodes (more statistical power per VM-hour than full episodes).
For a recorded episode (a run_holo task dir), in a fresh VM of the same task:
  full    replay every recorded action, including the final answer (DONE/FAIL as run_holo does), then evaluate:
          the replay-fidelity check (a recorded success must score again).
  branch  replay the recorded actions of steps 0..t-1 (t = the final answer step by default), then let the model
          continue for at most --max_new steps from that state, with the recorded history as its context, evaluate.
The replayed history is rebuilt like HoloComputerAgent.run builds it (fresh screenshots, recorded assistant JSON,
fresh tool outputs); each replayed screenshot is compared with the recorded one (mean abs pixel diff).
One JSON line per branch in <out>/branches.jsonl. Run through ~/osw/osh (docker + kvm), from the OSWorld root.
Usage: python branch_runner.py --episode <task_dir> [--episode ...] --mode full|branch --out <dir> [--k 2]
       [--server URL=NAME[=ENVVAR]] [--max_new 15] [--branch_at t]
"""
import argparse, json, logging, os, sys, time
from pathlib import Path

HOLO_REPRO = os.path.expanduser("~/osw/rtg/Env/OSWorld/holo_repro")
sys.path.insert(0, HOLO_REPRO); sys.path.insert(0, os.path.dirname(HOLO_REPRO))
sys.path.insert(0, str(Path(__file__).resolve().parent))
import numpy as np  # noqa: E402
from PIL import Image  # noqa: E402
import run_holo as RH  # noqa: E402
from holo_agent import SYSTEM_PROMPTS, HoloComputerAgent  # noqa: E402
from holo_agent.agent import trim_to_last_n_images  # noqa: E402
from holo_agent.tools import TERMINAL_TOOLS, parse_step  # noqa: E402
from osworld_computer_env import OSWorldComputerEnv  # noqa: E402
from probe_answer_rate import client_for  # noqa: E402

log = logging.getLogger("branch")


def recorded(task_dir):
    d = Path(task_dir)
    steps = [json.loads(l) for l in open(d / "traj.jsonl") if l.strip()]
    meta = json.loads((d / "meta.json").read_text()) if (d / "meta.json").exists() else {}
    score = float((d / "result.txt").read_text()) if (d / "result.txt").exists() else None
    return d, steps, meta, score


def pixel_diff(a, b):
    a = np.asarray(a.convert("RGB").resize((480, 270)), dtype=np.float32)
    b = np.asarray(b.convert("RGB").resize((480, 270)), dtype=np.float32)
    return float(np.abs(a - b).mean() / 255.0)


class BranchAgent(HoloComputerAgent):
    def run_branch(self, d, steps, n_replay, replay_answer, max_new):
        """Replay steps[0:n_replay], then (replay_answer) the recorded answer or up to max_new model steps."""
        messages = [self._system_message()]
        diffs, answer, finished, new_steps, tools = [], None, False, 0, []
        for i in range(n_replay):
            image = self.env.screenshot()
            diffs.append(pixel_diff(image, Image.open(d / steps[i]["screenshot_file"])))
            messages.append(self._observation_message(image)); trim_to_last_n_images(messages, self.image_budget)
            r = steps[i]
            step = parse_step(json.dumps({"note": r["note"], "thought": r["thought"], "tool_call": r["tool_call"]}),
                              self.step_model)
            messages.append({"role": "assistant", "content": step.model_dump_json()})
            result = self.env.step(self._tool_call_to_event(step.tool_call))
            out = result.info.get("tool_output", "") if isinstance(result.info, dict) else str(result.info)
            messages.append({"role": "user", "content": f'<tool_output tool="{step.tool_call.tool_name}">\n{out}\n</tool_output>'})
        if replay_answer:
            last = steps[-1]
            if last["tool_name"] in TERMINAL_TOOLS:
                finished, answer = True, last["tool_call"].get("content", "")
            return {"replay_diffs": diffs, "finished_by_agent": finished, "answer": answer, "new_steps": 0, "tools": []}
        while new_steps < max_new and not self.env.is_done():
            image = self.env.screenshot()
            messages.append(self._observation_message(image)); trim_to_last_n_images(messages, self.image_budget)
            step = None
            for _ in range(3):
                try:
                    content, _reasoning = self._call_model(messages); step = parse_step(content, self.step_model); break
                except Exception as e:  # noqa: BLE001 - same 3-attempt rule as HoloComputerAgent.run
                    log.warning("model call/parse failed: %s", e); time.sleep(1.5)
            if step is None:
                messages.pop(); tools.append("<unparsable>"); new_steps += 1; continue
            messages.append({"role": "assistant", "content": step.model_dump_json()})
            tc = step.tool_call; tools.append(tc.tool_name)
            if tc.tool_name in TERMINAL_TOOLS:
                finished, answer = True, getattr(tc, "content", ""); break
            result = self.env.step(self._tool_call_to_event(tc))
            out = result.info.get("tool_output", "") if isinstance(result.info, dict) else str(result.info)
            messages.append({"role": "user", "content": f'<tool_output tool="{tc.tool_name}">\n{out}\n</tool_output>'})
            new_steps += 1
            if result.done:
                break
        return {"replay_diffs": diffs, "finished_by_agent": finished, "answer": answer, "new_steps": new_steps, "tools": tools}


def one_branch(env, args, rh_args, task_dir, mode, server, k_index):
    d, steps, meta, rec_score = recorded(task_dir)
    domain, example_id = d.parent.name, d.name
    example = json.loads(open(os.path.join(rh_args.examples_dir, domain, f"{example_id}.json")).read())
    t = args.branch_at if args.branch_at is not None else len(steps) - 1
    assert steps[-1]["tool_name"] == "answer" or mode == "branch", f"{domain}/{example_id}: no final answer"
    t0 = time.time()
    env.reset(task_config=example); time.sleep(rh_args.sleep_after_reset)
    url, model, auth = (server.split("=", 2) + [None])[:3] if server else (None, "replay", None)
    client = client_for(url, auth) if url else None
    agent = BranchAgent(client=client, model=model, env=OSWorldComputerEnv(env, example["instruction"], pause=rh_args.pause),
                        max_steps=rh_args.max_steps, temperature=rh_args.temperature,
                        reasoning_effort=rh_args.reasoning_effort, image_budget=rh_args.image_budget,
                        system_prompt_template=SYSTEM_PROMPTS[rh_args.prompt])
    n_replay = len(steps) - 1 if mode == "full" else t
    s = agent.run_branch(d, steps, n_replay, mode == "full", args.max_new)
    declined = bool(s["answer"] is not None and RH._INFEASIBLE_RE.search(s["answer"]))
    if s["answer"] is not None:
        env.step("FAIL" if declined else "DONE", rh_args.pause)
    time.sleep(20)
    score = env.evaluate()
    return {"task": f"{domain}/{example_id}", "mode": mode, "model": model, "k": k_index, "branch_at": n_replay,
            "recorded_score": rec_score, "recorded_steps": len(steps), "score": float(score), "declined": declined,
            "seconds": round(time.time() - t0, 1), "replay_diff_max": max(s["replay_diffs"], default=None),
            "replay_diff_mean": float(np.mean(s["replay_diffs"])) if s["replay_diffs"] else None, **s}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--episode", action="append", required=True)
    ap.add_argument("--mode", choices=["full", "branch"], required=True)
    ap.add_argument("--server", action="append", default=[])
    ap.add_argument("--k", type=int, default=1)
    ap.add_argument("--max_new", type=int, default=15)
    ap.add_argument("--branch_at", type=int)
    ap.add_argument("--out", required=True)
    args = ap.parse_args()
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s %(message)s")
    rh_args = RH.parse_args(["--max_steps", "50"])
    out = Path(args.out); out.mkdir(parents=True, exist_ok=True)
    servers = args.server if args.mode == "branch" else [None]
    env = RH._make_env(rh_args)
    try:
        for ep in args.episode:
            for server in servers:
                for k in range(args.k):
                    try:
                        row = one_branch(env, args, rh_args, ep, args.mode, server, k)
                    except Exception as e:  # noqa: BLE001 - a failed branch is recorded and the run goes on
                        log.exception("branch failed"); row = {"task": ep, "mode": args.mode, "server": server, "k": k, "error": repr(e)[:300]}
                    with open(out / "branches.jsonl", "a") as f:
                        f.write(json.dumps(row) + "\n")
                    log.info("BRANCH %s", json.dumps({k2: row.get(k2) for k2 in ("task", "mode", "model", "k", "score", "recorded_score", "seconds", "replay_diff_max", "new_steps", "tools")}))
    finally:
        env.close()


if __name__ == "__main__":
    main()
