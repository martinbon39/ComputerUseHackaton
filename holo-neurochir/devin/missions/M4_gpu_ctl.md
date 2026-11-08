You are the infrastructure engineer of a small AI research lab. Job for this session (about 45 minutes): write the GPU infrastructure controller of the lab, `holo-neurochir/infra/gpu_ctl.py`, with unit tests. Our orchestrator will review it and run it for real on our server, with our credentials. You have no credentials and need none: everything you build must work and be tested offline.

## Context
We serve models with vLLM on Modal (one H100 per app, OpenAI-compatible endpoint), on two Modal accounts (CLI profiles `emilejouannet` = account 1 and `martinbon39` = account 2). Two GPU apps matter:
- `holo-vllm` (module `osworld/modal_vllm.py`, function `serve`): Holo-3.1-4B or one of our edited checkpoints. Env `HOLO_CKPT=<subdir of Volume holo-models:/ckpt>` (empty = original `Hcompany/Holo-3.1-4B` at the revision pinned in the module) and `HOLO_NAME=<served model name>`.
- `holo-judge` (module `osworld/modal_judge.py`, function `serve`): Hcompany/Holo4-27B, served as `Holo4-27B`.
- `holo-slot` (account 1 only, a second GPU slot) must be stopped by the budget guard too; `holo-jury-probe` is CPU-only and must never be stopped by the guard.
Endpoint URL: `https://{profile}--{app}-serve.us-east.modal.run/v1`. All endpoints require `Authorization: Bearer <vLLM key>` (on our server the key is in `~/.holo_modal_key`; env `HOLO_VLLM_KEY` overrides). An H100 costs ~4 $/h; a request to an app with 0 running containers cold-starts one (98 to 512 s measured, see `MODAL_COST.md`).

## Inputs
Attached archive `{M4_ARCHIVE_NAME}` (sha256 `{M4_ARCHIVE_SHA256}`, built from commit `{COMMIT}`; check it):
- `osworld/modal_vllm.py`, `osworld/modal_judge.py`: the two Modal apps.
- `osworld/modal_deploy.sh`: how we deploy today and write a manifest; `osworld/modal_deploys/*.json`: every deploy manifest so far (`*.smoke.json` and `*.revision.json` are probe records, not deploy manifests; a deploy manifest has the keys `app`, `account`, `modal_profile`, `url`, `served_model_name`, `checkpoint`).
- `osworld/modal_budget_guard.sh`: the shell budget guard you replace (same spend formula and the same three GPU apps).
- `osworld/MODAL_COST.md`, `MODAL.md`, `MODAL_MANIFEST.md`: costs and setup.
- `fixtures/`: REAL outputs of the Modal CLI 1.6.3 captured on our server today: `<profile>.app_list.json` (`modal app list --json`), `<profile>.billing_today.json` (`modal billing report --for today --json`), `<profile>.billing_since_2026-11-01.json` (`modal billing report --start 2026-11-01 --json`, full days only, empty today), and `modal_cli_help.txt` (help of `app list`, `app stop`, `deploy`, `billing report`).

## What to build: `holo-neurochir/infra/`
`gpu_ctl.py`, Python ≥ 3.9, standard library only, one file. It calls the `modal` CLI through `subprocess` (env `MODAL_PROFILE=<profile>`), never the Modal SDK, and HTTP through `urllib`.
```
python3 gpu_ctl.py [--config accounts.json] [--journal PATH] [--dry-run] [--fixtures DIR] <command>
  status  [--account N]                       apps not stopped (name, state, tasks, created) + cost today per app and per account
  guard   [--account N] [--enforce] [--notify-cmd CMD] [--once | --interval S --max-hours H]
  deploy  MANIFEST.json [--go] [--probe] [--timeout S]
  stop    APP --account N [--go]
  probe   [--account N] [--app APP | --manifest M | --url URL] [--allow-cold-start] [--timeout S]
```
1. **Config** `accounts.json` (ship `accounts.example.json`): per account `profile`, `warn_usd`, `stop_usd`, `budget_start` (date), `gpu_apps` (list); global `vllm_key_file`, `deploys_dir`, `repo_root`. Example values: account 1 warn 20 / stop 24, account 2 warn 27 / stop 29.5, budget_start 2026-11-01.
2. **status**: read-only. Spend of an account = sum of `cost` of `billing report --start <budget_start>` (full days) + sum of `billing report --for today`. Show today's cost per app (group rows by `description`) and the account total vs `warn_usd`/`stop_usd`.
3. **guard**: same spend. Below warn: nothing. At warn: run `--notify-cmd` once with a one-line message (deduplicated across runs through a small state file next to the journal). At stop: without `--enforce`, report `WOULD STOP <apps>` only; with `--enforce`, `modal app stop <app> -y` for each `gpu_apps` app that is not already stopped, then notify. Billing unreadable 3 times in a row for an account: notify. Exit code 0 below warn, 10 at warn, 20 at stop (highest over accounts). `--once` is the default; a loop needs `--max-hours`.
4. **deploy**: from a deploy manifest, rebuild the exact command: app `holo-vllm` → `MODAL_PROFILE=<modal_profile> HOLO_CKPT=<subdir from "holo-models:/ckpt/<subdir>", empty for "Hcompany/...@rev"> HOLO_NAME=<served_model_name> modal deploy osworld/modal_vllm.py`; app `holo-judge` → `modal deploy osworld/modal_judge.py`. For an `Hcompany/...@rev` checkpoint, refuse if `rev` differs from `HF_REV` read from the module source (text parse, no import). Refuse if the module has uncommitted changes (`git diff --quiet -- <module>` in `repo_root`). Without `--go`: print what would run and exit 0, nothing executed. `--probe`: after deploy, poll `/v1/models` until ready or `--timeout` (default 900 s).
5. **stop**: `modal app stop <app> -y` on that account's profile (any app, by exact name); without `--go`, print only. Already stopped or absent: say so, exit 0, run nothing.
6. **probe**: `GET <url>/models` with the bearer key; OK when the served model name (from the manifest, or any id when `--url` is given) is in `data[].id`; report latency. URL from `--url`, `--manifest`, or the newest deploy manifest of `--app` on `--account` (by file name). Before the request, read `app list`: if the app has 0 tasks, refuse unless `--allow-cold-start` (it would start a paid H100).
7. **Journal**: append one JSON line per command to `--journal` (default `holo-neurochir/infra/gpu_ctl.jsonl`): `ts_utc`, `command`, `argv`, `dry_run`, every external command or HTTP request made (or that would be made), its exit code / HTTP status, the decision, the exit code. The key never appears anywhere (stdout, journal, errors, tracebacks); `Authorization` is written as `Bearer <redacted>`.
8. **`--dry-run`**: no subprocess, no network, no file write except the journal. Read commands with `--fixtures DIR` use the recorded outputs (`<profile>.app_list.json`, `<profile>.billing_today.json`, `<profile>.billing_since_<date>.json`); without fixtures they print the commands they would run. Mutating commands print the exact commands (key redacted).
9. **Tests** `test_gpu_ctl.py` (unittest, no network: inject a fake command runner and a fake opener, or a local `http.server` on 127.0.0.1): spend formula on the fixtures (account 1 = 20.16 $, account 2 = 23.18 $ today, 2 decimals); guard thresholds and exit codes 0/10/20 and notify dedup; `--enforce` stops only GPU apps that are running, never `holo-jury-probe`; deploy command rebuilt exactly from `fixtures`-style manifests for both apps, refusal on revision mismatch and on a dirty module; stop and deploy without `--go` execute nothing; probe refuses a 0-task app without `--allow-cold-start`, passes on a fake `/v1/models`, fails on a wrong model name; the key never appears in stdout or the journal; `--dry-run` makes zero subprocess calls.
10. `README.md` (English, short): what it does, the commands, dry-run, exit codes, what it does not do.

## Rules
- No credentials, no Modal account, no spending, no PR, no push to any repository, no message to anyone. Do not install the Modal SDK into the tool; you may install the `modal` CLI to read its help, never log in.
- Do not modify the files of the archive; add only `holo-neurochir/infra/`.
- Run the tests and paste the real output. Do not claim anything you did not run.

## Deliverable
Attach to your final message `gpu_ctl.zip` containing exactly `holo-neurochir/infra/{gpu_ctl.py,test_gpu_ctl.py,accounts.example.json,README.md}`, and the same as `gpu_ctl.patch` (`git diff` creating these files against an empty repo). Structured output:
```json
{
  "mission": "M4",
  "zip_attached": false,
  "patch_attached": false,
  "files": [{"path": "", "sha256": "", "lines": 0}],
  "test_command": "",
  "tests_run": 0,
  "tests_failed": 0,
  "test_output_tail": "",
  "dry_run_example_output": "",
  "known_limits": []
}
```
