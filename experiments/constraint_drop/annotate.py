"""Blind annotation of the last 3 steps (note + thought) of answer-terminated episodes. See PROTOCOL.md."""
import json, os, random, re, subprocess, sys, threading
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

HOME = os.path.expanduser("~")
ARMS = {"modal": f"{HOME}/osw/results_test_gh_orig_modal_test", "pod": f"{HOME}/osw/results_test_gh_orig"}
EX = f"{HOME}/osw/rtg/Env/OSWorld/evaluation_examples/examples"
OUT = Path(__file__).with_name("annotations.jsonl")
PROMPT = """You are an annotator. Below is a computer-use task instruction, followed by the text the agent wrote in its last 3 steps, just before declaring the task finished.

Question: in this text written by the agent just before declaring the task finished, does the agent explicitly mention that a requirement of the instruction is NOT yet satisfied (or still has to be done or corrected)?

Answer "yes" only if the agent's own text says so explicitly; do not judge whether the task was actually done.
Reply with ONLY a JSON object, no other text: {"label": "yes" or "no", "quote": "<exact quote from the agent text supporting yes, or empty string>"}

=== TASK INSTRUCTION ===
{instruction}

=== AGENT TEXT (last 3 steps) ===
{agent_text}
"""


def episodes():
    for arm, root in ARMS.items():
        for traj in sorted(Path(root).rglob("traj.jsonl")):
            steps = [json.loads(l) for l in traj.read_text().splitlines() if l.strip()]
            if not steps or steps[-1].get("tool_name") != "answer":
                continue
            s = float((traj.parent / "result.txt").read_text().strip())
            if s not in (0.0, 1.0):
                continue
            meta = json.loads((traj.parent / "meta.json").read_text())
            dom, eid = traj.parent.parent.name, traj.parent.name
            instr = json.loads(Path(f"{EX}/{dom}/{eid}.json").read_text())["instruction"]
            parts = []
            for st in steps[-3:]:
                parts.append(f"[step {st['step_num']}] note: {st.get('note') or ''}\n[step {st['step_num']}] thought: {st.get('thought') or ''}")
            yield {"arm": arm, "domain": dom, "task_id": eid, "cls": "FS" if s == 0 else "TS",
                   "declared_infeasible": bool(meta.get("model_declared_infeasible")),
                   "instruction": instr, "agent_text": "\n".join(parts)}


def ask(ep):
    prompt = PROMPT.replace("{instruction}", ep["instruction"]).replace("{agent_text}", ep["agent_text"])
    for _ in range(2):
        r = subprocess.run(["claude", "-p", "--model", "sonnet"], input=prompt, capture_output=True, text=True, timeout=180)
        m = re.search(r"\{.*\}", r.stdout, re.S)
        try:
            d = json.loads(m.group(0))
            if d.get("label") in ("yes", "no"):
                return d["label"], d.get("quote", ""), r.stdout.strip()
        except Exception:
            pass
    return "unparseable", "", r.stdout.strip()


def norm(t):
    return re.sub(r"\s+", " ", t).strip().lower()


def main():
    eps = list(episodes())
    print({c: sum(e["cls"] == c for e in eps) for c in ("FS", "TS")}, flush=True)
    if "--count" in sys.argv:
        return
    done = set()
    if OUT.exists():
        done = {(j["arm"], j["task_id"]) for j in map(json.loads, OUT.read_text().splitlines())}
    random.Random(20261108).shuffle(eps)
    todo = [e for e in eps if (e["arm"], e["task_id"]) not in done]
    lock = threading.Lock()

    def work(ep):
        label, quote, raw = ask(ep)
        ep.update(label=label, quote=quote, quote_in_text=bool(quote) and norm(quote) in norm(ep["agent_text"]), raw=raw)
        with lock, OUT.open("a") as f:
            f.write(json.dumps(ep, ensure_ascii=False) + "\n")
            print(ep["cls"], label, flush=True)

    with ThreadPoolExecutor(3) as ex:
        list(ex.map(work, todo))


if __name__ == "__main__":
    main()
