# Online validation of a patched 4B (runbook)

Goal: from a CANDIDATE `patch_spec.json` to both OSWorld arms running in < 10 min. Pod = `ssh -i ~/.ssh/runpod_holo -p 15780 root@213.181.111.151`.

1. **Checkpoint** (pod, ~2 min):
   `cd /workspace/projet && PYTHONPATH=. HF_HOME=/workspace/hf HF_HUB_OFFLINE=1 HOLO_MODEL=Hcompany/Holo-3.1-4B /workspace/venv/bin/python scripts/make_patched_ckpt.py <spec.json> /workspace/ckpt/<tag>`
   Spec kinds (details in the script docstring):
   - `surgery` (default, `holo/surgery.py` format): projection removal on the writers of the listed layers (e.g. 2-3 late layers; `alpha` > 1 pushes the component negative). A constant vector subtraction is not compilable: the writers have no bias.
   - `steering`: `{"kind": "steering", "direction_file", "layers": [l], "alpha"}`, the hook compiled into the writers of layers 0..l (approximate).
   - `lm_head`: `{"kind": "lm_head", "tokens": ["answer"], "delta_file": <npz "delta" [n, d] or [d]>, "alpha"}`, lm_head rows += alpha * delta; the checkpoint is untied (`tie_word_embeddings=false`, the snapshot already stores `lm_head.weight` == embeddings), input embeddings unchanged. `answer` = token 8944 in both `<function=answer>` and `"name": "answer"`, but a row edit acts at every position, not only at the tool name.
   `patch_manifest.json` lists the edited tensors, their relative change and changed rows.
   Independent check: `scripts/check_ckpt_equiv.py /workspace/ckpt/<tag> /workspace/ckpt/_tests/probe.png [--device cpu --no_generate]` → differing tensors/rows, config diff, next-token logits moved, HF outputs (GPU ~4 min; CPU logits-only ~8 min).
2. **Serve** (pod, ~2 min): `bash /workspace/projet/osworld/serve_patched.sh /workspace/ckpt/<tag>` → tmux `vllm_8011`, name `Holo-3.1-4B-patched`, `--gpu-memory-utilization 0.15`, pod port 8011 (the pod's 8001 is Runpod's nginx). Stop: `tmux kill-session -t vllm_8011`.
3. **Tunnel** (orbit): tmux `osw_tunnel2` forwards orbit `127.0.0.1:8001` → pod `8011` (separate from `osw_tunnel`, :8000).
   Sanity: `python3 osworld/probe_served.py diagnostic_examples/click-button__s0__imp_step00.png --ref osworld/probe_ref_vllm.json` (8001 vs saved vLLM answers of the null checkpoint, temperature 0; `--a` instead compares with production 8000, which varies under load).
4. **Tasks**: `PYTHONPATH=. ~/osw/venv/bin/python osworld/make_val_tasks.py` (rerun once diag pass 2 is done) writes
   - `val_confirm_tasks.json`: main arm, all 45 tasks of `confirm_tasks.json` (frozen by ares, sha256 `03726f07b411…` checked, never used to build an intervention), tagged fs / ok / other from the diag passes in `val_tasks_provenance.json`;
   - `val_fs_insample_tasks.json`: secondary, **in-sample** — every split_diag task with ≥ 1 false-success pass (11 of them are also in confirm).
5. **Run** (orbit, needs ares' go): `bash osworld/run_patched_eval.sh <tag> confirm [workers=3]` (or `fs_insample`) → tmux `osw_val_<tag>`, results `~/osw/results_val_{patched,orig}_<tag>/`, task list frozen as `~/osw/val_<tag>.json`. Refuses if VMs would exceed 6 or `free -g` available < 14 G (3 workers per arm needs no other VM running).
   Progress: `bash osworld/watch_val.sh <tag> stuck|other [agent=ares] [every=10]` (in a tmux) sends the confirm block of compare_val every 10 new pairs and at the end.
6. **Compare**: `PYTHONPATH=. ~/osw/venv/bin/python osworld/compare_val.py ~/osw/results_val_patched_<tag> ~/osw/results_val_orig_<tag> --origin stuck|other --out <f.json>` (`stuck` = built by astra-stuck or combining a stuck edit: confirm = odd half of sha1("domain/example_id") only, FLEET_ORDERS.md) → in priority order paired success, false-success share, mean steps and share reaching 50 steps, per arm on all / confirm / confirm:{fs,ok,other} / insample (fs outside confirm; biased by regression to the mean), paired delta, bootstrap IC95 over tasks, discordant pairs.
