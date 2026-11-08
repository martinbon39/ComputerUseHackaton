# Feci Guard

The fix our paper ("Cogito, Ergo Feci") recommends. A computer-use agent's false "done" is not repaired in the
weights. It needs an **external verifier** that checks every requirement of the task on the screen and tells the
agent what is missing.

Holo-3.1-4B judging its own work is at chance level: it catches 53 % of false successes and rejects 48 % of true
ones (judge bench below). So the verifier is a stronger model, Claude through the local `claude -p` CLI (Sonnet by default). Blocking a
false "done" with no explanation repaired 0 of 2 feasible false successes, so a refusal always says what is missing.

## Judge bench (same 268 episodes, final screen only)
Source: `../judge_bench/RESULT.json` and `REPORT.md` (verif-study corpus: 66 false successes, 202 true successes,
90 tasks). Rule: INCOMPLETE = detection, COMPLETE = pass, error = pass. Wilson 95 % CI; CI of the gap from a
task-level bootstrap.

| | Holo-3.1-4B | Holo4-27B | Claude Sonnet (Feci Guard verifier, sha `0af76fdb`) |
|---|---|---|---|
| False successes detected | 53 % (35/66) [41–65] | 47 % (31/66) [35–59] | **68 % (45/66) [56–78]** |
| True successes wrongly rejected | 48 % (97/202) [41–55] | 31 % (63/202) [25–38] | **10 % (21/202) [7–15]** |
| Gap, detection − false rejection | +5 pts [−13, +23] | +16 pts [−3, +33] | **+58 pts [+41, +74]** |
| Errors / invalid outputs (count as pass) | 3 / 3 | 1 / 4 | 0 / 0 |

Caveat (REPORT.md, Limits): the Holo judges used verif-study's V1 prompt, while Claude used the Feci Guard prompt
(strict JSON, INCOMPLETE only when a requirement is visibly "no"). The Claude advantage therefore mixes the model and
the prompt.

## How it works
- `run_holo_guard.py` is a **copy** of the official `holo_repro/run_holo.py`. The original is never modified. The agent
  loop is the same as `HoloComputerAgent.run`, except at the terminal `answer`.
- On `answer` (unless the answer declares the task infeasible), the guard takes a fresh screenshot and calls
  `verifier.verify(task, screenshot)`. The verifier lists every requirement, gives each one yes/no/cannot_tell with
  its visual evidence, and returns `COMPLETE` or `INCOMPLETE`, plus the most important missing requirement and a next
  action. The output is strict JSON (`--json-schema`), with a 55 s timeout.
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
bash run_repair.sh nog|guard <out> repair/episodes.txt 2             # repair measure (replayed false successes)
python analyze_repair.py ~/osw/feci_repair                           # its paired analysis
```
Options: `--guard on|off`, `--guard_mode passive|active`, `--guard_model sonnet|opus|…`, `--guard_max_refusals 2`.
Judge backend from the environment: `GUARD_BACKEND=claude` (local `claude -p`) or `openai` (`GUARD_BASE_URL`,
`GUARD_MODEL`, `GUARD_API_KEY_ENV` = name of the variable holding the key). `sync_to_runner.sh` copies the guard to
holo-osworld-runner for GitHub runs. The API (GuardedAgent, feci_guard.check, verifier.py) is frozen during the duels.

## Results
See `RESULTS.md`, which is filled in after the runs. The protocol was fixed beforehand in `PREREG.md`.
