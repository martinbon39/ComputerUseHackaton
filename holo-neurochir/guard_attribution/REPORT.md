# h100prep report: guard attribution study, ready to run (2026-11-09)

Scope: `holo-neurochir/report/PREREG_GUARD_ATTRIBUTION.md` (frozen, not edited). No real episode was run.
Code: `holo-neurochir/guard_attribution/` (commits 7aac210, f9c0f07 and the commit that adds this report), pushed to main.
How to use it: `README.md` in this folder.

## Done (each prereg pre-run requirement)
| Requirement | Where | Evidence |
|---|---|---|
| Seed = f(s, task, step) in both loops, identical across arms | `seeding.py`, `arms.py` (subclasses patched into the module globals; frozen files untouched) | `tests/test_seeding_stub.py`; `tests/test_e2e_mock.py`: A and B send identical seed sequences up to the first answer, C shares the prefix; the mock vLLM records every seed |
| B: neutral stub, recorded latencies | `neutral_verifier.py`, `recorded_latencies.json` (96 values, 86/120 episodes of `results_test_gh_orig_guard_claude`) | 10,000 draws: quantiles equal to recorded at 0.05 to 0.95, KS D = 0.006, p = 1.0 |
| Analysis committed before results | `analysis.py` (stdlib); `boot()` identical to `online_guard_analysis.py` (tested) | Synthetic data: planted −17 pts recovered, CI [−24, −13]; null CI covers 0 in 29/30 replicates |
| Runner: interleave, one rerun, drop, 10 % stop, cost | `runner.py` | e2e: 3 arms on one task; dead → rerun → drop → exit 3; hung episode times out; worker dying mid-item recorded, not lost; refusals (shard with more than one seed, sub-sample, preflight); pilot |
| Pins | `pins.json`, `serve_h100.sh` (dry run by default), `check_weights.py`, `runner.py preflight` | Model `Hcompany/Holo-3.1-4B@8c88265a…` + 3 file sha256; vLLM 0.23.0 and args from `osworld/modal_vllm.py:20-35`; sha256 of 8 frozen files (RealtimeGUI a763361 + runner patch, verified byte-identical) |

Tests: 19 pass (13 stdlib in about 10 s, 6 end-to-end in about 80 s with the harness venv). `jury_kit/quickstart.sh` is still QUICKSTART OK.

## Where the earlier online test ran (found)
- Workflow: `holo-osworld-runner/.github/workflows/osworld.yml`.
  - Runners: `ubuntu-latest` with KVM. Provider: docker, image `happysixd/osworld-docker:latest` (digest not pinned).
  - VM: `xlangai/ubuntu_osworld` Ubuntu.qcow2 (revision not pinned, no sha256 recorded).
  - Harness: RealtimeGUI a763361 + `patches/rtg-a763361.patch`.
  - Guard: `GUARD_BACKEND=openai` through an SSH tunnel to the `guard_server.py` relay on orbit (127.0.0.1:9911).
- Runs: guarded 42468308809, 42468884640 and 42472655505; Modal original 42442467233.
- Model: Modal, 1 × H100, vLLM 0.23.0, no server seed, tensor-parallel 1.

## Decisions needed (Martin, via ares)
1. **VM topology.** The prereg budget line says "VMs on the GitHub runners as before" (option 1). That needs:
   - an `attribution` arm in `osworld.yml`, which I did not write because that repo is not mine; the exact command is
     in the README;
   - a way for the runners to reach the H100 vLLM servers (reverse tunnel to orbit).

   Option 2 (VMs on the H100 node, needs /dev/kvm) is ready to run now. It changes the VM host, which must be declared
   as a deviation. It is the same for all arms.
2. **`VLLM_BATCH_INVARIANT=1`: on or off.**
   - On: same-seed outputs stay identical under batching, so A and B stay coupled longer (secondary 3).
   - Off (the default here): kernels unchanged from the earlier run, but same-seed outputs can diverge under batching
     (vLLM docs "Reproducibility"; Thinking Machines, 2025-09-10).
3. **Interpretations to accept or list as deviations** (README §Interpretations):
   - k = retry index within a step;
   - the 10 % stop counts first attempts;
   - reruns happen after a seed's pass;
   - the arm order rotates;
   - served name `Holo-3.1-4B-orig`;
   - step cap from `meta.json` steps;
   - a model outage mid-episode is scored but reported.
4. **Pin the VM image and docker image.** Before seed 0, record the qcow2 sha256 and the docker image digest (never
   recorded in the earlier runs).

## What we need from Emile (checklist)
1. SSH host, port, user, how to add our key, sudo, and whether the machine is bare metal, a VM or a container.
2. `nvidia-smi` output: 8 × H100 80GB, driver ≥ 570 (CUDA 12.8), exclusive use during the window.
3. `ls -l /dev/kvm` and whether our user can open it (option 2 only; a container usually has no KVM).
4. CPU cores and RAM. Option 2 needs about 2 cores and 5 GB per VM, so 24 VMs need about 48 cores and 120 GB.
5. At least 300 GB free on a local disk.
6. Docker usable by our user (option 2).
7. Egress to huggingface.co, pypi, github.com and docker hub, plus outbound SSH to orbit (guard relay).
8. Window: start time and duration (≥ 6 h including setup and reruns).

## Run order on the node (option 2)
1. `serve_h100.sh --gpus 8 --go`, which runs `check_weights.py` first.
2. SSH tunnel to the orbit relay on port 9911, then set `GUARD_BASE_URL` and `OSW_NETWORK_SH`.
3. `runner.py preflight --probe --probe-verifier --go`.
4. `runner.py run --go --pilot`; read its 3 episodes.
5. `runner.py run --go --workers 24`.
6. `analysis.py --results DIR --out result.json --md result.md`.

Estimate: about 3.5 min per episode (run 42442467233), so about 63 VM-hours, which is about 2.6 h on 24 VMs plus
reruns. Claude: about 300 calls, about $9.

## Review (maker ≠ checker)
A fresh-context reviewer (general-purpose subagent, read-only) checked the code against the prereg line by line in
three rounds.
- Round 1: PASS WITH FIXES, 12 findings, all addressed in 7aac210.
- Round 2: PASS WITH FIXES. It reproduced a hang in the new supervisor and found 5 more issues, fixed in f9c0f07.
- Round 3: PASS WITH FIXES. Bugs 1-5 were fixed and verified by 5 supervisor probes (death with an item in hand,
  death before ready, never ready, late result after a timeout, SIGTERM ignored). The two remaining low items are
  fixed in the last commit, and all 19 tests still pass:
  - an episode interrupted after scoring keeps its score;
  - a VM container is orphaned when a worker is killed while booting; it is removed after each pass and logged.

  It also asked to declare the extra verifier probe call as a deviation, which README interpretation 9 does.

## Sources (practices applied)
- vLLM docs, "Reproducibility" and "Batch Invariance": same-seed outputs are not guaranteed identical across batching.
  We measure this (secondary 3) and do not assume it.
- Thinking Machines, "Defeating Nondeterminism in LLM Inference", 2025-09-10: server load drives nondeterminism, which
  is why each task is pinned to one GPU.
- Anthropic, "A statistical approach to model evaluations", 2024-11-19: paired differences, resampling within a
  question, the cluster (task) as the bootstrap unit. This matches the preregistered statistic.
