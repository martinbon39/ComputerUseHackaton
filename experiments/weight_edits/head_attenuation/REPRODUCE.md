# Reproducing the audit

The owned pod folder is `/workspace/astra/moon-leak`. The repository archive is `experiments/weight_edits/head_attenuation`. `frozen/` contains byte-verified copies of the manifest, FROZEN.json, schema and all55 compressed input payloads; originals were read-only. `baseline_A/` contains the reused220 GUI baseline draws and the three newly measured text controls. `recorded_steps.json` preserves the39 teacher-forced suffix sources. Full source trajectories and the model snapshot remain external pinned inputs.

On the pod, run an independent CPU reconstruction of one arm:

```bash
cd /workspace/astra/moon-leak
OMP_NUM_THREADS=2 MKL_NUM_THREADS=2 OPENBLAS_NUM_THREADS=2 taskset -c 40,41 \
  /workspace/venv/bin/python independent_screen_audit.py head4_s0 --power ./frozen
```

The six arm names are `head4_s05`, `head4_s0`, `raw4_s05`, `raw4_s0`, `random4_s0`, `random_raw4_s0`. The last two are matched to the selective and raw families respectively. `control_contrasts.py --power ./frozen` checks their audits and computes paired contrasts. These commands perform no model inference. The Python environment needs NumPy and jsonschema.

`audit_budget.py` is deliberately expected to exit1: the7426-attempt budget is within the limits, but the retrospective audit flags continuation after two equality failures without execution progress. It did not act as an interlock during the experiment. Do not change its criteria to obtain a green exit.

`spec_*.json`, `build_head_edit.py` and the independently authored `verify_head_edit.py` reproduce each complete HF checkpoint from the pinned original Holo snapshot. Retired failed checkpoints are listed in `retired.jsonl`; no weight file is included in this archive. No production prompt, runtime hook or LoRA is part of these weight edits. Wv/Wk variants and the unused2/6-head specifications were not executed.

`attribution.py` is the final measured implementation; failed earlier script revisions were not individually archived. Their logs and raw pilot records remain, so some historical forward counts are inferred rather than direct terminal counters. Do not interpret re-running this script as an approved extension of the closed experiment.

Generation launchers retain the exact sampling, schema and server settings used. Existing experiment caps are closed; new inference results must be recorded as a separate experiment with their own budget. The offline cohort was used for both selection and screening, so its confidence intervals are exploratory. No online task success was measured here.
