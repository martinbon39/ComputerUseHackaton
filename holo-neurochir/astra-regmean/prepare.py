from common import *

sys.path.insert(0, "/workspace/projet")
from holo.osw_replay import check_traj
from holo.osw_taxonomy import load_task


def main():
    assert not (ROOT / "manifest.json").exists()
    source = Path("/workspace/astra/4b/manifest_v2.json")
    broad = json.loads((BROAD / "manifest.json").read_text())
    allow = json.loads((ROOT / "diag_extra.json").read_text())
    allow_ids = {domain + "/" + task for domain, tasks in allow.items() for task in tasks}
    reserved = set(broad["reserve_exclusion_ids"])
    evaluation = {r["task_id"] for r in broad["evaluation"]}
    assert len(allow_ids) == 75 and not allow_ids & reserved
    excluded = reserved | evaluation | {BANNED}
    pool = [dict(r) for r in json.loads(source.read_text())["rows"]
            if r["task_id"] in allow_ids and r["task_id"] not in excluded]
    selected = []
    for label, limit in [("fs+", 19), ("fs-", 19), ("healthy", 16)]:
        by_task = {}
        for r in pool:
            if r["label"] == label:
                if r["task_id"] not in by_task or r["t"] > by_task[r["task_id"]]["t"]:
                    by_task[r["task_id"]] = r
        ordered = sorted(by_task, key=lambda t: hashlib.sha256(("regmean-20261108:" + t).encode()).hexdigest())
        selected.extend(by_task[t] for t in ordered[:limit])
    rows = []
    for i, row in enumerate(selected):
        assert row["pass"] == "results_diag"
        d = Path(row["path"])
        _, _, steps = load_task(d)
        check_traj(d, steps)
        assert steps[row["t"]]["tool_name"] == row["tool"]
        assert (row["tool"] == "answer") == (row["label"] in ["fs+", "fs-"])
        row["id"] = f"context_{i:03d}"
        row["sha256"] = {name: sha(d / name) for name in ["traj.jsonl", "meta.json", "result.txt", "system_prompt.txt"]}
        row["images_sha256"] = {s["screenshot_file"]: sha(d / s["screenshot_file"]) for s in steps[:row["t"] + 1]}
        rows.append(row)
    assert len(rows) <= 54 and len({r["task_id"] for r in rows if r["label"] == "fs+"}) >= 10
    tasks = {r["task_id"] for r in rows}
    assert not tasks & excluded
    manifest = dict(rows=rows, evaluation=broad["evaluation"], text_prompts=broad["text_prompts"], seeds=list(range(7100, 7108)),
                    source=str(source), source_sha256=sha(source), broad_manifest_sha256=sha(BROAD / "manifest.json"),
                    allowlist_sha256=sha(ROOT / "diag_extra.json"), excluded_ids=sorted(excluded),
                    model=str(HOLO), positions=["prefill", "endthink_before_note"],
                    selection="19 fs+, 19 true finishes and 16 latest healthy steps, one per task/stratum, fixed SHA256 ordering",
                    parameters=dict(beta=0.5, preservation_lambda=1.0, ridge_trace_over_d=[0.01, 0.1, 1.0],
                                    construction_positions=[0, 1], per_stratum_mean_covariance=True),
                    replay_limit="Trajectory structure and token counts checked; unlogged harness errors require external run-log evidence.")
    write_json(ROOT / "manifest.json", manifest)
    (ROOT / "manifest.sha256").write_text(sha(ROOT / "manifest.json") + "\n")
    print(json.dumps(dict(rows=len(rows), tasks=len(tasks), labels={label: sum(r["label"] == label for r in rows) for label in ["fs+", "fs-", "healthy"]}, manifest_sha256=sha(ROOT / "manifest.json"))))


if __name__ == "__main__":
    main()
