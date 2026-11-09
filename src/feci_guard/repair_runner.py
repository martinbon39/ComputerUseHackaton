"""Repair measure, guard arm: osworld/branch_runner.py's paired branching (same replay, pace, fidelity check, scoring),
with the continuation's `answer` going through the exact Feci Guard episode policy (run_holo_guard.GuardedAgent._check:
infeasible answers unchecked, refusal on reject with the verifier feedback as the answer's tool output, at most 2
refusals). The no-guard arm is branch_runner.py itself, unchanged.
One JSON line per branch in <out>/branches.jsonl; the guard journal of each branch in <out>/guard/<task>_k<k>/.
Run through osworld/run_branch.sh's environment: see run_repair.sh.
Usage: python repair_runner.py --episode <task_dir> [...] --server URL=NAME --out <dir> [--k 2] [--max_new 15]
       [--branch_back 0] [--guard_mode passive]
"""
import argparse, json, logging, os, sys, time
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))  # src/ (holo.*, used by osworld/probe_answer_rate)
sys.path.insert(0, str(HERE.parent / "osworld"))
sys.path.insert(0, str(HERE))
import branch_runner as BR  # noqa: E402  (puts holo_repro and the OSWorld root on sys.path)
import run_holo_guard as RG  # noqa: E402
from holo_agent import SYSTEM_PROMPTS  # noqa: E402
from holo_agent.agent import trim_to_last_n_images  # noqa: E402
from holo_agent.tools import TERMINAL_TOOLS, parse_step  # noqa: E402
from osworld_computer_env import OSWorldComputerEnv  # noqa: E402

log = logging.getLogger("repair")


class GuardBranchAgent(BR.BranchAgent, RG.GuardedAgent):
    def run_branch(self, d, steps, n_replay, replay_answer, max_new):
        """Replay steps[0:n_replay] exactly as BranchAgent.run_branch does, then up to max_new model steps with the
        guard on every answer (a refused answer counts as a step, as in run_holo_guard)."""
        assert not replay_answer
        messages = [self._system_message()]
        diffs = []
        gaps = BR.recorded_gaps(steps)
        for i in range(n_replay):
            t_step = time.time()
            image = self.env.screenshot()
            diffs.append(BR.pixel_diff(image, BR.Image.open(d / steps[i]["screenshot_file"])))
            messages.append(self._observation_message(image)); trim_to_last_n_images(messages, self.image_budget)
            r = steps[i]
            step = parse_step(json.dumps({"note": r["note"], "thought": r["thought"], "tool_call": r["tool_call"]}),
                              self.step_model)
            messages.append({"role": "assistant", "content": step.model_dump_json()})
            if (r.get("info") or {}).get("guard") == "refused":
                out = r["info"].get("tool_output", "")
            else:
                result = self.env.step(self._tool_call_to_event(step.tool_call))
                out = result.info.get("tool_output", "") if isinstance(result.info, dict) else str(result.info)
            messages.append({"role": "user", "content": f'<tool_output tool="{step.tool_call.tool_name}">\n{out}\n</tool_output>'})
            if self.pace and i < len(gaps) and gaps[i] is not None:
                time.sleep(max(0.0, min(20.0, gaps[i]) - (time.time() - t_step)))
        answer, finished, new_steps, tools = None, False, 0, []
        frames = Path(self.guard_dir) / "frames"; frames.mkdir(exist_ok=True)
        while new_steps < max_new and not self.env.is_done():
            image = self.env.screenshot()
            image.convert("RGB").save(frames / f"new_{new_steps:02d}.png")  # demo sequences (kept per branch)
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
            with open(frames / "steps.jsonl", "a", encoding="utf-8") as f:
                f.write(json.dumps({"new_step": new_steps, "frame": f"new_{new_steps:02d}.png",
                                    **json.loads(step.model_dump_json())}, ensure_ascii=False) + "\n")
            if tc.tool_name in TERMINAL_TOOLS:
                rec = self._check(n_replay + new_steps, getattr(tc, "content", ""))
                if rec["decision"] != "refused":
                    finished, answer = True, getattr(tc, "content", ""); break
                messages.append({"role": "user", "content": f'<tool_output tool="{tc.tool_name}">\n{rec["feedback"]}\n</tool_output>'})
                tools[-1] = "answer(refused)"; new_steps += 1
                continue
            result = self.env.step(self._tool_call_to_event(tc))
            out = result.info.get("tool_output", "") if isinstance(result.info, dict) else str(result.info)
            messages.append({"role": "user", "content": f'<tool_output tool="{tc.tool_name}">\n{out}\n</tool_output>'})
            new_steps += 1
            if result.done:
                break
        return {"replay_diffs": diffs, "finished_by_agent": finished, "answer": answer, "new_steps": new_steps,
                "tools": tools, "guard": self.guard_summary()}


def one_branch(env, args, rh_args, task_dir, server, k_index):
    d, steps, meta, rec_score = BR.recorded(task_dir)
    domain, example_id = d.parent.name, d.name
    example = json.loads(open(os.path.join(rh_args.examples_dir, domain, f"{example_id}.json")).read())
    t = max(0, len(steps) - 1 - args.branch_back)
    gdir = Path(args.out) / "guard" / f"{domain}_{example_id[:8]}_k{k_index}"
    gdir.mkdir(parents=True, exist_ok=True)
    t0 = time.time()
    env.reset(task_config=example); time.sleep(rh_args.sleep_after_reset)
    url, model, auth = (server.split("=", 2) + [None])[:3]
    agent = GuardBranchAgent(client=BR.client_for(url, auth), model=model,
                             env=OSWorldComputerEnv(env, example["instruction"], pause=rh_args.pause),
                             max_steps=rh_args.max_steps, temperature=rh_args.temperature,
                             reasoning_effort=rh_args.reasoning_effort, image_budget=rh_args.image_budget,
                             system_prompt_template=SYSTEM_PROMPTS[rh_args.prompt], guard_dir=str(gdir),
                             instruction=example["instruction"], guard_model=args.guard_model,
                             guard_mode=args.guard_mode, max_refusals=2)
    s = agent.run_branch(d, steps, t, False, args.max_new)
    declined = bool(s["answer"] is not None and RG._INFEASIBLE_RE.search(s["answer"]))
    if s["answer"] is not None:
        env.step("FAIL" if declined else "DONE", rh_args.pause)
    time.sleep(20)
    score = env.evaluate()
    return {"task": f"{domain}/{example_id}", "mode": "branch", "arm": "guard", "model": model, "k": k_index,
            "branch_at": t, "recorded_score": rec_score, "recorded_steps": len(steps), "score": float(score),
            "declined": declined, "seconds": round(time.time() - t0, 1),
            "replay_diff_max": max(s["replay_diffs"], default=None),
            "replay_valid": max(s["replay_diffs"], default=0.0) <= args.max_replay_diff, **s}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--episode", action="append", required=True)
    ap.add_argument("--server", required=True)
    ap.add_argument("--k", type=int, default=2)
    ap.add_argument("--max_new", type=int, default=15)
    ap.add_argument("--branch_back", type=int, default=0)
    ap.add_argument("--max_replay_diff", type=float, default=0.05)
    ap.add_argument("--guard_model", default=RG.verifier.DEFAULT_MODEL)
    ap.add_argument("--guard_mode", choices=["passive", "active"], default="passive")
    ap.add_argument("--out", required=True)
    args = ap.parse_args()
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s %(message)s")
    rh_args = BR.RH.parse_args(["--max_steps", "50"])
    Path(args.out).mkdir(parents=True, exist_ok=True)
    env = BR.RH._make_env(rh_args)
    try:
        for ep in args.episode:
            for k in range(args.k):
                try:
                    row = one_branch(env, args, rh_args, ep, args.server, k)
                except Exception as e:  # noqa: BLE001 - a failed branch is recorded and the run goes on
                    log.exception("branch failed"); row = {"task": ep, "arm": "guard", "k": k, "error": repr(e)[:300]}
                with open(Path(args.out) / "branches.jsonl", "a") as f:
                    f.write(json.dumps(row, default=str) + "\n")
                log.info("BRANCH %s", json.dumps({x: row.get(x) for x in ("task", "k", "score", "recorded_score", "seconds", "replay_diff_max", "new_steps", "tools")}))
    finally:
        env.close()


if __name__ == "__main__":
    main()
