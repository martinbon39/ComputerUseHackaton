# AGENTS.md

Guide for coding agents (and careful humans) working in this repository. The overview, the claims table and the
citation are in [README.md](README.md).

## What this repository is
The companion repository of the paper *Cogito, Ergo Feci* on false "done" in the computer-use agent Holo-3.1-4B. It
must let a reader check every number of the paper. Three properties matter more than anything else:
1. **Every number in the paper is generated from data.** `paper/build.sh` runs `paper/figs/*.py` on `paper/data/`,
   writes `paper/generated/*.tex` (each macro names its source in a comment) and compiles both PDFs.
2. **The headline numbers recompute on CPU.** `bash reproduce/run_all.sh` exits 0 only if each recomputed number
   equals the one in the paper.
3. **Results are not edited after the fact.** Gates and decision rules were committed before the data they judge;
   corrections are appended, never rewritten.

## Checks to keep green
```bash
bash reproduce/run_all.sh           # exit 0, ends with "ALL CHECKS OK"
python3 reproduce/check_links.py    # 0 broken relative links or anchors
bash paper/build.sh                 # rebuilds every number, table, figure and both PDFs; 0 undefined references
```

## Do not edit
- `src/feci_guard/feci_guard.py` and `src/feci_guard/verifier.py`: the frozen v1 decision rule and verifier. Every
  recorded verdict carries the verifier's sha256 prefix `0af76fdb`. v2 lives in separate files.
- Result and data files (`*.json`, `*.jsonl`, `*.csv`, logs, images) anywhere, and everything under `paper/data/`.
- `docs/lab_notebook/`: raw working logs, kept verbatim as provenance. They use the pre-restructure paths
  (`holo-neurochir/...`, `jury_kit/...`); [docs/REPO_MAP.md](docs/REPO_MAP.md) maps them to the current layout.
- Pre-registration and protocol files (`PREREG*.md`, `PROTOCOL.md`, `AMENDMENT*.md`).

## Where things are
- `paper/`: sources (`sec/`, `fig/`, `shared/`, `neurips/`), `data/`, `figs/*.py`, `generated/`, PDFs. Read
  [paper/README.md](paper/README.md) before changing a number.
- `reproduce/`: CPU checks, checkpoint rebuild (`rebuild_merge.py`), decision probe (`probe_decision.py`),
  per-task scores in `results/`, expected output.
- `src/`: `feci_guard/` (the verifier and its agent loops), `holo/` (harness), `osworld/` (online evaluation),
  `scripts/` (checkpoint builders).
- `experiments/`: one folder per study with its protocol and report. Status of each:
  [docs/REPO_MAP.md](docs/REPO_MAP.md).

## Things that look odd but are intended
- Many folders hold negative results. They are kept on purpose and labelled in `docs/REPO_MAP.md`.
- Scripts contain absolute paths of the machines they ran on (`/home/orbit/...`, `~/osw/...`, `/workspace/...`).
  They document what ran. The scripts in `reproduce/` use relative paths only.
- The split called "reserve" in the paper is `confirm` in `reproduce/results/scores.csv`.
- Weight-edit folders were renamed from the agent code names used while the work ran (`astra-merge` became
  `experiments/weight_edits/task_vector_merge`, and so on; the table is in
  [experiments/weight_edits/README.md](experiments/weight_edits/README.md)). Reports inside them may still use the
  old names.
- Claims follow one rule: a gain is claimed only if the lower bound of the paired 95 % CI is above zero.
