import json
from pathlib import Path


work = Path(__file__).resolve().parent
static = {r["name"]: r for r in json.loads((work / "STATIC_RESULTS.json").read_text())["results"]}
accounts = {
    "cua_b025": [1, 2],
    "cua_b050": [2],
    "cua_b100": [1],
    "fara_b025": [1],
    "fara_b050": [1],
    "fara_b100": [1],
    "dual_mean_b050": [1],
    "cua_mid_b050": [1, 2],
    "cua_mid_b025": [2],
}
rows = []
for label, cloud_accounts in accounts.items():
    build = json.loads((work / f"{label}_build.json").read_text())["build"]
    evidence_name = f"VERIFY_{label.upper()}.json"
    audit = json.loads((work / evidence_name).read_text())
    assert audit["verdict"] == "PASS", label
    name = "merge_" + label
    assert Path(build["output"]).name == name
    measured = static.get(name)
    status = ("HEALTHY" if measured["format_health"] else "REJECTED") if measured else "QUEUED" if build.get("layer_range") else "NOT_RUN_SCOPE_AMENDMENT"
    behavior_name = f"VERIFY_{label.upper()}_BEHAVIOR.json"
    if status == "HEALTHY":
        behavior = json.loads((work / behavior_name).read_text())
        assert behavior.get("status") == "PASS_STATIC_AUDIT" or behavior.get("verdict") == "COUNTS_CONFIRMED_WITH_CAUSALITY_LIMIT", label
    rows.append({
        "name": name,
        "method": build["method"],
        "beta": build["beta"],
        "layer_range_half_open": build.get("layer_range"),
        "donors": build["donors"],
        "complete_hf": True,
        "weight_verification": "PASS",
        "weight_evidence": evidence_name,
        "modal_accounts": cloud_accounts,
        "modal_volume_path": f"holo-models:/ckpt/{name}",
        "served_root": f"/models/ckpt/{name}",
        "served_name": f"Holo-3.1-4B-{name}",
        "static_status": status,
        "static_evidence": f"{name}_full/generations.jsonl" if measured else None,
        "behavior_audit": behavior_name if measured else None,
        "changed_tensors": len(build["changed_tensors"]),
        "changed_elements": build["changed_elements"],
        "actual_update_l2": build["actual_update_l2"],
        "files": build["files"],
    })
assert len(rows) == 9
(work / "CHECKPOINTS.json").write_text(json.dumps({"owner": "astra-merge", "construction_cap": 9, "constructed": 9, "online_evaluation_owner": "ares", "osworld_score_improvement_established": False, "note": "HEALTHY refers to the frozen static screen and independent behavioral audit, not OSWorld success. QUEUED means no runtime health measurement yet. Cloud account availability is documented by upload records, deployment identities and REPORT.md.", "checkpoints": rows}, indent=2) + "\n")
for row in rows:
    print(row["name"], row["weight_verification"], row["static_status"], "accounts", row["modal_accounts"])
