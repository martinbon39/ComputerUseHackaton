# gpu_ctl.py

Controller of the lab's Modal GPU apps (`holo-vllm`, `holo-judge`, `holo-slot`) on the two Modal accounts.
It is one Python 3.9+ file that uses only the standard library. It drives the `modal` CLI through `subprocess` with
`MODAL_PROFILE=<profile>` (never the Modal SDK) and calls the vLLM endpoints through `urllib`. It replaces
`osworld/modal_budget_guard.sh` and `osworld/modal_deploy.sh` for redeploys.

## Setup

    cp accounts.example.json accounts.json   # per account: profile, warn_usd, stop_usd, budget_start, gpu_apps
                                             # global: vllm_key_file, repo_root, deploys_dir (relative to this file)

If `accounts.json` is missing, the tool falls back to `accounts.example.json` and prints a note. The vLLM key comes
from `$HOLO_VLLM_KEY` or, failing that, from `vllm_key_file` (default `~/.holo_modal_key`). Only `probe` and
`deploy --probe` read it.

## Commands

    python3 gpu_ctl.py [--config accounts.json] [--journal PATH] [--dry-run] [--fixtures DIR] <command>
    status [--account N]                     apps not stopped (name, state, tasks, created), today's cost per app,
                                             account spend vs warn/stop. Read-only.
    guard  [--account N] [--enforce] [--notify-cmd CMD] [--once | --interval S --max-hours H]
    deploy MANIFEST.json [--go] [--probe] [--timeout S]
    stop   APP --account N [--go]
    probe  [--account N] [--app APP | --manifest M | --url URL] [--allow-cold-start] [--timeout S]

- **Spend** = sum of `cost` in `modal billing report --start <budget_start> --json` (full days) plus sum of `cost` in
  `modal billing report --for today --json`.
- **guard**: below `warn_usd` it does nothing. At `warn_usd` it runs `CMD "<one-line message>"` once: the message is
  passed as the last argument and no shell is used. Repeats are suppressed through `<journal>.state.json`, keyed by
  account, threshold and budget_start. A notification counts as sent only when CMD exits 0. At `stop_usd` without
  `--enforce`, it prints `WOULD STOP <apps>` and notifies once. With `--enforce`, it runs `modal app stop <app> -y` for
  each `gpu_apps` app that is not already stopped, then notifies. `holo-jury-probe` is never stopped, and the config is
  rejected if `holo-jury-probe` is listed in `gpu_apps`. If billing is unreadable 3 times in a row for an account,
  guard notifies. `--once` is the default. A loop needs `--interval` and `--max-hours` and writes one journal line per
  round.
- **deploy**: rebuilds the command from a deploy manifest, i.e. a JSON file with the keys `app`, `account`,
  `modal_profile`, `url`, `served_model_name` and `checkpoint`. `*.smoke.json` and `*.revision.json` are rejected.
  - `holo-vllm` → `MODAL_PROFILE=p HOLO_CKPT=<subdir or ''> HOLO_NAME=<name> modal deploy osworld/modal_vllm.py`
  - `holo-judge` → `MODAL_PROFILE=p modal deploy osworld/modal_judge.py`

  The command runs in `repo_root`. The deploy is refused when any of these holds:
  - for an `Hcompany/...@rev` checkpoint, the repo id or `rev` differs from `HF_ID`/`HF_REV` in the module source
    (read as text; the module is not imported);
  - `vllm_args` in the manifest differ from `VLLM_ARGS` in the module, so the deploy would not reproduce the manifest;
  - the profile or URL does not match the config;
  - `git diff --quiet -- <module>` or `git diff --quiet --cached -- <module>` fails.

  Without `--go`, deploy prints the command and exits 0. `--probe` polls `<url>/models` until the served name is
  listed or `--timeout` expires (default 900 s).
- **stop**: runs `modal app stop APP -y` on the account's profile. Without `--go`, it only prints the command. If the
  app is already stopped or absent, it says so, runs nothing, and exits 0.
- **probe**: sends `GET <url>/models` with `Authorization: Bearer <key>`. The probe is OK when the served model name is
  in `data[].id`; with `--url`, any id counts. It reports the latency. `--app` uses the newest deploy manifest of that
  app on `--account`, chosen by file name. The probe first reads `modal app list`. If the app has 0 tasks, the probe is
  refused unless `--allow-cold-start` is given, because the request would start a paid H100 (about 4 $/h, 98-512 s
  cold start).

## Read-only vs mutating

Without `--go` (or without `--enforce` for guard), the tool still runs read-only commands: `modal app list`,
`modal billing report`, and `git diff --quiet` for deploy. It runs no `modal deploy` and no `modal app stop`.

## Dry run

`--dry-run` makes no subprocess calls, no network requests and no file writes, except for the journal line. With
`--fixtures DIR`, read commands use `<profile>.app_list.json`, `<profile>.billing_today.json` and
`<profile>.billing_since_<budget_start>.json`. Without fixtures, they print the commands they would run. Mutating
commands print the exact command, with the key redacted. `--fixtures` is refused without `--dry-run`, so the guard can
never act on recorded data.

    python3 gpu_ctl.py --dry-run --fixtures ../../fixtures guard --enforce

## Journal and secrets

Each command appends one JSON line to `--journal` (default `gpu_ctl.jsonl` next to the script). The line contains:
`ts_utc`, `command`, `argv`, `dry_run`, `actions` (each external command or HTTP request, made or planned, with its
exit code or HTTP status), `decision` and `exit_code`.

The key is redacted from stdout, stderr and the journal. `Authorization` is written as `Bearer <redacted>`. No
traceback is ever printed. These variables are not passed to child processes: `MODAL_TOKEN_ID`, `MODAL_TOKEN_SECRET`
(they would override the profile), `HOLO_VLLM_KEY`, and any inherited `HOLO_*`.

## Exit codes

| code | meaning |
|---|---|
| 0 | ok, below warn, or plan only |
| 1 | a command or probe failed |
| 2 | refused or usage/config error |
| 3 | billing unreadable (guard/status) |
| 10 | at warn (guard: highest over accounts) |
| 20 | at stop |

## What it does not do

- It does not create Modal apps, Secrets or Volumes, and it does not upload checkpoints.
- It does not write a new deploy manifest; use `modal_deploy.sh` for a first deploy.
- It does not check the budget before a deploy.
- It does not close the jury gate (`modal_jury_gate.sh`) as the old guard did.
- It does not log in or store any Modal token.

## Tests

    python3 -m unittest -v test_gpu_ctl.py

The tests run offline. They use a fake command runner, a fake opener and a local `http.server` on 127.0.0.1, together
with `../../fixtures` and `../../osworld` (override the location with `GPU_CTL_REPO_ROOT`).
