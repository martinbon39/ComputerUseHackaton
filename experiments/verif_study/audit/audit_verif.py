#!/usr/bin/env python3
"""Independent, read-only audit of the final-screen verifier study.

The script reconstructs corpus eligibility from the four raw OSWorld result
trees.  If responses.jsonl exists, it also validates every request and
recomputes verdict metrics without importing maker code.
"""

from __future__ import annotations

import argparse
import base64
import hashlib
import json
import math
import random
import re
import struct
from collections import Counter, defaultdict
from datetime import datetime
from pathlib import Path
from typing import Any


STUDY = Path(__file__).resolve().parents[1]
OSW = Path("/home/orbit/osw")
SOURCES = {
    "diag1": OSW / "results_diag",
    "diag2": OSW / "results_diag2",
    "extra1": OSW / "results_diag_extra_gh/pass1",
    "extra2": OSW / "results_diag_extra_gh/pass2",
}
TASKS = OSW / "rtg/Env/OSWorld/evaluation_examples/examples"
REPLICATES = ("t0", "t08_r1", "t08_r2", "t08_r3")
PROMPT = (
    "Task: {instruction}. Here is the final screen. List every requirement of the task, "
    "then for each say whether the screen shows it is satisfied (yes / no / cannot tell). "
    "Finally answer VERDICT: COMPLETE or INCOMPLETE."
)
VERDICT_RE = re.compile(
    r"(?<!\w)[\"']?VERDICT[\"']?\s*:\s*[\"']?(COMPLETE|INCOMPLETE)\b[\"']?"
    r"(?!\s+or\s+[\"']?(?:COMPLETE|INCOMPLETE)\b)",
    re.IGNORECASE,
)
SCREEN_RE = re.compile(r"^step_(\d+)_(.*)\.png$")


def digest(path: Path) -> str:
    hasher = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            hasher.update(chunk)
    return hasher.hexdigest()


def load_json(path: Path) -> Any:
    return json.loads(path.read_text())


def load_jsonl(path: Path) -> list[dict[str, Any]]:
    return [json.loads(line) for line in path.read_text().splitlines() if line.strip()]


def screen_key(path: Path) -> tuple[int, str]:
    match = SCREEN_RE.match(path.name)
    return (int(match.group(1)), match.group(2)) if match else (-1, path.name)


def png_dimensions(path: Path) -> tuple[int, int] | None:
    with path.open("rb") as handle:
        header = handle.read(24)
    if len(header) != 24 or header[:8] != b"\x89PNG\r\n\x1a\n" or header[12:16] != b"IHDR":
        return None
    return struct.unpack(">II", header[16:24])


def final_tool(row: dict[str, Any]) -> Any:
    value = row.get("tool_name")
    call = row.get("tool_call")
    if not value and isinstance(call, dict):
        value = call.get("tool_name")
    return value


def source_inventory() -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    inventory: list[dict[str, Any]] = []
    selected: list[dict[str, Any]] = []
    seen: set[tuple[str, str, str]] = set()
    for pass_id, source in SOURCES.items():
        for trajectory in sorted(source.rglob("traj.jsonl")):
            directory = trajectory.parent
            task_id, domain = directory.name, directory.parent.name
            episode_id = f"{pass_id}__{domain}__{task_id}"
            row: dict[str, Any] = {
                "episode_id": episode_id,
                "pass_id": pass_id,
                "domain": domain,
                "task_id": task_id,
                "source_dir": str(directory),
                "trajectory_sha256": digest(trajectory),
            }
            key = (pass_id, domain, task_id)
            if key in seen:
                row["exclusion"] = "duplicate_task_pass"
                inventory.append(row)
                continue
            seen.add(key)
            try:
                records = load_jsonl(trajectory)
                last = records[-1]
                task_path = TASKS / domain / f"{task_id}.json"
                task = load_json(task_path)
                result_path = directory / "result.txt"
                score = float(result_path.read_text().strip())
                meta_path = directory / "meta.json"
                meta = load_json(meta_path) if meta_path.is_file() else {}
                evaluator = task.get("evaluator", {}).get("func")
                infeasible = "infeasible" in json.dumps(evaluator).lower()
                partial = 0 < score < 1
                row.update(
                    score=score,
                    score_sha256=digest(result_path),
                    final_tool=final_tool(last),
                    last_step=last.get("step_num"),
                    task_source=str(task_path),
                    task_sha256=digest(task_path),
                    instruction=task["instruction"],
                    evaluator_func=evaluator,
                    infeasible=infeasible,
                    partial=partial,
                    model_declared_infeasible=meta.get("model_declared_infeasible"),
                )
                if row["final_tool"] != "answer":
                    row["exclusion"] = "last_tool_not_answer"
                elif infeasible:
                    row["exclusion"] = "infeasible"
                elif partial:
                    row["exclusion"] = "partial_score"
                elif score not in (0.0, 1.0):
                    row["exclusion"] = "score_out_of_range"
                else:
                    referenced = directory / str(last.get("screenshot_file", "__missing__"))
                    screens = sorted(directory.glob("step_*.png"), key=screen_key)
                    latest = screens[-1] if screens else None
                    if referenced.is_file():
                        protocol_screen = referenced
                        protocol_rule = "final_trajectory_screenshot"
                    elif latest is not None:
                        protocol_screen = latest
                        protocol_rule = "latest_available_step"
                    else:
                        raise FileNotFoundError("No final screenshot")
                    row.update(
                        label="false_success" if score == 0 else "true_success",
                        protocol_screenshot_source=str(protocol_screen),
                        protocol_screenshot_rule=protocol_rule,
                        protocol_screenshot_sha256=digest(protocol_screen),
                        referenced_screenshot_exists=referenced.is_file(),
                        latest_screenshot_source=str(latest) if latest else None,
                        later_than_referenced=bool(
                            latest
                            and referenced.is_file()
                            and screen_key(latest) > screen_key(referenced)
                        ),
                        screen_step_matches_last=(
                            screen_key(protocol_screen)[0] == last.get("step_num")
                        ),
                        screen_dimensions=png_dimensions(protocol_screen),
                        exclusion=None,
                    )
                    selected.append(row)
            except (OSError, ValueError, KeyError, IndexError, json.JSONDecodeError) as error:
                row["exclusion"] = "invalid_or_missing_evidence"
                row["error"] = f"{type(error).__name__}: {error}"
            inventory.append(row)
    return inventory, selected


def all_scored_feasible_inventory() -> dict[str, Any]:
    scores: list[float] = []
    excluded_infeasible = 0
    malformed: list[str] = []
    for source in SOURCES.values():
        for result_path in sorted(source.rglob("result.txt")):
            domain = result_path.parent.parent.name
            task_id = result_path.parent.name
            try:
                task = load_json(TASKS / domain / f"{task_id}.json")
                score = float(result_path.read_text().strip())
                infeasible = "infeasible" in json.dumps(
                    task.get("evaluator", {}).get("func")
                ).lower()
            except (OSError, ValueError, KeyError, json.JSONDecodeError) as error:
                malformed.append(f"{result_path}: {type(error).__name__}: {error}")
                continue
            if infeasible:
                excluded_infeasible += 1
            else:
                scores.append(score)
    return {
        "feasible_scored_episode_count": len(scores),
        "official_score_sum": math.fsum(scores),
        "official_score_mean": math.fsum(scores) / len(scores) if scores else None,
        "infeasible_scored_excluded": excluded_infeasible,
        "malformed": malformed,
        "scope": (
            "All saved result.txt episodes in the four source roots with a non-infeasible task evaluator; "
            "includes partial-score and non-answer episodes and is not the full benchmark."
        ),
    }


def compare_corpus(
    raw_inventory: list[dict[str, Any]], raw_selected: list[dict[str, Any]]
) -> dict[str, Any]:
    manifest = load_json(STUDY / "manifest.json")
    maker_inventory = load_json(STUDY / "inventory.json")
    raw_by_id = {row["episode_id"]: row for row in raw_selected}
    manifest_by_id = {row["episode_id"]: row for row in manifest}
    errors: list[str] = []
    warnings: list[str] = []

    if len(raw_by_id) != len(raw_selected):
        errors.append("independent eligible set contains duplicate episode IDs")
    if len(manifest_by_id) != len(manifest):
        errors.append("manifest contains duplicate episode IDs")
    missing = sorted(set(raw_by_id) - set(manifest_by_id))
    extra = sorted(set(manifest_by_id) - set(raw_by_id))
    if missing:
        errors.append(f"manifest omits {len(missing)} independently eligible episodes")
    if extra:
        errors.append(f"manifest includes {len(extra)} independently ineligible episodes")

    field_mismatches: list[dict[str, Any]] = []
    copied_hash_mismatches: list[dict[str, Any]] = []
    screen_rule_differences: list[dict[str, Any]] = []
    compare_fields = (
        "pass_id",
        "domain",
        "task_id",
        "source_dir",
        "trajectory_sha256",
        "score",
        "score_sha256",
        "final_tool",
        "last_step",
        "task_source",
        "task_sha256",
        "instruction",
        "evaluator_func",
        "infeasible",
        "partial",
        "label",
    )
    for episode_id in sorted(set(raw_by_id) & set(manifest_by_id)):
        raw = raw_by_id[episode_id]
        made = manifest_by_id[episode_id]
        mismatched = {
            field: {"raw": raw.get(field), "manifest": made.get(field)}
            for field in compare_fields
            if raw.get(field) != made.get(field)
        }
        if mismatched:
            field_mismatches.append({"episode_id": episode_id, "fields": mismatched})
        manifest_source = made.get("screenshot_source")
        manifest_screen_hash = made.get("screenshot_sha256")
        if manifest_source != raw.get("protocol_screenshot_source"):
            screen_rule_differences.append(
                {
                    "episode_id": episode_id,
                    "protocol_source": raw.get("protocol_screenshot_source"),
                    "manifest_source": manifest_source,
                    "referenced_exists": raw.get("referenced_screenshot_exists"),
                    "later_than_referenced": raw.get("later_than_referenced"),
                }
            )
        for kind, path_value, expected in (
            ("image_copy", made.get("image_path"), manifest_screen_hash),
            ("task_copy", made.get("task_path"), made.get("task_sha256")),
        ):
            target = STUDY / str(path_value)
            actual = digest(target) if target.is_file() else None
            if actual != expected:
                copied_hash_mismatches.append(
                    {
                        "episode_id": episode_id,
                        "kind": kind,
                        "path": str(target),
                        "expected": expected,
                        "actual": actual,
                    }
                )
        source_screen = Path(str(manifest_source))
        actual_source_screen_hash = digest(source_screen) if source_screen.is_file() else None
        if actual_source_screen_hash != manifest_screen_hash:
            copied_hash_mismatches.append(
                {
                    "episode_id": episode_id,
                    "kind": "source_screen",
                    "path": str(source_screen),
                    "expected": manifest_screen_hash,
                    "actual": actual_source_screen_hash,
                }
            )

    raw_exclusions = Counter(row.get("exclusion") for row in raw_inventory if row.get("exclusion"))
    maker_exclusions = Counter(row.get("exclusion") for row in maker_inventory if row.get("exclusion"))
    if raw_exclusions != maker_exclusions:
        errors.append("maker and independent exclusion counts differ")
    if field_mismatches:
        errors.append(f"{len(field_mismatches)} eligible rows have source-field mismatches")
    if copied_hash_mismatches:
        errors.append(f"{len(copied_hash_mismatches)} copied/source artifacts fail hash checks")
    if screen_rule_differences:
        warnings.append(
            f"{len(screen_rule_differences)} screenshots differ from strict final-record-first protocol reading"
        )
    screen_step_mismatches = [
        row["episode_id"] for row in raw_selected if not row.get("screen_step_matches_last")
    ]
    invalid_pngs = [
        row["episode_id"] for row in raw_selected if row.get("screen_dimensions") is None
    ]
    if screen_step_mismatches:
        errors.append(
            f"{len(screen_step_mismatches)} selected screenshots do not match the final trajectory step"
        )
    if invalid_pngs:
        errors.append(f"{len(invalid_pngs)} selected screenshots lack a valid PNG IHDR")

    task_groups: dict[tuple[str, str], list[dict[str, Any]]] = defaultdict(list)
    image_groups: dict[str, list[str]] = defaultdict(list)
    for row in manifest:
        task_groups[(row["domain"], row["task_id"])].append(row)
        image_groups[row["screenshot_sha256"]].append(row["episode_id"])
    repeated_groups = [rows for rows in task_groups.values() if len(rows) > 1]
    cross_label = [rows for rows in repeated_groups if len({row["label"] for row in rows}) > 1]
    duplicate_image_groups = [ids for ids in image_groups.values() if len(ids) > 1]

    summary = load_json(STUDY / "corpus_summary.json")
    actual_manifest_hash = digest(STUDY / "manifest.json")
    if summary.get("manifest_sha256") != actual_manifest_hash:
        errors.append("corpus_summary manifest SHA256 does not match current manifest")

    scored_feasible = all_scored_feasible_inventory()
    if scored_feasible["malformed"]:
        errors.append("all-scored-feasible inventory contains malformed entries")
    return {
        "errors": errors,
        "warnings": warnings,
        "source_episode_count": len(raw_inventory),
        "independent_eligible_count": len(raw_selected),
        "manifest_count": len(manifest),
        "independent_labels": dict(Counter(row["label"] for row in raw_selected)),
        "independent_exclusions": dict(raw_exclusions),
        "maker_exclusions": dict(maker_exclusions),
        "missing_episode_ids": missing,
        "extra_episode_ids": extra,
        "field_mismatches": field_mismatches,
        "hash_mismatches": copied_hash_mismatches,
        "screen_rule_differences": screen_rule_differences,
        "screen_step_mismatch_episode_ids": screen_step_mismatches,
        "invalid_png_episode_ids": invalid_pngs,
        "screen_dimension_counts": {
            f"{dimensions[0]}x{dimensions[1]}": count
            for dimensions, count in Counter(
                row.get("screen_dimensions") for row in raw_selected if row.get("screen_dimensions")
            ).items()
        },
        "strict_protocol_screen_counts": dict(
            Counter(row["protocol_screenshot_rule"] for row in raw_selected)
        ),
        "manifest_screen_counts": dict(Counter(row["screenshot_rule"] for row in manifest)),
        "unique_task_count": len(task_groups),
        "repeated_task_group_count": len(repeated_groups),
        "episodes_in_repeated_task_groups": sum(len(rows) for rows in repeated_groups),
        "cross_label_repeated_task_group_count": len(cross_label),
        "duplicate_image_hash_group_count": len(duplicate_image_groups),
        "episodes_with_duplicate_image_hash": sum(len(ids) for ids in duplicate_image_groups),
        "duplicate_image_groups": duplicate_image_groups,
        "selected_model_declared_infeasible_counts": {
            str(key): count
            for key, count in Counter(
                row.get("model_declared_infeasible") for row in raw_selected
            ).items()
        },
        "selected_model_declared_infeasible_episode_ids": [
            row["episode_id"]
            for row in raw_selected
            if row.get("model_declared_infeasible") is True
        ],
        "manifest_sha256": actual_manifest_hash,
        "all_scored_feasible_sensitivity_population": scored_feasible,
    }


def wilson(successes: int, total: int, z: float = 1.959963984540054) -> list[float] | None:
    if total == 0:
        return None
    proportion = successes / total
    denominator = 1 + z * z / total
    center = (proportion + z * z / (2 * total)) / denominator
    margin = z * math.sqrt(proportion * (1 - proportion) / total + z * z / (4 * total * total)) / denominator
    return [center - margin, center + margin]


def classify_verdict(
    content: Any, *, status: Any, finish_reason: Any
) -> tuple[str, list[str]]:
    if status != "ok":
        return "error", []
    normalized = re.sub(r"[*`_]", "", content) if isinstance(content, str) else ""
    matches = [match.upper() for match in VERDICT_RE.findall(normalized)]
    unique = sorted(set(matches))
    if finish_reason == "length":
        return "truncated", matches
    if finish_reason != "stop":
        return "invalid_finish", matches
    if not isinstance(content, str):
        return "missing", []
    if len(unique) == 1:
        return unique[0].lower(), matches
    if len(unique) > 1:
        return "ambiguous", matches
    if re.search(r"\bVERDICT\b", normalized, re.IGNORECASE):
        return "malformed", []
    return "missing", []


def requirement_decision_items(content: Any) -> list[dict[str, Any]]:
    if not isinstance(content, str):
        return []
    plain = re.sub(r"[*`_]", "", content)
    before_verdict = re.split(
        r"(?<!\w)[\"']?VERDICT[\"']?\s*:", plain, maxsplit=1, flags=re.IGNORECASE
    )[0]
    general = re.compile(
        r"(?:^|\s[-–—:]\s*|:\s*|\|\s*)(yes|no|cannot tell)\b", re.I
    )
    terminal_parenthetical = re.compile(
        r"\(\s*(yes|no|cannot tell)\s*\)\s*[.!]?$", re.I
    )
    items: list[dict[str, Any]] = []
    original_lines = content.splitlines()
    for line_number, line in enumerate(before_verdict.splitlines(), 1):
        stripped = re.sub(r"^\s*(?:\d+[.)]|[-•])\s*", "", line).strip()
        match = general.search(stripped)
        if match is None:
            match = terminal_parenthetical.search(stripped)
        if match:
            items.append(
                {
                    "decision": match.group(1).lower(),
                    "line_number": line_number,
                    "text": original_lines[line_number - 1].strip(),
                }
            )
    return items


def explicit_requirement_decisions(content: Any) -> tuple[Counter[str], str]:
    """Conservative line-level count; it is formatting, not accuracy scoring."""
    counts = Counter(item["decision"] for item in requirement_decision_items(content))
    if not isinstance(content, str):
        return counts, "missing_content"
    if counts:
        return counts, "parsed_explicit_lines"
    return counts, "no_explicit_decision_lines"


def request_seed(request_id: str) -> int:
    return int(hashlib.sha256(request_id.encode()).hexdigest()[:8], 16) % (2**31 - 1)


def validate_response_record(
    row: dict[str, Any], manifest_by_id: dict[str, dict[str, Any]]
) -> tuple[list[str], dict[str, Any]]:
    errors: list[str] = []
    request_id = row.get("request_id")
    episode_id = row.get("episode_id")
    replicate = row.get("replicate")
    episode = manifest_by_id.get(str(episode_id))
    if episode is None:
        errors.append("unknown episode_id")
        return errors, {"request_id": request_id, "verdict": "missing"}
    expected_id = f"{episode_id}__{replicate}"
    if request_id != expected_id:
        errors.append("request_id does not equal episode_id plus replicate")
    if replicate not in REPLICATES:
        errors.append("unknown replicate")
    request = row.get("request") or {}
    image = STUDY / episode["image_path"]
    expected_request = {
        "model": "Holo-3.1-4B",
        "temperature": 0.0 if replicate == "t0" else 0.8,
        "top_p": 1.0,
        "top_k": -1,
        "presence_penalty": 0.0,
        "frequency_penalty": 0.0,
        "repetition_penalty": 1.0,
        "seed": request_seed(str(request_id)),
        "max_tokens": 4096,
        "stream": False,
        "chat_template_kwargs": {"enable_thinking": True},
        "prompt": PROMPT.format(instruction=episode["instruction"]),
        "image_path": episode["image_path"],
        "image_sha256": episode["screenshot_sha256"],
    }
    image_bytes = image.read_bytes() if image.is_file() else b""
    expected_payload = {
        "model": "Holo-3.1-4B",
        "messages": [
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": expected_request["prompt"]},
                    {
                        "type": "image_url",
                        "image_url": {
                            "url": "data:image/png;base64,"
                            + base64.b64encode(image_bytes).decode()
                        },
                    },
                ],
            }
        ],
        "temperature": expected_request["temperature"],
        "top_p": 1.0,
        "top_k": -1,
        "presence_penalty": 0.0,
        "frequency_penalty": 0.0,
        "repetition_penalty": 1.0,
        "seed": expected_request["seed"],
        "max_tokens": 4096,
        "stream": False,
        "chat_template_kwargs": {"enable_thinking": True},
    }
    expected_request["request_body_sha256"] = hashlib.sha256(
        json.dumps(expected_payload, ensure_ascii=False).encode()
    ).hexdigest()
    for key, expected in expected_request.items():
        if request.get(key) != expected:
            errors.append(f"request.{key} mismatch")
    if not image.is_file() or digest(image) != request.get("image_sha256"):
        errors.append("request image file/hash mismatch")
    if row.get("status") != "ok":
        errors.append(f"non-ok final status: {row.get('status')}")

    response = row.get("response") or {}
    if response.get("model") != "Holo-3.1-4B":
        errors.append("response model mismatch")
    choices = response.get("choices")
    if not isinstance(choices, list) or len(choices) != 1:
        errors.append("response does not have exactly one choice")
        message: dict[str, Any] = {}
        finish_reason = None
    else:
        message = choices[0].get("message") or {}
        finish_reason = choices[0].get("finish_reason")
    content = message.get("content")
    reasoning = message.get("reasoning")
    if reasoning is None:
        reasoning = message.get("reasoning_content")
    verdict, verdict_matches = classify_verdict(
        content, status=row.get("status"), finish_reason=finish_reason
    )
    decisions, requirement_format = explicit_requirement_decisions(content)
    return errors, {
        "request_id": request_id,
        "episode_id": episode_id,
        "task_key": f"{episode['domain']}__{episode['task_id']}",
        "label": episode["label"],
        "replicate": replicate,
        "verdict": verdict,
        "verdict_matches": verdict_matches,
        "finish_reason": finish_reason,
        "content_length": len(content) if isinstance(content, str) else 0,
        "reasoning_length": len(reasoning) if isinstance(reasoning, str) else 0,
        "requirement_decisions": dict(decisions),
        "requirement_format": requirement_format,
    }


def rate_table(records: list[dict[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for label in ("false_success", "true_success"):
        rows = [row for row in records if row["label"] == label]
        counts = Counter(row["verdict"] for row in rows)
        incomplete = counts["incomplete"]
        valid = counts["incomplete"] + counts["complete"]
        result[label] = {
            "denominator_all": len(rows),
            "verdict_counts": dict(counts),
            "incomplete_rate_all": incomplete / len(rows) if rows else None,
            "incomplete_wilson95_all": wilson(incomplete, len(rows)),
            "denominator_valid": valid,
            "incomplete_rate_valid": incomplete / valid if valid else None,
            "incomplete_wilson95_valid": wilson(incomplete, valid),
            "finish_reason_counts": dict(Counter(row.get("finish_reason") for row in rows)),
        }
    return result


def cluster_bootstrap(
    records: list[dict[str, Any]], iterations: int = 20_000, seed: int = 20261108
) -> dict[str, Any]:
    by_task: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in records:
        by_task[row["task_key"]].append(row)
    keys = sorted(by_task)
    rng = random.Random(seed)
    draws: dict[str, list[float]] = {
        "false_success": [],
        "true_success": [],
        "detection_minus_false_rejection": [],
    }
    for _ in range(iterations):
        sampled_rows: list[dict[str, Any]] = []
        for _index in keys:
            sampled_rows.extend(by_task[rng.choice(keys)])
        sample_rates: dict[str, float] = {}
        for label in ("false_success", "true_success"):
            labeled = [row for row in sampled_rows if row["label"] == label]
            if labeled:
                rate = sum(row["verdict"] == "incomplete" for row in labeled) / len(labeled)
                draws[label].append(rate)
                sample_rates[label] = rate
        if len(sample_rates) == 2:
            draws["detection_minus_false_rejection"].append(
                sample_rates["false_success"] - sample_rates["true_success"]
            )
    result: dict[str, Any] = {"iterations": iterations, "seed": seed, "cluster_count": len(keys)}
    for label, values in draws.items():
        values.sort()
        if values:
            low = values[math.floor(0.025 * (len(values) - 1))]
            high = values[math.ceil(0.975 * (len(values) - 1))]
            result[label] = [low, high]
        else:
            result[label] = None
    return result


def audit_branch_pilot() -> dict[str, Any]:
    roots = {
        "original": Path("/home/orbit/osw/branch_pilot/orig/branches.jsonl"),
        "candidate": Path("/home/orbit/osw/branch_pilot/cand/branches.jsonl"),
    }
    arm_rows = {arm: load_jsonl(path) for arm, path in roots.items()}
    summaries: dict[str, Any] = {}
    for arm, rows in arm_rows.items():
        enriched = []
        for row in rows:
            domain, task_id = row["task"].split("/", 1)
            task = load_json(TASKS / domain / f"{task_id}.json")
            infeasible = "infeasible" in json.dumps(
                task.get("evaluator", {}).get("func")
            ).lower()
            enriched.append(
                {
                    **row,
                    "domain": domain,
                    "task_id": task_id,
                    "infeasible": infeasible,
                    "replay_valid": row["replay_diff_max"] <= 0.05,
                    "success": row["score"] == 1,
                }
            )

        def count(predicate: Any) -> dict[str, Any]:
            selected = [row for row in enriched if predicate(row)]
            successes = sum(row["success"] for row in selected)
            return {
                "successes": successes,
                "denominator": len(selected),
                "rate": successes / len(selected) if selected else None,
                "nominal_wilson95": wilson(successes, len(selected)),
            }

        summaries[arm] = {
            "source": str(roots[arm]),
            "sha256": digest(roots[arm]),
            "all": count(lambda row: True),
            "recorded_failures_raw": count(lambda row: row["recorded_score"] == 0),
            "recorded_failures_replay_valid": count(
                lambda row: row["recorded_score"] == 0 and row["replay_valid"]
            ),
            "recorded_failures_replay_valid_feasible": count(
                lambda row: row["recorded_score"] == 0
                and row["replay_valid"]
                and not row["infeasible"]
            ),
            "recorded_successes_replay_valid": count(
                lambda row: row["recorded_score"] == 1 and row["replay_valid"]
            ),
            "distinct_task_count": len({row["task"] for row in enriched}),
            "error_count": sum(bool(row.get("error")) for row in enriched),
        }
    return {
        "arms": summaries,
        "fidelity_threshold": 0.05,
        "uncertainty_warning": (
            "Wilson intervals are nominal only: K=2 continuations from each task are clustered; "
            "the feasible-failure subset contains one task, so task-level uncertainty is not estimable."
        ),
        "transfer_warning": (
            "The only original-arm repair is on an officially infeasible GIMP task excluded from the verifier corpus."
        ),
    }


def audit_requirement_review(
    responses_path: Path, review_path: Path
) -> dict[str, Any]:
    review = load_json(review_path)
    raw_lines = responses_path.read_bytes().splitlines(keepends=True)
    selected_lines: list[bytes] = []
    rows: dict[str, dict[str, Any]] = {}
    for raw_line in raw_lines:
        row = json.loads(raw_line)
        if str(row.get("request_id", "")).endswith("__t0"):
            selected_lines.append(raw_line)
            rows[row["request_id"]] = row
    selected_hash = hashlib.sha256(b"".join(selected_lines)).hexdigest()
    errors: list[str] = []
    expected_hash = review["source"]["selected_t0_raw_lines_sha256"]
    if selected_hash != expected_hash:
        errors.append("selected T0 raw-line SHA256 differs from semantic review")
    if len(rows) != 268 or len(selected_lines) != 268:
        errors.append("semantic review does not resolve to exactly 268 unique T0 rows")

    decisions_by_request: dict[str, list[dict[str, Any]]] = {}
    for request_id, row in rows.items():
        choices = (row.get("response") or {}).get("choices") or []
        content = (
            choices[0].get("message", {}).get("content") if len(choices) == 1 else None
        )
        decisions_by_request[request_id] = requirement_decision_items(content)
    base_totals = Counter(
        item["decision"]
        for decisions in decisions_by_request.values()
        for item in decisions
    )

    correction_ids = [item["request_id"] for item in review["corrections"]]
    if len(correction_ids) != len(set(correction_ids)):
        errors.append("semantic review contains duplicate correction request IDs")
    for correction in review["corrections"]:
        request_id = correction["request_id"]
        if request_id not in rows:
            errors.append(f"{request_id}: correction request missing from T0 rows")
            continue
        decisions = decisions_by_request[request_id]
        initial = Counter(item["decision"] for item in decisions)
        expected_initial = Counter(correction["parser_counts"])
        if initial != expected_initial:
            errors.append(
                f"{request_id}: parser counts differ: {dict(initial)} != {dict(expected_initial)}"
            )
        content = rows[request_id]["response"]["choices"][0]["message"].get("content") or ""
        content_lines = content.splitlines()
        for operation in correction["operations"]:
            line_number = operation["content_line"]
            actual_text = (
                content_lines[line_number - 1].strip()
                if 0 < line_number <= len(content_lines)
                else None
            )
            if actual_text != operation["text"].strip():
                errors.append(f"{request_id}:{line_number}: raw line text mismatch")
                continue
            if operation["op"] in {"remove", "change", "split_compound_line"}:
                old = operation.get("from", operation.get("decision"))
                matches = [
                    index
                    for index, item in enumerate(decisions)
                    if item["line_number"] == line_number and item["decision"] == old
                ]
                if len(matches) != 1:
                    errors.append(
                        f"{request_id}:{line_number}: expected one removable {old}, got {len(matches)}"
                    )
                else:
                    decisions.pop(matches[0])
            if operation["op"] in {"add", "change", "split_compound_line"}:
                label = operation.get("to", operation.get("decision"))
                count = operation.get("audited_count", 1)
                for ordinal in range(count):
                    decisions.append(
                        {
                            "decision": label,
                            "line_number": line_number,
                            "text": operation["text"],
                            "ordinal": ordinal + 1,
                        }
                    )
        final = Counter(item["decision"] for item in decisions)
        expected_final = Counter(correction["audited_counts"])
        if final != expected_final:
            errors.append(
                f"{request_id}: audited counts differ: {dict(final)} != {dict(expected_final)}"
            )

    audited_totals = Counter(
        item["decision"]
        for decisions in decisions_by_request.values()
        for item in decisions
    )
    expected_totals = Counter(
        {
            key: review["counts"]["strict_audited_distinct_model_listed_requirements"][key]
            for key in ("yes", "no", "cannot tell")
        }
    )
    if audited_totals != expected_totals:
        errors.append(
            f"semantic totals differ: {dict(audited_totals)} != {dict(expected_totals)}"
        )
    manifest = {row["episode_id"]: row for row in load_json(STUDY / "manifest.json")}
    subgroup: dict[str, Counter[str]] = defaultdict(Counter)
    for request_id, decisions in decisions_by_request.items():
        episode_id = request_id[: -len("__t0")]
        label = manifest[episode_id]["label"]
        subgroup[label].update(item["decision"] for item in decisions)
    return {
        "review_path": str(review_path),
        "review_sha256": digest(review_path),
        "selected_t0_raw_lines_sha256": selected_hash,
        "selected_t0_rows": len(selected_lines),
        "correction_count": len(correction_ids),
        "base_parser_totals": dict(base_totals),
        "audited_totals": dict(audited_totals),
        "audited_subgroup_totals": {
            label: dict(counts) for label, counts in subgroup.items()
        },
        "errors": errors,
        "interpretation": (
            "Counts are explicit model-emitted requirement ratings after a semantic formatting audit; "
            "they do not measure whether the ratings are correct."
        ),
    }
def audit_attempts(path: Path, final_rows: list[dict[str, Any]]) -> dict[str, Any]:
    attempts = load_jsonl(path)
    by_request: dict[str, list[dict[str, Any]]] = defaultdict(list)
    errors: list[str] = []
    intervals: list[tuple[float, int]] = []
    finish_times: list[float] = []
    deadline = datetime.fromisoformat("2026-11-08T09:45:00+00:00").timestamp()
    raw_response_mismatches = 0
    for row in attempts:
        request_id = str(row.get("request_id"))
        by_request[request_id].append(row)
        try:
            started = datetime.fromisoformat(row["started_at"]).timestamp()
            finished = datetime.fromisoformat(row["finished_at"]).timestamp()
            if finished < started:
                errors.append(f"{request_id}: finished before started")
            intervals.extend([(started, 1), (finished, -1)])
            finish_times.append(finished)
        except (KeyError, TypeError, ValueError):
            errors.append(f"{request_id}: invalid attempt timestamps")
        if row.get("status") == "ok":
            try:
                if json.loads(row.get("response_raw", "")) != row.get("response"):
                    raw_response_mismatches += 1
            except (TypeError, json.JSONDecodeError):
                raw_response_mismatches += 1
    final_by_id = {str(row.get("request_id")): row for row in final_rows}
    retry_count = 0
    final_copy_mismatches = 0
    for request_id, rows in by_request.items():
        rows.sort(key=lambda row: row.get("attempt", 0))
        attempt_numbers = [row.get("attempt") for row in rows]
        if attempt_numbers not in ([1], [1, 2]):
            errors.append(f"{request_id}: attempt sequence {attempt_numbers}")
        if len(rows) == 2:
            retry_count += 1
            if rows[0].get("status") != "transport_error":
                errors.append(f"{request_id}: retry did not follow a transport error")
        if request_id in final_by_id and rows[-1] != final_by_id[request_id]:
            final_copy_mismatches += 1
    missing_attempt_for_final = sorted(set(final_by_id) - set(by_request))
    final_missing_from_attempts = sorted(set(by_request) - set(final_by_id))
    active = 0
    max_concurrency = 0
    for _timestamp, delta in sorted(intervals, key=lambda item: (item[0], item[1])):
        active += delta
        max_concurrency = max(max_concurrency, active)
    finish_times.sort()
    max_progress_gap = max(
        (right - left for left, right in zip(finish_times, finish_times[1:])), default=0.0
    )
    return {
        "path": str(path),
        "sha256": digest(path),
        "attempt_record_count": len(attempts),
        "logical_request_count": len(by_request),
        "attempt_count_distribution": dict(
            Counter(str(len(rows)) for rows in by_request.values())
        ),
        "retry_count": retry_count,
        "max_observed_concurrent_attempts": max_concurrency,
        "max_seconds_between_attempt_completions": max_progress_gap,
        "attempts_started_at_or_after_deadline": sum(
            datetime.fromisoformat(row["started_at"]).timestamp() >= deadline
            for row in attempts
        ),
        "attempts_finished_after_deadline": sum(
            datetime.fromisoformat(row["finished_at"]).timestamp() > deadline
            for row in attempts
        ),
        "raw_response_json_mismatch_count": raw_response_mismatches,
        "final_copy_mismatch_count": final_copy_mismatches,
        "missing_attempt_for_final_request_ids": missing_attempt_for_final,
        "attempt_request_ids_without_final_row": final_missing_from_attempts,
        "errors": errors,
    }


def audit_responses(path: Path, branch_pilot: dict[str, Any]) -> dict[str, Any]:
    manifest = load_json(STUDY / "manifest.json")
    manifest_by_id = {row["episode_id"]: row for row in manifest}
    raw_rows = load_jsonl(path)
    expected_ids = {
        f"{episode['episode_id']}__{replicate}"
        for episode in manifest
        for replicate in REPLICATES
    }
    actual_ids = [str(row.get("request_id")) for row in raw_rows]
    duplicate_ids = sorted(key for key, count in Counter(actual_ids).items() if count > 1)
    unexpected_ids = sorted(set(actual_ids) - expected_ids)
    missing_ids = sorted(expected_ids - set(actual_ids))
    validation_errors: list[dict[str, Any]] = []
    parsed: list[dict[str, Any]] = []
    for row in raw_rows:
        errors, parsed_row = validate_response_record(row, manifest_by_id)
        if errors:
            validation_errors.append({"request_id": row.get("request_id"), "errors": errors})
        episode = manifest_by_id.get(str(parsed_row.get("episode_id")))
        if episode:
            meta_path = Path(episode["source_dir"]) / "meta.json"
            meta = load_json(meta_path) if meta_path.is_file() else {}
            parsed_row["model_declared_infeasible"] = meta.get(
                "model_declared_infeasible", False
            )
        parsed.append(parsed_row)

    by_replicate = {
        replicate: rate_table([row for row in parsed if row["replicate"] == replicate])
        for replicate in REPLICATES
    }
    by_episode: dict[str, dict[str, dict[str, Any]]] = defaultdict(dict)
    for row in parsed:
        by_episode[str(row["episode_id"])][str(row["replicate"])] = row
    majority_rows: list[dict[str, Any]] = []
    unanimous = 0
    complete_triplets = 0
    comparable_pairs = 0
    disagreeing_pairs = 0
    for episode_id, episode in manifest_by_id.items():
        rows = by_episode.get(episode_id, {})
        t08 = [rows.get(name) for name in REPLICATES[1:]]
        verdicts = [row["verdict"] if row else "missing" for row in t08]
        vote_counts = Counter(verdict for verdict in verdicts if verdict in {"complete", "incomplete"})
        if vote_counts["complete"] >= 2:
            majority = "complete"
        elif vote_counts["incomplete"] >= 2:
            majority = "incomplete"
        else:
            majority = "missing"
        if all(row is not None for row in t08):
            complete_triplets += 1
        if len(verdicts) == 3 and verdicts[0] in {"complete", "incomplete"} and len(set(verdicts)) == 1:
            unanimous += 1
        for left in range(3):
            for right in range(left + 1, 3):
                if verdicts[left] in {"complete", "incomplete"} and verdicts[right] in {"complete", "incomplete"}:
                    comparable_pairs += 1
                    disagreeing_pairs += verdicts[left] != verdicts[right]
        majority_rows.append(
            {
                "episode_id": episode_id,
                "task_key": f"{episode['domain']}__{episode['task_id']}",
                "label": episode["label"],
                "verdict": majority,
                "t0_verdict": rows.get("t0", {}).get("verdict", "missing"),
                "t08_verdicts": verdicts,
                "all_three_valid": all(
                    verdict in {"complete", "incomplete"} for verdict in verdicts
                ),
                "unanimous": (
                    len(verdicts) == 3
                    and verdicts[0] in {"complete", "incomplete"}
                    and len(set(verdicts)) == 1
                ),
                "valid_pair_count": sum(
                    verdicts[left] in {"complete", "incomplete"}
                    and verdicts[right] in {"complete", "incomplete"}
                    for left in range(3)
                    for right in range(left + 1, 3)
                ),
                "pair_disagreement_count": sum(
                    verdicts[left] in {"complete", "incomplete"}
                    and verdicts[right] in {"complete", "incomplete"}
                    and verdicts[left] != verdicts[right]
                    for left in range(3)
                    for right in range(left + 1, 3)
                ),
            }
        )
    comparable_majority_t0 = [
        row
        for row in majority_rows
        if row["verdict"] in {"complete", "incomplete"}
        and row["t0_verdict"] in {"complete", "incomplete"}
    ]
    stability_by_label: dict[str, Any] = {}
    for label in ("all", "false_success", "true_success"):
        selected = [
            row for row in majority_rows if label == "all" or row["label"] == label
        ]
        valid_triplets = [row for row in selected if row["all_three_valid"]]
        comparable = [
            row
            for row in selected
            if row["verdict"] in {"complete", "incomplete"}
            and row["t0_verdict"] in {"complete", "incomplete"}
        ]
        pair_count = sum(row["valid_pair_count"] for row in selected)
        pair_disagreement = sum(
            row["pair_disagreement_count"] for row in selected
        )
        stability_by_label[label] = {
            "episodes": len(selected),
            "all_three_valid": len(valid_triplets),
            "unanimous_count": sum(row["unanimous"] for row in selected),
            "unanimity_rate_all": (
                sum(row["unanimous"] for row in selected) / len(selected)
                if selected
                else None
            ),
            "unanimity_rate_valid_triplets": (
                sum(row["unanimous"] for row in valid_triplets) / len(valid_triplets)
                if valid_triplets
                else None
            ),
            "pairwise_comparison_count": pair_count,
            "pairwise_disagreement_count": pair_disagreement,
            "pairwise_disagreement_rate": (
                pair_disagreement / pair_count if pair_count else None
            ),
            "majority_t0_comparable_count": len(comparable),
            "majority_t0_agreement_count": sum(
                row["verdict"] == row["t0_verdict"] for row in comparable
            ),
            "majority_t0_agreement_rate": (
                sum(row["verdict"] == row["t0_verdict"] for row in comparable)
                / len(comparable)
                if comparable
                else None
            ),
        }

    t0_rows = [row for row in parsed if row["replicate"] == "t0"]
    t0_false_without_declared_infeasible = [
        row
        for row in t0_rows
        if row["label"] == "false_success" and not row.get("model_declared_infeasible")
    ]
    decision_counts: Counter[str] = Counter()
    format_counts: Counter[str] = Counter()
    for row in t0_rows:
        decision_counts.update(row["requirement_decisions"])
        format_counts[row["requirement_format"]] += 1

    false_incomplete = sum(
        row["label"] == "false_success" and row["verdict"] == "incomplete"
        for row in t0_rows
    )
    true_incomplete = sum(
        row["label"] == "true_success" and row["verdict"] == "incomplete"
        for row in t0_rows
    )
    false_total = sum(row["label"] == "false_success" for row in t0_rows)
    true_total_observed = sum(row["label"] == "true_success" for row in t0_rows)
    attempts_audit = (
        audit_attempts(STUDY / "attempts.jsonl", raw_rows)
        if (STUDY / "attempts.jsonl").is_file()
        else None
    )
    selected_n = len(manifest)
    baseline_successes = sum(row["label"] == "true_success" for row in manifest)
    original_branch = branch_pilot["arms"]["original"]
    conditional_scenarios: dict[str, Any] = {}
    for name, branch_key in (
        ("feasible_replay_valid", "recorded_failures_replay_valid_feasible"),
        ("naive_all_replay_valid", "recorded_failures_replay_valid"),
    ):
        branch_rate = original_branch[branch_key]
        repair_rate = branch_rate["rate"] or 0.0
        expected_repairs = false_incomplete * repair_rate
        conditional_scenarios[name] = {
            "branch_evidence": branch_rate,
            "expected_repairs_not_observed": expected_repairs,
            "net_change_if_true_successes_preserved": expected_repairs,
            "net_change_if_all_flagged_true_successes_lost": (
                expected_repairs - true_incomplete
            ),
            "gain_pp_if_true_successes_preserved": 100 * expected_repairs / selected_n,
            "gain_pp_if_all_flagged_true_successes_lost": (
                100 * (expected_repairs - true_incomplete) / selected_n
            ),
        }
    all_saved = all_scored_feasible_inventory()
    all_saved_n = all_saved["feasible_scored_episode_count"]
    all_saved_sum = all_saved["official_score_sum"]
    all_saved_scenarios = {
        name: {
            "expected_repairs_not_observed": scenario["expected_repairs_not_observed"],
            "gain_pp_if_true_successes_preserved": (
                100 * scenario["expected_repairs_not_observed"] / all_saved_n
            ),
            "gain_pp_if_all_flagged_true_successes_lost": (
                100
                * (scenario["expected_repairs_not_observed"] - true_incomplete)
                / all_saved_n
            ),
            "score_mean_if_true_successes_preserved": (
                all_saved_sum + scenario["expected_repairs_not_observed"]
            )
            / all_saved_n,
            "score_mean_if_all_flagged_true_successes_lost": (
                all_saved_sum
                + scenario["expected_repairs_not_observed"]
                - true_incomplete
            )
            / all_saved_n,
        }
        for name, scenario in conditional_scenarios.items()
    }
    return {
        "responses_path": str(path),
        "responses_sha256": digest(path),
        "protocol_sha256": digest(STUDY / "PROTOCOL.md"),
        "prepare_sha256": digest(STUDY / "prepare.py"),
        "runner_sha256": digest(STUDY / "run_verifier.py"),
        "raw_record_count": len(raw_rows),
        "expected_record_count": len(expected_ids),
        "missing_request_count": len(missing_ids),
        "missing_request_ids": missing_ids,
        "unexpected_request_ids": unexpected_ids,
        "duplicate_request_ids": duplicate_ids,
        "validation_error_count": len(validation_errors),
        "validation_errors": validation_errors,
        "response_model_counts": dict(
            Counter((row.get("response") or {}).get("model") for row in raw_rows)
        ),
        "status_counts": dict(Counter(row.get("status") for row in raw_rows)),
        "attempt_counts": dict(Counter(str(row.get("attempt")) for row in raw_rows)),
        "attempts_audit": attempts_audit,
        "reasoning_nonempty_count": sum(row["reasoning_length"] > 0 for row in parsed),
        "finish_reason_counts": dict(Counter(row["finish_reason"] for row in parsed)),
        "by_replicate": by_replicate,
        "t08_majority": rate_table(majority_rows),
        "t08_complete_triplet_count": complete_triplets,
        "t08_unanimous_count": unanimous,
        "t08_unanimity_rate_all_episodes": unanimous / len(manifest) if manifest else None,
        "t08_pairwise_comparable_count": comparable_pairs,
        "t08_pairwise_disagreement_count": disagreeing_pairs,
        "t08_pairwise_disagreement_rate": (
            disagreeing_pairs / comparable_pairs if comparable_pairs else None
        ),
        "majority_t0_comparable_count": len(comparable_majority_t0),
        "majority_t0_agreement_count": sum(
            row["verdict"] == row["t0_verdict"] for row in comparable_majority_t0
        ),
        "majority_t0_agreement_rate": (
            sum(row["verdict"] == row["t0_verdict"] for row in comparable_majority_t0)
            / len(comparable_majority_t0)
            if comparable_majority_t0
            else None
        ),
        "stability_by_label": stability_by_label,
        "t0_requirement_decision_counts": dict(decision_counts),
        "t0_requirement_format_counts": dict(format_counts),
        "t0_cluster_bootstrap95": cluster_bootstrap(t0_rows),
        "t0_detection_minus_false_rejection": (
            false_incomplete / false_total - true_incomplete / true_total_observed
            if false_total and true_total_observed
            else None
        ),
        "posthoc_metadata_sensitivity": {
            "definition": (
                "Exclude score-0 answer episodes whose pre-existing meta.json marks "
                "model_declared_infeasible=true; primary retains them under the registered last-answer rule."
            ),
            "excluded_episode_ids": [
                row["episode_id"]
                for row in t0_rows
                if row["label"] == "false_success" and row.get("model_declared_infeasible")
            ],
            "false_success_metrics_after_exclusion": rate_table(
                t0_false_without_declared_infeasible
            )["false_success"],
        },
        "blocking_only_simulation": {
            "false_successes_flagged_but_not_repaired": false_incomplete,
            "true_successes_flagged_and_potentially_blocked": true_incomplete,
            "measured_repairs": 0,
            "hard_block_net_success_change": -true_incomplete,
            "best_case_if_true_successes_are_not_damaged": 0,
            "baseline_successes": baseline_successes,
            "baseline_success_rate": baseline_successes / selected_n,
            "conditional_repair_extrapolation": conditional_scenarios,
            "all_scored_feasible_denominator_sensitivity": {
                "population": all_saved,
                "assumption": (
                    "Hold every episode outside the 268 verified answer episodes unchanged and apply "
                    "repairs/damage only to verified episodes."
                ),
                "scenarios": all_saved_scenarios,
            },
            "limits": [
                branch_pilot["uncertainty_warning"],
                branch_pilot["transfer_warning"],
                "Blocking alone repairs zero tasks; extrapolated repairs are not measured OSWorld improvement.",
                "The 268 selected answer episodes are not the full benchmark.",
            ],
        },
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--responses", type=Path, default=STUDY / "responses.jsonl")
    parser.add_argument("--no-responses", action="store_true")
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    raw_inventory, raw_selected = source_inventory()
    branch_pilot = audit_branch_pilot()
    report: dict[str, Any] = {
        "corpus": compare_corpus(raw_inventory, raw_selected),
        "branch_pilot": branch_pilot,
    }
    requirement_review = STUDY / "audit/requirement_review.json"
    if requirement_review.is_file() and args.responses.is_file():
        report["requirement_review"] = audit_requirement_review(
            args.responses, requirement_review
        )
    if not args.no_responses and args.responses.is_file():
        report["responses"] = audit_responses(args.responses, branch_pilot)
    rendered = json.dumps(report, indent=2, ensure_ascii=False, sort_keys=True) + "\n"
    if args.output:
        output = args.output.resolve()
        audit_root = (STUDY / "audit").resolve()
        if audit_root not in output.parents:
            raise SystemExit(f"Audit output must be under {audit_root}")
        output.write_text(rendered)
    print(rendered, end="")


if __name__ == "__main__":
    main()
