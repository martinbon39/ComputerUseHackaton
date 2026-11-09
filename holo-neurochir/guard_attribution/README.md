# Guard attribution study: code to run it

This folder implements `holo-neurochir/report/PREREG_GUARD_ATTRIBUTION.md` (frozen, commits b8d2ddd and 26565da).
No episode of arms A, B or C had been run when this code was committed.
The frozen files are not edited: `feci_guard/*.py` and RealtimeGUI's `run_holo.py` / `holo_agent`.

## What the prereg requires before any episode, and where it is

| Prereg requirement | File | Test |
|---|---|---|
| vLLM sampling seed = fixed function of (seed, task id, step index), identical across arms, in both loops | `seeding.py`, `arms.py` | `tests/test_seeding_stub.py`, `tests/test_e2e_mock.py` |
| Arm B: neutral verifier, always COMPLETE after a delay drawn from the recorded latencies | `neutral_verifier.py`, `recorded_latencies.json` (from `extract_latencies.py`) | `tests/test_seeding_stub.py` (KS test, quantiles) |
| Analysis script: primary C − B, secondaries 1-6, committed before any result | `analysis.py` | `tests/test_analysis.py` (synthetic data from `synth.py`) |
| Arms interleaved by task, one rerun of infra-dead episodes, drop rule, 10 % hard stop after seed 0, cost log | `runner.py` | `tests/test_e2e_mock.py` |
| Same checkpoint, vLLM version and args, GPU type, 50 steps, prompt v2, OSWorld copy, VM image | `pins.json`, `serve_h100.sh`, `check_weights.py`, `runner.py preflight` | preflight on the node |

Run the tests:
```bash
cd holo-neurochir/guard_attribution
python3 -m unittest tests.test_seeding_stub tests.test_analysis     # stdlib only, ~15 s
HARNESS_PY=~/osw/venv/bin/python python3 -m unittest tests.test_e2e_mock   # needs the harness venv (openai, desktop_env, holo_agent)
python3 neutral_verifier.py --report                                # recorded vs drawn latencies, KS test
python3 runner.py plan                                              # the 1,080-episode schedule, nothing runs
```

## How each piece works

**Seeds (`seeding.py`).** `request_seed(s, task, step, k)` is the first 31 bits of
`sha256("guard-attribution/v1|s|task|step|k")`. `seeded(cls)` subclasses an agent class. It wraps the OpenAI client so
that every `chat.completions.create` gets `seed=`, and wraps `on_step` to count steps. The step index is the loop's
own `steps` counter: both loops call `on_step` once per increment of `steps`
(`rtg Agent/holo_agent/agent.py:217-299`, `feci_guard/run_holo_guard.py:124-186`). `k` counts the requests already
sent at that step: parse retries, and steps retried after a failed screenshot or `env.step`. On the normal path
`k = 0`. HTTP retries inside `_call_model` resend the same request, so they keep the same seed. Each request is logged
to `<episode>/seeds.jsonl`.

**Arms (`arms.py`).** It imports `run_holo` (arm A) and `run_holo_guard` (arms B, C). It replaces, in their module
globals, `HoloComputerAgent` and `GuardedAgent` with their seeded subclasses. `run_one()` looks these names up at call
time, so it builds the seeded classes. For B, the `feci` global of `run_holo_guard` becomes a `NeutralFeci`. For C it
is the real `feci_guard` module, and the loader refuses to start unless its `VERIFIER_SHA` is `0af76fdbacc72317`. In
B and C the guarded loop is unchanged, including the fresh screenshot at answer time. Only the verdict differs.

**Neutral verifier (`neutral_verifier.py`).** It resamples the 96 latencies of the real verifier recorded in
`results_test_gh_orig_guard_claude` (86 of 120 episodes; `meta.json` → `feci_guard.verifier_latency_s`). The RNG is
seeded from (seed, task, verifier call index). Over 10,000 draws the quantiles match the recorded ones to 0.01 s. The
two-sample KS test gives D = 0.006, p = 1.0. `meta.json` of B records `verifier_sha = neutral-<sha of the stub>` and
backend `neutral_stub`.

**Runner (`runner.py`).** Schedule: for each seed in order, the 120 tasks of `osworld/split_test.json` (sha256 pinned).
The three arms of a task run back to back, with the arm order rotated by task (ABC, BCA, CAB, ...). Workers (one VM
each) pull from that queue. After a seed's pass, each infra-dead episode (no `result.txt`: 0 steps, or a crash before
scoring) is moved to `<task>.dead1` and rerun once with the same seed. If it is still dead, `analysis.py` drops that
(task, seed) from all three arms. After seed 0, more than 10 % infra-dead first attempts stops the run with exit code 3.
Each attempt is one line of `<results>/ledger.jsonl`. It records wall time, model requests and failed requests, and
the verifier's calls, decisions, errors and cost. `<results>/cost.json` sums them.
The start record holds the repo HEAD.

Every task is pinned to one vLLM server (task index mod number of servers), so its three arms use the same GPU.

The parent hands items one at a time to each worker slot (one VM) and keeps the assignment, so an item whose worker
dies is recorded as infra-dead, never lost.
- An episode that runs longer than `--episode-timeout-min` (default 45) gets SIGTERM. The worker then closes its VM
  (`env.close()`), is killed after 60 s if still alive, and is replaced by a new generation. Messages from an old
  generation are ignored.
- A worker that dies 3 times before it is ready, or takes more than 15 min to start its VM, closes its slot. When no
  slot is left, the remaining items are recorded as infra-dead.
- After each pass, when all workers are stopped, the OSWorld containers created during the pass are removed (a VM
  started by a worker killed while still booting). The removal is logged in the ledger as `cleanup`. It only touches
  containers of the pinned OSWorld image that did not exist before the pass.
- An episode interrupted after it wrote `result.txt` keeps its score and is not infra-dead (the prereg's definition is
  "fails before scoring").

Real runs need `--go`, all 120 tasks, and a passing preflight. The preflight refuses to run if any of the following
holds:
- The study code is not committed.
- A frozen file differs from its sha256 in `pins.json` (`feci_guard.py`, `verifier.py`, `run_holo_guard.py`, and the
  five RealtimeGUI files of a763361 + patch).
- The split differs.
- An endpoint lacks the model or runs another vLLM version.
- `GUARD_BACKEND` is not the relay, or the relay does not answer `/models`. If the verifier fails, C passes every answer
  and so silently becomes B.
- A local GPU is not an H100.
- `OSW_NETWORK_SH` does not point to the earlier runs' VM network script.

`preflight --probe` sends 3 seeded requests per endpoint. `preflight --probe-verifier --go` makes one real verifier call
through the relay on a recorded screenshot (about $0.03). The relay's `/models` answers without reaching Claude, so
only this call shows that C will get verdicts.

A sharded job must run exactly one seed. `--max-tasks` exists only for `--mock`.

`--pilot` runs the one-task real test that the prereg asks for before any arm ("tested on one task"). It uses the
first TEST task, the three arms and seed 99 (not a study seed), and writes into `<results>/pilot`, which
`analysis.py` never reads. It ends with PILOT OK (exit 0) only if all three arms scored with no failed model request
and C's verifier calls, if any, had no error. Otherwise it ends with PILOT FAILED (exit 4).

**Analysis (`analysis.py`).** Python stdlib only. Episode outcomes are those of `online_guard_analysis.py`. `boot()` is
identical to its `boot()`, and a test checks this. Primary: the per-task false-"done" rate averaged over valid seeds,
paired C − B, bootstrap over tasks, 10,000 draws, `random.Random(0)`, percentile 95 %. The guard reduces false "done"
only if the upper bound is < 0. Then secondaries 1-6 in prereg order. There is one extra block,
`checks_not_preregistered`. It holds the verifier latency in B vs C, C's verifier decisions and errors, the number of
episodes that end on a refused answer (these count as false "done" by the prereg's definition, which can only count
against C), and the failed model requests per arm. Usage:
`python3 analysis.py --results DIR --tasks ../osworld/split_test.json --out result.json --md result.md`.

## Pins (`pins.json`)
- Model: `Hcompany/Holo-3.1-4B@8c88265a5a159bfd1492db9243733dd2e6e04a6e`. The sha256 of `config.json` and of both
  safetensors are from `osworld/modal_deploys/20261108T093735_acct1_Holo-3.1-4B-modal-orig.revision.json`.
  `check_weights.py` verifies them on the node.
- vLLM 0.23.0, image `nvidia/cuda:12.8.1-devel-ubuntu24.04`, Python 3.12, and the pip pins of `osworld/modal_vllm.py:31-35`.
  Args from `osworld/modal_vllm.py:25-27`: `--dtype bfloat16 --max-model-len 32768 --max-num-seqs 64
  --gpu-memory-utilization 0.40 --kv-cache-memory-bytes 30G --limit-mm-per-prompt {"image": 5} --reasoning-parser qwen3
  --enable-prefix-caching`. 1 × H100 per server, tensor-parallel 1, no server `--seed`.
- Harness: RealtimeGUI `a763361f9fffad5fcbbdb16bdb51ea3ff667c183` plus `holo-osworld-runner/patches/rtg-a763361.patch`.
  Docker provider with KVM. Env of `osworld.yml` "Run Holo on shard": `OSWORLD_FORCE_KVM=1 OSW_MEM_LIMIT=5g
  OSW_NETWORK_SH=<runner>/scripts/network_nft.sh`. Max 50 steps, prompt v2.
- Not pinned in the earlier runs, so to be recorded before seed 0: the digest of `happysixd/osworld-docker:latest` and
  the sha256 of `Ubuntu.qcow2` (from `xlangai/ubuntu_osworld`, no revision in the URL).

## Two ways to run it on the 8 × H100

The prereg budget line says: "the H100s provided for 2026-11-09 serve the agent; VMs on the GitHub runners as before".
**Option 1 is the preregistered one.** Option 2 changes the VM host. It is the same for all three arms, so it cannot
bias C − B. It is still a deviation and must be listed in the result.

### Option 1 (preregistered): model on the H100 node, VMs on GitHub runners
1. On the node: `bash serve_h100.sh --gpus 8` (dry run), then `HOLO_VLLM_KEY=... bash serve_h100.sh --gpus 8 --go`.
   This starts 8 servers on 127.0.0.1:8000-8007 and verifies the weights first.
2. Reach the node from the runners. The workflow already keeps an SSH tunnel to a "tunnel host" (`scripts/tunnel.sh`,
   pinned host key). Either:
   (a) the node is the tunnel host, and its forwards are 8000-8007 plus a reverse path to the guard relay; or
   (b) the node opens `ssh -R 18000-18007 → 127.0.0.1:8000-8007` to orbit, and the runners keep `tunnel_host=orbit`
   with forwards `9911,18000-18007`.
   (b) reuses the path that already worked for the guard relay (`LOG.md:630`).
3. In `holo-osworld-runner/.github/workflows/osworld.yml`, step "Run Holo on shard", add an `attribution` arm that runs
   instead of `run_holo.py`:
   `~/osw/venv/bin/python $GITHUB_WORKSPACE/guard_attribution/runner.py run --go --shard $SHARD/$N_SHARDS --seeds $SEED
   --results $RES --base-urls http://127.0.0.1:$((18000 + SHARD % 8))/v1 --served-model Holo-3.1-4B-orig --workers 1`,
   with `GUARD_BASE_URL=http://127.0.0.1:9911/v1`, `GUARD_KEY=EMPTY` and `HOLO_VLLM_KEY` from a secret. Copy
   `guard_attribution/` next to `feci_guard/` (as `feci_guard/sync_to_runner.sh` does). Each job runs its tasks with
   all three arms back to back, on one VM.
4. Before seed 0, run the pilot (`--pilot`) on one runner and read its episodes. Then, per seed (one seed per
   dispatch): dispatch the 20 shards, collect them with `osworld/gh_collect.sh`, and merge the ledgers. Then
   `python3 runner.py status --results DIR`, which exits 3 when the 10 % rule says stop after seed 0. Then start the
   next seed.

### Option 2: model and VMs on the H100 node (needs `/dev/kvm` on the node)
1. Same step 1 as option 1.
2. Install RealtimeGUI at the pinned commit in `~/osw/rtg` (`run_holo_guard.py:34` hard-codes that path). Apply the
   patch, create the harness venv as the workflow does (`osworld.yml:224-267`), and download `Ubuntu.qcow2`.
3. Tunnel to the guard relay: `ssh -N -L 9911:127.0.0.1:9911 orbit@<vps>` and `export GUARD_BASE_URL=http://127.0.0.1:9911/v1`.
   Do not stop the relay on orbit. It allows 4 concurrent calls (`GUARD_RELAY_CONCURRENCY`).
4. `python3 runner.py preflight --base-urls <8 urls> --probe`, then the pilot
   `python3 runner.py run --go --pilot --results ~/attr --base-urls <8 urls>`. Read its three episodes. Then run
   `python3 runner.py run --go --results ~/attr --base-urls <8 urls> --workers 24`.
   The worker count is set by CPU and RAM: each VM is a docker container capped at 5 GB.

### Time and cost (estimates, not measured on the node)
- One episode takes about 3.5 min: run 42442467233 shard 1 took (4547 − 381) s for 20 episodes (`_jobs/*/timing.json`).
  1,080 episodes is about 63 VM-hours. That is about 3.2 h with 20 GitHub runners, or about 2.6 h with 24 local VMs,
  plus reruns.
- Claude calls in C: about 100 per seed (prereg), about $9 in total at $0.03 per call.

## What we need from Emile (send before the window)
1. SSH: host, port, user, how to add our public key, sudo (yes/no), and whether it is a bare-metal node, a VM or a container (k8s/RunPod-like).
2. GPUs: `nvidia-smi` output (8 × H100 80GB, SXM or PCIe), driver version (≥ 570 for CUDA 12.8), and exclusive use during the window.
3. KVM: `ls -l /dev/kvm` and whether our user can open it (needed only for option 2). A container usually has no KVM, which means option 1.
4. CPU and RAM: core count and total RAM. Option 2 needs about 2 cores and 5 GB per VM: 24 VMs is about 48 cores and 120 GB.
5. Disk: at least 300 GB free on a local disk (VM image 24 GB unzipped, weights 9 GB, vLLM venv 15 GB, results about 20 GB).
6. Docker: installed and usable by our user. Needed for option 2 (the OSWorld provider). Not needed for vLLM, which runs from a venv.
7. Egress: huggingface.co (weights, VM image), pypi, github.com, docker hub, and outbound SSH to orbit (guard relay; tunnel for option 1). Inbound SSH is enough; no public port is needed.
8. Window: start time and how long we keep the node (≥ 6 h including setup and reruns).

## Interpretations of the prereg (to confirm or list as deviations)
1. "Step index" is the loop's `steps` counter. A retried request at the same step gets `k = 1, 2, ...`. Without this,
   a parse retry would resend the same seed and get the same failure.
2. The 10 % hard stop counts infra-dead **first attempts** among the 360 seed-0 episodes, before reruns. This is the
   stricter reading. In a sharded run (option 1), `runner.py status` applies it on the collected ledgers.
3. Reruns of a seed run after that seed's main pass. They are not interleaved with the other arms.
4. The arm order is rotated by task (ABC, BCA, CAB) so that no arm always goes first.
5. The study serves the model as `Holo-3.1-4B-orig`. The earlier run used `Holo-3.1-4B-modal-orig`. The name is not in
   the prompt.
6. The VM host (option 2) and the vLLM host (H100 node instead of Modal) differ from the earlier run. They are the same
   across arms.
7. Step cap = the loop's step counter reached 50 (`meta.json` `steps`). `traj.jsonl` also holds the accepted answer,
   so counting its lines (as `paper/figs/guard.py` did) overstates the count by one.
8. A model-server outage in the middle of an episode ends the episode, which is then scored. The prereg's infra-dead
   definition is "0 steps or failure before scoring". Such episodes are not infra-dead, but each one is counted in the
   ledger and in `checks_not_preregistered` (failed model requests). An episode killed by the timeout counts as
   infra-dead (the runner failed before scoring).
9. `preflight --probe-verifier --go` makes one Claude call outside arm C (about $0.03). The prereg says Claude calls
   happen only in C. This call is a preflight check, not an episode, and it is listed as a deviation.

## Arm D: placebo refusal (supplementary, draft prereg `report/PREREG_GUARD_PLACEBO.md`)
- `neutral_verifier.PlaceboFeci` refuses each checked answer with probability 0.23, with a fixed generic message. The
  draw is seeded by (seed, task, verifier call index), so reruns draw the same refusals. Latency is drawn as in B.
- `runner.py --arms A,B,C,D` rotates ABCD by task. The default stays `A,B,C` until Martin approves the supplement. The
  frozen stop rule, drops and `analysis.py` use A, B and C only.
- Supplementary analysis: `analysis_placebo.py` (primary C − D false "done", kill rule on C's seed-0 refusal rate).
- Why: `placebo_power.py` (simulation). A random refuser at r = 0.23 meets the frozen primary in about 27 % of
  replications if seeding holds, and 17-22 % if it holds in 40-70 % of episodes. Its effect is −1.9 pts. The figure
  ranges from 0.4 % to 78 % depending on post-refusal behaviour.
- B's stub hash now covers only the latency data and B's code (`neutral-63939f75`; it was `neutral-b76422a8` in
  3f66e6a, before any episode).
- Every episode now keeps its step screenshots and `final_screen_after_eval.png` on the node. The pilot fails if any
  are missing.

## Open decision for Martin: batch-invariant vLLM
vLLM does not promise identical outputs for the same seed. A request's result depends on the other requests batched
with it (vLLM docs "Reproducibility", https://docs.vllm.ai/en/latest/usage/reproducibility/; Thinking Machines,
"Defeating Nondeterminism in LLM Inference", 2025-09-10). So with the pinned args, A and B share the sampling seeds but
can diverge after the first token that differs. The prereg expects this and measures it (secondary 3).
`VLLM_BATCH_INVARIANT=1` (beta, needs compute capability ≥ 8.0, https://docs.vllm.ai/en/latest/features/batch_invariance/)
would make outputs independent of batching. It would raise secondary 3 and tighten the A vs B pairing. But it changes
the kernels relative to the earlier online run ("same vLLM version and args"). We have not checked that it supports this
model in 0.23.0. It is **off** by default here. Turning it on is a deviation to declare. The primary criterion's
bootstrap over tasks stays valid either way, since tasks are the unit (Anthropic, "A statistical approach to model
evaluations", 2024-11-19).
