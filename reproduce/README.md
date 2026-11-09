# Reproduce

Checks of the paper's numbers, from the cheapest to the most expensive. Level 1 needs nothing but Python; levels 2
and 3 need downloads and, for level 3, a GPU.

## Level 1: recompute the headline numbers (CPU, Python ≥ 3.9 standard library, about a minute)
```bash
bash reproduce/run_all.sh     # runs the four scripts below; exit 0 = every number equals the paper's
```
| Script | What it recomputes | Input |
|---|---|---|
| [`verify_results.py`](verify_results.py) | Online paired comparisons of the weight edits (merge, AlphaEdit, ExPO) and the noise floor, task-level bootstrap with a fixed seed. Must print +1.94 (165 tasks), +0.18 (test), +6.64 (reserve) | [`results/scores.csv`](results/scores.csv): 660 rows, one per task, arm and split; the paper's "reserve" split is `confirm` here |
| [`replay_guard.py`](replay_guard.py) | The frozen guard decision (`src/feci_guard/feci_guard.py::check`) on the 268 recorded final screenshots (sha256-checked); only the network call is replaced by the verdict recorded on 2026-11-08. Must print 45/66 and 21/202 | `experiments/verif_study/`, `experiments/judge_bench/claude_responses.jsonl` |
| [`recount_judges.py`](recount_judges.py) | The three judges (Holo-3.1-4B, Holo4-27B, Claude) recounted from their raw responses: 35/66, 31/66, 45/66 | `experiments/verif_study/`, `experiments/judge_bench/` |
| [`verify_online_guard.py`](verify_online_guard.py) | The online guard test (120 tasks), with the analysis function committed before the results were read, checked against the published JSON | [`results/online_guard_tasks.csv`](results/online_guard_tasks.csv), `experiments/online_guard/` |
| [`check_links.py`](check_links.py) | Every relative link and anchor of the repository's Markdown files | |

Expected output: [`EXPECTED_OUTPUT.md`](EXPECTED_OUTPUT.md). The paper itself is rebuilt from its data with
`bash paper/build.sh` ([`paper/README.md`](../paper/README.md)).

## Level 2: one live verifier call (Claude CLI or an Anthropic key, about $0.03)
```bash
python3 reproduce/guard_live.py                    # uses the claude CLI, logged in
pip install openai && ANTHROPIC_API_KEY=... python3 reproduce/guard_live.py --api
python3 reproduce/guard_live.py --list             # the 268 episode ids, label, recorded verdict
python3 reproduce/guard_live.py --episode <id>
```
It sends one recorded final screen to the verifier and compares the live decision with the recorded one. The CLI path
was run (output in [`EXPECTED_OUTPUT.md`](EXPECTED_OUTPUT.md#level-2)); the `--api` path was not, for lack of a key on
the machine.

## Level 2: rebuild the merged checkpoint bit-for-bit (about 40 GB of disk, CPU)
```bash
python3 reproduce/rebuild_merge.py --build OUT       # full rebuild, compares the safetensors sha256 with expected_sha256.json
python3 reproduce/rebuild_merge.py --check 2 --merged DIR   # compare 2 tensors only
```
The merge is `θ = θ_Holo + 0.5·(θ_CUA − θ_Qwen)` on the language tower. `embed_tokens` is merged, and since Holo has
`tie_word_embeddings=true` the effective output head changes too. Pinned inputs:
`Hcompany/Holo-3.1-4B@8c88265a5a159bfd1492db9243733dd2e6e04a6e`, `Qwen/Qwen3.5-4B@851bf6e806efd8d0a36b00ddf55e13ccb7b8cd0a`,
`OnAnOrange/CUA-Lite-Qwen3.5-4B-ScaleCUA-gpt5_5-epoch3-public@df6eba93efb2df3ed9adc810e0f7f4e038959c74`
(`pip install -r reproduce/requirements.txt`). The merged checkpoint is not yet published on the Hugging Face Hub.

## Level 3: replay four frozen contexts on the original and the merged model (GPU with 16 GB)
[`probe_decision.py`](probe_decision.py) or [`probe_decision.ipynb`](probe_decision.ipynb) (Colab T4, fp16) replays the
contexts in [`contexts/`](contexts/) (3 full-resolution screenshots each) and prints P(`answer`) against the other tools,
original vs merged. `--dry-run` needs only `pillow`; use `--sample 4` for an informative number.

## What was and was not run before release
- Level 1: run in full, and in CI on every change to its inputs.
- Level 2 rebuild: the full merged checkpoint was rebuilt on an independent machine with our merge script (same formula)
  and reproduced the sha256 of both safetensors shards (`b7acdd12…`, `6f88c913…`). `rebuild_merge.py` itself was checked
  on 2 tensors only; its full `--build` was not run.
- Level 3: message construction checked identical to our harness and tokenisation checked; the forward pass was not run
  on a GPU by the authors.

Harness caveat: our OSWorld harness (RealtimeGUI @ `a763361`) is more permissive than the official Holo adapter on
infeasible tasks, so absolute scores are not comparable with published ones. Only paired comparisons are meaningful.

Also here: [`RESULTS.md`](RESULTS.md) (summary of the weight-edit track, written before the paper's review),
[`tools/`](tools/) (the scripts that exported `results/` and `contexts/` from the raw runs; they need the raw runs).
