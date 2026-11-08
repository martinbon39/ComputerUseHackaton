# Feci Guard

The fix our paper ("Cogito, Ergo Feci") recommends. A computer-use agent's false "done" is not repaired in the
weights. It needs an **external verifier** that checks every requirement of the task on the screen and tells the
agent what is missing.

Holo-3.1-4B judging its own work is at chance level: it catches 51 % of false successes and rejects 48 % of true
ones. So the verifier is a stronger model, Claude through the local `claude -p` CLI (Sonnet by default). Blocking a
false "done" with no explanation repaired 0 of 2 feasible false successes, so a refusal always says what is missing.

## How it works
- `run_holo_guard.py` is a **copy** of the official `holo_repro/run_holo.py`. The original is never modified. The agent
  loop is the same as `HoloComputerAgent.run`, except at the terminal `answer`.
- On `answer` (unless the answer declares the task infeasible), the guard takes a fresh screenshot and calls
  `verifier.verify(task, screenshot)`. The verifier lists every requirement, gives each one yes/no/cannot_tell with
  its visual evidence, and returns `COMPLETE` or `INCOMPLETE`, plus the most important missing requirement and a next
  action. The output is strict JSON (`--json-schema`), with a 90 s timeout.
- **INCOMPLETE** refuses the answer. As the answer's tool output, the agent gets
  `Verifier: requirement '…' is not satisfied on screen: <evidence>. <next action> Continue the task.`, and the
  episode goes on. **COMPLETE**, or no verdict (timeout, CLI error, invalid JSON), lets the answer through.
- Each episode allows at most 2 refusals. The 3rd answer is accepted without a check.
- Each episode directory gets:
  - `guard.md`: the readable journal, with each requirement ✓/✗/? and its evidence, the decision, and the feedback sent;
  - `guard.jsonl`: the raw verdicts, with latency and cost;
  - `guard_step_N.png`: the screenshot that was checked;
  - a `feci_guard` summary inside `meta.json`.

```
bash run_guard.sh ~/osw/results_feci_guard <tasks.json> 3            # guard on (default)
bash run_guard.sh ~/osw/results_x <tasks.json> 1 --guard off         # official behaviour, same copy
python verifier.py --task "<instruction>" --image shot.png           # one manual check
python -c "import feci_guard; print(feci_guard.check(task, png_bytes))"  # library entry point (duel, verif-study)
python compare_online.py --guard <dir> --orig <dir> [--orig <dir>] --tasks <tasks.json>
python offline_eval.py ...                                           # blind packet, see offline/
```
Options: `--guard on|off`, `--guard_model sonnet|opus|…`, `--guard_max_refusals 2`.

## Results
See `RESULTS.md`, which is filled in after the runs. The protocol was fixed beforehand in `PREREG.md`.
