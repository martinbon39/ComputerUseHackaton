#!/usr/bin/env python3
"""Retrospective attribution-budget audit.

This reconstructs preserved runs after the fact. It was not an active interlock
during any pilot or attribution run and cannot retroactively enforce a stop.
"""

import json
import sys
from pathlib import Path


LEDGER = Path(__file__).with_name("attribution_attempts.json")
ALLOWED_COUNT_TYPES = {"observed", "inferred"}
ALLOWED_GATE_RESULTS = {"PASS", "FAIL"}


def fail(errors, message):
    errors.append(message)
    print(f"FAIL: {message}")


def main():
    errors = []
    data = json.loads(LEDGER.read_text(encoding="utf-8"))
    attempts = data.get("attempts", [])

    print("RETROSPECTIVE ONLY: this audit was not an active interlock during the experiments.")

    if data.get("retrospective_only") is not True:
        fail(errors, "ledger must declare retrospective_only=true")
    if data.get("active_interlock_during_experiment") is not False:
        fail(errors, "ledger must declare active_interlock_during_experiment=false")
    if not attempts:
        fail(errors, "ledger contains no attempts")
        return 1

    orders = [row.get("order") for row in attempts]
    if orders != list(range(1, len(attempts) + 1)):
        fail(errors, f"attempt order is not contiguous: {orders!r}")
    ids = [row.get("id") for row in attempts]
    if len(ids) != len(set(ids)):
        fail(errors, "attempt ids are not unique")

    for row in attempts:
        if not isinstance(row.get("forward_attempts"), int) or row["forward_attempts"] < 0:
            fail(errors, f"{row.get('id')}: invalid forward_attempts")
        if row.get("count_type") not in ALLOWED_COUNT_TYPES:
            fail(errors, f"{row.get('id')}: invalid count_type")
        if row.get("gate_result") not in ALLOWED_GATE_RESULTS:
            fail(errors, f"{row.get('id')}: invalid gate_result")
        if not isinstance(row.get("execution_progress"), bool):
            fail(errors, f"{row.get('id')}: execution_progress must be boolean")
        if not row.get("guard_id"):
            fail(errors, f"{row.get('id')}: missing guard_id")

    total = sum(row["forward_attempts"] for row in attempts)
    expected = data.get("expected_total_forward_attempts")
    global_cap = data.get("caps", {}).get("all_attribution_forward_attempts")
    main_cap = data.get("caps", {}).get("main_attribution_forward_attempts")
    main_rows = [row for row in attempts if row.get("run_kind") == "main"]

    print(f"TOTAL: {total} forward attempts (expected {expected}; cap {global_cap})")
    if total != expected:
        fail(errors, f"recomputed total {total} != declared expected total {expected}")
    elif total > global_cap:
        fail(errors, f"global attribution cap exceeded: {total} > {global_cap}")
    else:
        print(f"PASS: global forward cap, {total} <= {global_cap} (headroom {global_cap-total})")

    if len(main_rows) != 1:
        fail(errors, f"expected one main run, found {len(main_rows)}")
    else:
        main_count = main_rows[0]["forward_attempts"]
        if main_count > main_cap:
            fail(errors, f"main attribution cap exceeded: {main_count} > {main_cap}")
        else:
            print(f"PASS: main forward cap, {main_count} <= {main_cap} (headroom {main_cap-main_count})")

    required_stop_at = None
    consecutive_guard = None
    no_progress_failures = 0
    for index, row in enumerate(attempts):
        same_failed_guard = (
            row["gate_result"] == "FAIL"
            and row["execution_progress"] is False
            and row["guard_id"] == consecutive_guard
        )
        if row["gate_result"] == "FAIL" and row["execution_progress"] is False:
            no_progress_failures = no_progress_failures + 1 if same_failed_guard else 1
            consecutive_guard = row["guard_id"]
        else:
            no_progress_failures = 0
            consecutive_guard = None
        if no_progress_failures >= 2:
            required_stop_at = index
            break

    if required_stop_at is None:
        print("PASS: no two consecutive same-guard failures without execution progress")
    else:
        trigger = attempts[required_stop_at]
        later = [row["id"] for row in attempts[required_stop_at + 1 :] if row["forward_attempts"] > 0]
        if later:
            fail(
                errors,
                "required stop was not honored after two consecutive failures of "
                f"guard {trigger['guard_id']!r} without execution progress; "
                f"second failure={trigger['id']!r}; later model runs={later!r}",
            )
        else:
            print(f"PASS: required stop honored after {trigger['id']}")

    if errors:
        print(f"AUDIT RESULT: FAIL ({len(errors)} issue(s)); numeric caps may still pass independently.")
        return 1
    print("AUDIT RESULT: PASS")
    return 0


if __name__ == "__main__":
    sys.exit(main())
