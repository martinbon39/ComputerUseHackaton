"""Extract, for each task of an OSWorld run directory, the tool of the last recorded step and the score.
Usage: python extract_last_steps.py ~/osw/results_test_gh_orig_modal_test > results_test_gh_orig_modal_test/last_steps.jsonl
"""
import glob
import json
import os
import sys

root = sys.argv[1]
for t in sorted(glob.glob(os.path.join(root, "pyautogui/screenshot/*/*/*/traj.jsonl"))):
    d = os.path.dirname(t)
    lines = [json.loads(x) for x in open(t) if x.strip()]
    tools = [x.get("tool_name") for x in lines if x.get("tool_name")]
    print(json.dumps({"task": "/".join(d.split("/")[-2:]), "steps": len(lines),
                      "last_tool": tools[-1] if tools else None,
                      "score": float(open(os.path.join(d, "result.txt")).read().strip())}))
