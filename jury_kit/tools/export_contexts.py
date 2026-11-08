"""Maintainers only: freeze recorded episode contexts (system prompt, history, last 3 screenshots) into contexts/."""
import json, pathlib, shutil, sys
from PIL import Image

OSW = pathlib.Path.home() / "osw" / "results_diag" / "pyautogui" / "screenshot" / "Holo-3.1-4B"
WORK = pathlib.Path("/tmp/astra-merge-work")
OUT = pathlib.Path(__file__).resolve().parent.parent / "contexts"
IMAGE_BUDGET = 3
CONTEXTS = [  # id, domain/task, step index t (0-based), kind
    ("ctx1_false_success_feasible", "chrome/47543840-672a-467d-80df-8f7c3b9788c9", 13, "false success on a feasible task (score 0)"),
    ("ctx2_false_success_infeasible", "chrome/480bcfea-d68f-4aaa-a0a9-2589ef319381", 4, "answer is the CORRECT action here (infeasible task)"),
    ("ctx3_true_finish_multi_apps", "multi_apps/c867c42d-a52d-4a24-8ae3-f75d256b5618", 17, "true finish (score 1)"),
    ("ctx4_true_finish_impress", "libreoffice_impress/ed43c15f-00cb-4054-9c95-62c880865d68", 17, "true finish (score 1)"),
]


def assistant_json(r):
    return json.dumps({"note": r["note"], "thought": r["thought"], "tool_call": r["tool_call"]}, ensure_ascii=False, separators=(",", ":"))


def tool_output(r):
    info = r["info"]
    return str(info["value"]) if set(info) == {"value"} else info.get("tool_output", "")


def sampled(label, tid, t):
    s = json.loads((WORK / label / "summary.json").read_text())["per_row"]
    for k, v in s.items():
        if k.endswith(f"/{tid}@{t}"):
            return {"answer": v["answer"], "n": v["n"], "invalid": v["invalid"]}


for cid, task, t, kind in CONTEXTS:
    d = OSW / task
    steps = [json.loads(l) for l in open(d / "traj.jsonl") if l.strip()]
    assert t == len(steps) - 1 and steps[t]["tool_name"] == "answer"
    sysprompt = (d / "system_prompt.txt").read_text()
    out = OUT / cid
    (out / "images").mkdir(parents=True, exist_ok=True)
    first_img = max(0, t + 1 - IMAGE_BUDGET)
    msgs = [{"role": "system", "text": sysprompt}]
    for i in range(t + 1):
        if i >= first_img:
            name = f"images/step{i:02d}.png"
            Image.open(d / steps[i]["screenshot_file"]).convert("RGB").save(out / name, optimize=True)
            msgs.append({"role": "user", "observation": {"image": name}})
        else:
            msgs.append({"role": "user", "observation": {"evicted": True}})
        if i == t:
            break
        msgs.append({"role": "assistant", "text": assistant_json(steps[i])})
        msgs.append({"role": "user", "text": f'<tool_output tool="{steps[i]["tool_name"]}">\n{tool_output(steps[i])}\n</tool_output>'})
    tid = task.split("/")[1]
    rec = {"id": cid, "task": task, "step_t": t, "kind": kind, "episode_score": float((d / "result.txt").read_text()),
           "recorded_final_step": {"reasoning": steps[t].get("reasoning"), "json": json.loads(assistant_json(steps[t]))},
           "recorded_answer_rate_8_samples_T0.8": {lab: sampled(lab, tid, t) for lab in ("original_pod", "merge_cua_b025_full", "merge_cua_b050_full")},
           "messages": msgs}
    (out / "context.json").write_text(json.dumps(rec, indent=1, ensure_ascii=False))
    print(cid, sum(p.stat().st_size for p in out.rglob("*") if p.is_file()) // 1024, "KB", rec["recorded_answer_rate_8_samples_T0.8"])
