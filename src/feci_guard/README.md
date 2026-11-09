# Feci Guard

The fix our paper ("Cogito, Ergo Feci") recommends. A computer-use agent's false "done" is not repaired in the
weights. It needs an **external verifier** that checks every requirement of the task on the screen and tells the
agent what is missing.

Holo-3.1-4B judging its own work is at chance level: it catches 53 % of false successes and rejects 48 % of true ones.
So the verifier is a stronger model, Claude. Blocking a false "done" with no explanation repaired 0 of 2 feasible
false successes, so a refusal always says what is missing. **Results: `RESULTS.md`** (final). Protocols: `PREREG.md`
(v1, repair measure) and `v2/PROTOCOL.md` (sprint S1).

## How it works (v1, the version used online)
- `run_holo_guard.py` is a **copy** of the official `holo_repro/run_holo.py`; the original is never modified. The
  agent loop is the same as `HoloComputerAgent.run`, except at the terminal `answer`.
- On `answer` (unless the answer declares the task infeasible), the guard takes a fresh screenshot from the VM and
  calls `feci_guard.check(task, screenshot)`. The verifier (`verifier.py`) lists every requirement, gives each one
  yes/no/cannot_tell with its visual evidence, and returns COMPLETE or INCOMPLETE, plus the most important missing
  requirement and a next action. The output is strict JSON, with a 55 s timeout.
- **INCOMPLETE** (with at least one requirement "no") refuses the answer. As the answer's tool output, the agent gets
  `Verifier: requirement '…' is not satisfied on screen: <evidence>. <next action> Continue the task.`, and the
  episode goes on.
- **COMPLETE**, no verdict (timeout, error) or a self-contradictory verdict lets the answer through (fail-open).
- At most 2 refusals per episode; the 3rd answer passes unchecked.
- Each episode directory gets:
  - `guard.md`: the readable journal, with each requirement ✓/✗/? and its evidence, the decision, and the feedback
    sent;
  - `guard.jsonl`: the raw verdicts, with latency and cost;
  - `guard_step_N.png`: the screenshot that was checked;
  - a `feci_guard` summary in `meta.json`.
- Options: `--guard on|off`, `--guard_mode passive|active` (active: NEED_CHECK asks the agent for a read-only check
  first), `--guard_model`, `--guard_max_refusals`.
- Claude CLI location: `verifier.py` is frozen and finds the CLI through `FECI_CLAUDE`, which defaults to our server's
path (`/home/orbit/.local/bin/claude`). On your machine run `export FECI_CLAUDE=$(which claude)` first, otherwise every
check returns no verdict and, by the fail-open rule, every answer is accepted (`r["kind"] == "no_verdict"`).
`reproduce/guard_live.py` sets it for you. Judge backend from the environment:
  - `GUARD_BACKEND=claude` (local `claude -p`);
  - `openai`, for any OpenAI-compatible endpoint: `GUARD_BASE_URL`, `GUARD_MODEL`, and `GUARD_API_KEY_ENV` = the name
    of the variable holding the key. GitHub runs use the relay `guard_server.py` (127.0.0.1:9911,
    `GUARD_MODEL=claude-sonnet`).

## Files
| file | what |
|---|---|
| `verifier.py`, `feci_guard.py`, `run_holo_guard.py` | v1: verifier, the accept/reject rule (`check`), the guarded harness. **Frozen** (sha in PREREG.md). |
| `run_holo_guard_rescue.py` | v1 plus escalation: after the first refusal, the rest of the episode is played by `RESCUE_MODEL` (`RESCUE_BASE_URL`, `RESCUE_API_KEY_ENV`, `RESCUE_TIMEOUT_S`). |
| `verifier_v2.py`, `feci_guard_v2.py`, `run_holo_guard_v2.py`, `guard_server_v2.py` | v2 (Opus + history), with an optional `GUARD_V2_UNBLOCK=1` feedback hint; relay on 9912 (stopped: no online v2 arm). |
| `guard_server.py` | v1 relay for GitHub runners (written by ares). |
| `repair_runner.py`, `run_repair.sh`, `analyze_repair.py`, `repair/` | repair measure (guard arm; the no-guard arm is `../osworld/branch_runner.py`). |
| `compare_online.py`, `run_guard.sh`, `run_guard_rescue.sh` | online paired comparison and local launchers. |
| `v2/` | sprint S1: split, protocol, runs, scores. |
| `smoke/` | journals of the end-to-end runs. |
| `sync_to_runner.sh` | copies the guard files to holo-osworld-runner/feci_guard/ (the source of truth is here). |

```
bash run_guard.sh <result_dir> <tasks.json> <workers> [--guard off]      # guarded run_holo on orbit VMs
bash run_guard_rescue.sh <result_dir> <tasks.json> <workers>             # + escalation to Holo4-27B
python verifier.py --task "<instruction>" --image shot.png               # one manual check
python -c "import feci_guard; print(feci_guard.check(task, png_bytes))"  # library entry point
python analyze_repair.py ~/osw/feci_repair                               # repair measure analysis
python v2/score_v2.py holdout ab v1                                      # S1 scores
```

Demo sequence (refusal, then a real repair): `~/osw/feci_demo/calc_1de60575/`.
