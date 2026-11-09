import argparse
import json
from collections import Counter, defaultdict
from pathlib import Path


def key(row):
    r = row.get("row", {})
    return (r.get("label", "TEXT"), r.get("task_id"), r.get("t"), row.get("seed"), r.get("text_prompt"))


def main():
    p = argparse.ArgumentParser()
    p.add_argument("artifact")
    p.add_argument("cohort")
    p.add_argument("out_json")
    p.add_argument("out_md")
    a = p.parse_args()
    root = Path(a.artifact)
    rows = [json.loads(x) for x in (root / "generations.jsonl").read_text().splitlines() if x.strip()]
    summary_path = root / "summary.json"
    summary = json.loads(summary_path.read_text())
    cohort = json.loads(Path(a.cohort).read_text())
    assert len(rows) == 51, len(rows)
    assert sum("text_prompt" in x.get("row", {}) for x in rows) == 3
    assert sum("text_prompt" not in x.get("row", {}) for x in rows) == 48
    cohort_keys = {(r["label"], r["task_id"], r["t"], seed) for r in cohort["train"] for seed in cohort["seeds"]}
    structured_keys = {key(x)[:4] for x in rows if "text_prompt" not in x.get("row", {})}
    assert structured_keys == cohort_keys, (len(structured_keys), len(cohort_keys))
    counts = defaultdict(Counter)
    invalid_details = defaultdict(Counter)
    for x in rows:
        label = x.get("row", {}).get("label", "TEXT")
        if label == "TEXT":
            continue
        tool = x.get("tool")
        category = "answer" if tool == "answer" else "valid_nonanswer" if tool else "invalid"
        step_key = (label, x.get("row", {}).get("task_id"), x.get("row", {}).get("t"))
        counts[step_key][category] += 1
        if category == "invalid":
            invalid_details[step_key][f"{x.get('finish_reason')}:{'truncated' if x.get('truncated') else 'empty_or_unparsed'}"] += 1
    errors = sum(bool(x.get("error")) for x in rows)
    truncated = sum(bool(x.get("truncated")) for x in rows)
    for label, per in summary["per_row"].items():
        parts = label.split(" | ")
        label_name, step = parts[1], parts[2]
        task_id, _, t = step.rpartition("@")
        actual = counts[(label_name, task_id, int(t))]
        assert per["answer"] == actual["answer"], (label, per, actual)
        assert per["valid_nonanswer"] == actual["valid_nonanswer"], (label, per, actual)
        assert per["invalid"] == actual["invalid"], (label, per, actual)
        assert per["error"] == 0
    assert errors == 0
    out = {
        "artifact": str(root),
        "summary_source": str(summary_path),
        "rows": len(rows),
        "structured_rows": 48,
        "text_rows": 3,
        "tasks_and_seeds_match_cohort": True,
        "settings": summary["request_settings"],
        "identity": summary["servers"],
        "errors": errors,
        "truncated": truncated,
        "per_stratum": {label: {category: sum(v[category] for k, v in counts.items() if k[0] == label) for category in ("answer", "valid_nonanswer", "invalid")} for label in ("fs+", "fs-", "healthy")},
        "invalid_mechanism": {label: {kind: sum(v[kind] for k, v in invalid_details.items() if k[0] == label) for kind in {kind for k, v in invalid_details.items() if k[0] == label for kind in v}} for label in ("fs+", "fs-")},
        "text_transport": {"nonempty": sum(bool(x.get("content")) for x in rows if "text_prompt" in x.get("row", {})), "stop": sum(x.get("finish_reason") == "stop" for x in rows if "text_prompt" in x.get("row", {}))},
    }
    Path(a.out_json).write_text(json.dumps(out, indent=2) + "\n")
    lines = ["# Mechanical behavioral audit", "", "PASS: raw counts were recomputed and matched the supplied summary and frozen cohort.", "", f"- Rows: {out['rows']} ({out['structured_rows']} structured + {out['text_rows']} text)", f"- Errors: {errors}; truncated: {truncated}"]
    for label in ("fs+", "fs-", "healthy"):
        lines.append(f"- {label}: {out['per_stratum'][label]}")
    lines += ["", "Invalid mechanism counts are computed from raw `tool`/`finish_reason`/`truncated` fields:", ""]
    for label in ("fs+", "fs-"):
        lines.append(f"- {label}: {out['invalid_mechanism'][label]}")
    lines += ["", f"Text transport: {out['text_transport']}", ""]
    Path(a.out_md).write_text("\n".join(lines) + "\n")


if __name__ == "__main__":
    main()
