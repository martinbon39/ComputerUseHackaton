# Online validation of a patched 4B (runbook)

Goal: from a CANDIDATE `patch_spec.json` to both OSWorld arms running in < 10 min. Pod = `ssh -i ~/.ssh/runpod_holo -p 15780 root@213.181.111.151`.

1. **Checkpoint** (pod, ~2 min):
   `cd /workspace/projet && PYTHONPATH=. HF_HOME=/workspace/hf HF_HUB_OFFLINE=1 HOLO_MODEL=Hcompany/Holo-3.1-4B /workspace/venv/bin/python scripts/make_patched_ckpt.py <spec.json> /workspace/ckpt/<tag>`
   Spec: `holo/surgery.py` format, or `{"kind": "steering", "direction_file", "layers": [l], "alpha"}` (hook compiled into the writers of layers 0..l, approximate). `patch_manifest.json` lists the edited tensors and their relative change.
   Optional independent check (~4 min): `scripts/check_ckpt_equiv.py /workspace/ckpt/<tag> /workspace/ckpt/_tests/probe.png` (differing tensors + HF outputs vs original).
2. **Serve** (pod, ~2 min): `bash /workspace/projet/osworld/serve_patched.sh /workspace/ckpt/<tag>` → tmux `vllm_8011`, name `Holo-3.1-4B-patched`, `--gpu-memory-utilization 0.15`, pod port 8011 (the pod's 8001 is Runpod's nginx). Stop: `tmux kill-session -t vllm_8011`.
3. **Tunnel** (orbit): tmux `osw_tunnel2` forwards orbit `127.0.0.1:8001` → pod `8011` (separate from `osw_tunnel`, :8000).
   Sanity: `python3 osworld/probe_served.py diagnostic_examples/click-button__s0__imp_step00.png` (8000 vs 8001, temperature 0).
4. **Tasks**: `PYTHONPATH=. ~/osw/venv/bin/python osworld/make_val_tasks.py` refreshes `val_fs_tasks.json` (split_diag tasks with ≥ 1 false-success pass) and `val_ok_tasks.json` (15 always-successful, non-regression) from `~/osw/results_diag*`. Freeze them before launching.
5. **Run** (orbit, needs the operator's go): `bash osworld/run_patched_eval.sh <tag>` → tmux `osw_val_<tag>`, 2 workers per arm, results `~/osw/results_val_{patched,orig}_<tag>/`. Refuses if VMs would exceed 6 or `free -g` available < 14 G.
6. **Compare**: `PYTHONPATH=. ~/osw/venv/bin/python osworld/compare_val.py ~/osw/results_val_patched_<tag> ~/osw/results_val_orig_<tag> --out <f.json>` → success and false-success rates per arm on fs / ok / all, paired delta, bootstrap IC95 over tasks, discordant pairs.
