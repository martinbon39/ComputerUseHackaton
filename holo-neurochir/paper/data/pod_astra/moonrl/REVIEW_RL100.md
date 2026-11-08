# Independent RL100 review

No model/API/GPU/OS call was made.

## Verdict

- **RAN:** independent completeness, identity, frozen-row/payload, JSON-schema, error/truncation, aggregate, bootstrap/gate, receipt, and three-text-control checks.
- **PASSED:** technical completeness, JSON-rate gate, and text controls.
- **CORRECT:** `analysis_rl100.json` matches independent recomputation.
- **REJECTED:** the mandatory healthy structural gate fails. The fs+ efficacy signal also fails in the opposite direction.
- **NOT RUN:** exhaustive blind qualitative action review, because no qualitative result can override failure of the mandatory healthy gate; live OS behavior; checkpoint construction/integrity; other arms.

## Evidence

`runs/rl100/generations.jsonl` SHA-256: `617cc6a2b41bb7d95b6e68057ffe434e2075ad1e37ab38213406680af241dd6c`. It contains exactly 220 unique expected task/seed pairs. Every frozen row, payload digest, arm and model identity matches. The receipt records vLLM 0.23.0, sole model `power_rl100`, root `/dev/shm/moon_rl_tmax_b100`, frozen SHA `9bf07af1f630ffbee0f628347270dff9c3abe068aa9fb76c9c8c747e47585839`, retries zero, and 220 completions.

Schema-valid, non-error outputs are 219/220 = 99.545%, passing the 95% gate. There are zero transport errors and one fs+ truncation/schema-invalid output.

| Stratum | A answer | RL100 answer | Delta | 95% paired task-bootstrap CI |
|---|---:|---:|---:|---:|
| fs+ | 56/76 | 62/76 | **+7.895 pp** | [+2.632, +14.474] pp |
| true finish | 75/80 | 74/80 | -1.250 pp | [-3.750, 0.000] pp |
| healthy | 4/64 | 7/64 | +4.688 pp | [0.000, +12.500] pp |

Healthy valid non-answer falls from 60/64 to 57/64: **-4.6875 pp**, 95% paired task-bootstrap CI [-12.5, 0.0] pp. This fails the registered mandatory cutoff `>= -2 pp`. Healthy exact recorded-tool rate falls from 59/64 to 57/64, diagnostic only. Fs+ answer probability increases by 7.895 points rather than meeting the `<= -15 pp` signal.

All three T0 controls are error-free, untruncated, coherent and correct: `391`; the correct French translation; and a correct one-sentence freezing explanation.

The qualitative files contain 101 differing actions among the 140 fs+/healthy pairs, with 39 identical and 80 true-finish pairs out of scope. No blind judgments were frozen: exhaustive qualitative review stopped once the mandatory healthy failure was independently confirmed. No new threshold or exception was introduced.
