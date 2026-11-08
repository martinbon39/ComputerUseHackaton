# Rescue runner — independent verification

Verified 2026-11-08 before the live pilot. The reviewer did not author `feci_guard/rescue_runner.py` and did not call an endpoint or start a VM.

## Verdict

**RAN:** CPU import/compile, shell syntax, all frozen SHA-256 checks, all 12 episode preconditions from the enforced OSWorld working directory, MRO/dispatch assertions, and mocked control / Guard-pass / Guard-refusal calls.

**PASSED:** all checks above, plus the second and final correction review for path normalization and durable-result recovery. The runner is safe to run the registered pilot.

**CORRECT:**

- MRO is `RescueAgent → BranchAgent → GuardedAgent → HoloComputerAgent`. `BranchAgent` inherits the frozen `_call_model`; its frozen replay loop calls `self._call_model`, so the rescue override gates the boundary and delegates actual generation through the frozen Holo call.
- The control invokes no Guard and receives no feedback. A Guard pass/fail-open returns the recorded terminal answer with zero Holo4 calls. A Guard refusal inserts the recorded answer followed by Guard feedback and a fresh observation before the first Holo4 call. The Guard is not applied again.
- `max_new` is capped at 20, replay fidelity and boundary fidelity are recorded separately, and scoring uses OSWorld `DONE`/`FAIL`, the registered settle delay, then official `env.evaluate()`.
- The runner resolves `--out`, `--episodes`, and `--key_file` before changing to the OSWorld runtime directory. It then validates every frozen source hash before tasks, gates memory and VM count, preserves two attempt directories per slot, skips successful slots, and retains the paired pilot gate.
- Resume scans `*/*/attempt_*/result.json` before launch. A durable successful result missing from `branches.jsonl` is appended with `recovered_from` provenance and added to `completed`, so it is not rerun after a crash between result persistence and journal append.
- `BranchTimeout` derives from `BaseException`, so the frozen `except Exception` retry loops cannot swallow the deadline. The outer runner catches it explicitly and closes the environment in `finally`.

**NOT RUN:** Holo4 or Claude network calls, Docker/KVM, desktop execution, official evaluation, and the live pilot.

## CPU evidence

- `/home/orbit/osw/venv/bin/python -m py_compile feci_guard/rescue_runner.py`: pass.
- `bash -n rescue_bench/run.sh`: pass.
- Frozen manifest: 9/9 current SHA-256 values match.
- Episode validation: 12/12 pass from `/home/orbit/osw/rtg/Env/OSWorld`.
- Mock dispatch: control, Guard pass, and Guard refusal all pass; only control/refusal reached the stub standing in for frozen Holo generation, and only refusal contained Guard feedback.
- Round 2/2: path resolution occurs before `chdir`; the recovery glob matches the actual `arm/slot/attempt_N/result.json` layout, ignores already journaled successes, journals an unindexed durable result once, and marks its `(task, arm, k)` slot complete before pilot/full scheduling.

## Residual limitations

The recovery reader assumes that every existing `result.json` is complete valid JSON. A timeout or process death during the small non-atomic `write_text` window could leave a partial file; on resume, `json.loads` would stop startup before the registered retry. This is a narrow crash-recovery limitation rather than a normal pilot-path defect. Hardening would write through a temporary file plus `os.replace`, or ignore/quarantine invalid result files while retaining their failed attempt directory.
