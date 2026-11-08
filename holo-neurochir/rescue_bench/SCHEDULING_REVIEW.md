# Two-VM scheduling — independent review, pass 1/2

Reviewed 2026-11-08 before the full-cohort launch. No endpoint or VM was opened, and the reviewer did not modify the runner.

## Verdict

**RAN:** Python compile, shell syntax, static orchestration review, and CPU simulations of partition coverage, pilot completion, shard ownership, and recovery ownership.

**PASSED:** the scheduling partition, journal design, and registered deadline enforcement after correction 1/2. The two-shard full cohort is cleared to launch.

**CORRECT:**

- For 12 registered episodes, index parity produces two disjoint sets of six whose union is exactly the cohort. Episode order and the existing within-episode K/arm order are retained.
- The original pilot journal is included by `branches*.jsonl`. Its four successful slots enter `completed`; shard 0 therefore does not rerun the first episode, while shard 1 never owns it.
- Both full shards apply the pilot gate from the combined journals before filtering to assigned episodes. Shard 1 therefore passes the same four-branch gate even though the first episode belongs to shard 0.
- Shards write distinct journals, `branches.s0-of-2.jsonl` and `branches.s1-of-2.jsonl`. Recovery only writes a durable result when its task belongs to that shard. Since assignment is disjoint, the two workers cannot recover or execute the same slot.
- Analysis reads the original and sharded journals with `branches*.jsonl` and rejects any duplicate successful `(task, arm, k)` slot before aggregation.
- `RUNNER_PILOT_SHA256` retains the pre-scheduling runner digest. The current full runner has a different digest, as expected; the scheduling diff does not alter replay, Guard treatment, Holo generation, or official scoring code.

**NOT RUN:** Docker/KVM, Guard or Holo endpoints, live pilot/full execution, and official evaluation.

## Correction 1/2 — verified

The initial review found stale defaults of 11:38/11:40. The runner now defaults `--stop_launch` to **2026-11-08 11:20:00 UTC** and `--hard_stop` to **2026-11-08 11:29:50 UTC**, exactly matching the scheduling amendment and preceding the 11:30 endpoint closure.

Targeted `py_compile` passes. No further blocking finding remains. The already-running pilot used explicit deadline overrides and is unaffected by this default-only correction.

## Concurrency limitation

Each worker reads all journals at startup while each writer appends only to its own journal. Normal full launch is safe because the pilot is complete and the shard journals start separate. On a concurrent resume, reading another worker's journal exactly during its single append could observe a partial final line and fail JSON parsing. This fails closed and does not duplicate a slot; resume should be coordinated while peer journals are idle, or future hardening can tolerate one incomplete trailing line.
