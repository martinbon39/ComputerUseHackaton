import hashlib
import json
from pathlib import Path


work = Path(__file__).resolve().parent
results = []
for path in sorted(work.glob("*_full/generations.jsonl")):
    summary = path.parent / "summary.json"
    if not summary.is_file():
        continue
    rows = [json.loads(line) for line in path.read_text().splitlines()]
    metadata = json.loads(summary.read_text())
    entry = {
        "name": path.parent.name.removesuffix("_full"),
        "generations_sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
        "n": len(rows),
        "errors": sum(bool(r.get("error")) for r in rows),
        "truncated": sum(bool(r.get("truncated")) for r in rows),
        "settings": metadata["request_settings"],
        "servers": metadata["servers"],
        "groups": {},
    }
    for label in ["fs+", "fs-", "healthy"]:
        subset = [r for r in rows if r["row"].get("label") == label]
        entry["groups"][label] = {
            "n": len(subset),
            "answer": sum(bool(r.get("answer")) for r in subset),
            "valid_nonanswer": sum(bool(r.get("valid_nonanswer")) for r in subset),
            "invalid": sum(not r.get("answer") and not r.get("valid_nonanswer") and not r.get("error") for r in subset),
        }
    texts = [r for r in rows if "text_prompt" in r["row"]]
    entry["text_complete"] = sum(bool(r.get("content")) and not r.get("error") and not r.get("truncated") for r in texts)
    entry["text_n"] = len(texts)
    entry["invalid_gui"] = sum(group["invalid"] for group in entry["groups"].values())
    entry["format_health"] = (
        entry["n"] == 51
        and all(group["n"] == 16 for group in entry["groups"].values())
        and entry["errors"] == entry["truncated"] == entry["invalid_gui"] == 0
        and entry["groups"]["healthy"]["valid_nonanswer"] == 16
        and entry["text_complete"] == entry["text_n"] == 3
    )
    results.append(entry)
(work / "STATIC_RESULTS.json").write_text(json.dumps({"limitation": "Static stopping and format probes only; not an OSWorld success estimate. Text coherence is assessed in the independent behavioral audits.", "results": results}, indent=2) + "\n")
for row in results:
    counts = row["groups"]
    print(row["name"], "fs+", counts["fs+"]["answer"], "fs-", counts["fs-"]["answer"], "healthy", counts["healthy"]["valid_nonanswer"], "invalid", row["invalid_gui"], "errors", row["errors"], "truncated", row["truncated"], "format_health", row["format_health"])
