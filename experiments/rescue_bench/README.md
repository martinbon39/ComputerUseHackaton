# Rescue benchmark

This experiment tests whether a frozen Claude Feci Guard refusal followed by Holo4-27B repairs recorded feasible false completions better than Holo4 continuation without Guard. It uses the same 12 recordings as the Holo3.1 repair benchmark, two repetitions per arm, up to 20 new model turns, and the official OSWorld evaluator.

Read `REPORT.md` for measured results and limitations, `RESULT.json` for per-episode outcomes, and `PREREG.md` for the protocol and dated clarifications. Reserve/test gain is a conditional prediction; these splits were not rerun by this experiment.

## Recompute without a model or VM

From the repository root, using Python 3 and its standard library:

```bash
python3 experiments/rescue_bench/verify_analysis.py
python3 experiments/rescue_bench/analyze.py --root experiments/rescue_bench/data
```

The first command checks pairing, partial scores, no-action credit, missing outcomes, duplicate rejection, and boundary validity. The second regenerates `REPORT.md` and `RESULT.json` from the archived branch journals. Its generation timestamp changes; the numerical estimates use a fixed bootstrap seed. The `data/` archive contains the three branch journals from the completed pilot and two full-run shards.

Official score1 and repair credit are separate: a success without any new action receives zero repair credit in the prediction. The registered primary requires all four branches to have valid replay screenshots. The stricter sensitivity also checks the terminal boundary; every episode's exclusions are shown. All completed episodes, including invalid replays, remain in a separate sensitivity analysis.

## Run the real experiment

The VPS launcher is `run.sh`; the new implementation is `../feci_guard/rescue_runner.py`. It imports the existing repair runner, frozen verifier, and canonical `run_holo` harness. `FROZEN.json` pins their file hashes. The launcher expects the existing Docker+KVM OSWorld environment at `~/osw/rtg/Env/OSWorld`, its Python environment at `~/osw/venv`, the registered recordings, and an authorized Holo4-compatible endpoint. It reads the bearer key from `~/.holo_modal_key` without displaying it.

Run the compatibility phase, then the paired pilot, then the full phase. Use the same output directory so the completed pilot is retained. The runner accepts `--phase compatibility|pilot|full`, `--out`, `--base_url`, `--model`, `--stop_launch`, and `--hard_stop`. Its default deadline is specific to 2026-11-08 and must be explicitly changed for a later experiment.

For two workers, use `--shards 2 --shard 0` and `--shards 2 --shard 1` in separate processes after obtaining both fleet slots. The shards contain disjoint episode indices and keep the registered within-episode order. The fleet limit is two OSWorld VMs; available memory must remain above the runner's 10 GiB gate. Failed infrastructure attempts may be retried once; successful outcome slots are never rerun. A resumed worker recovers durable outcomes before scheduling missing slots.

Raw screenshots, model calls, Guard decisions, and evaluator logs from this run remain at `/home/orbit/osw/rescue_bench/`. The committed journals contain the official scores, tool sequences, replay diagnostics, and source hashes needed for numerical reproduction. Independent reviews are recorded in `VERIFY_RUNNER.md`, `SCHEDULING_REVIEW.md`, `STATS_REVIEW.md`, and `MEASURED_REPAIRS_REVIEW.md`, and `FINAL_REVIEW.md`.
