# Devin session that wrote `infra/` (mission M4)

| | |
|---|---|
| Devin session | `devin-13e97ca8040d4fe789ae006a61f0705b` (Devin API v1, tags `holo-lab`, `M4`) |
| Date | 2026-11-08, created 10:51:07 UTC, last Devin message 10:59:46 UTC, status `finished` at 11:05 UTC |
| ACU consumed | **not reported by the API.** `GET /v1/sessions/{id}` and `GET /v1/sessions` return no ACU field, and the usage paths we tried answer 404. The session was capped at `max_acu_limit: 6`. |
| Input | `gpu_ctl_inputs-1a657617794f.tar.gz` (sha256 `b85d0e38…2b30`, 30 218 bytes): Modal CLI fixtures, `osworld/` modules, deploy manifests and cost notes at commit `1a657617`. Devin had no credentials. |
| Output | 2 attachments, `gpu_ctl.zip` and `gpu_ctl.patch`, downloaded through `GET https://api.devin.ai/v1/attachments/<uuid>/<name>`. The `app.devin.ai/attachments/...` links in the message answer 401 to an API key. |
| Review and real run | session `devin-review` of the argos fleet (Claude Opus 5.5), 2026-11-08 11:42-11:50 UTC |

## What Devin wrote

The four files in this folder are committed as Devin delivered them, without any edit:

| file | lines | sha256 (announced in `structured_output` = zip = patch) |
|---|---|---|
| `gpu_ctl.py` | 900 | `546398f13373f1ce822e4c85db1e54baa3a0e51012032a14fe8dca1b769d46ef` |
| `test_gpu_ctl.py` | 676 | `bc9c7802f67ee214c177cceaa270d21642304d50d80468502beeb5d14a32e892` |
| `README.md` | 108 | `1140236adf8c55631fb8de438ea727511b68f24c158bcff832329ff84f9638a9` |
| `accounts.example.json` | 11 | `58e934cd1d85899afa69de7f87800ddb39c4289b74a6a374ee2b09f776953cb2` |

The zip and the patch contain the same four files, and all four hashes match the ones Devin announced.

`gpu_ctl.py` is a Python standard-library CLI that controls the lab's Modal vLLM apps on two accounts:
- `status`: apps that are not stopped, cost of the day per app, spend against the warn and stop thresholds;
- `guard`: budget guard that notifies at warn and stops the GPU apps at stop only with `--enforce`;
- `deploy`: redeploys exactly what a deploy manifest describes, only with `--go`;
- `stop`: `modal app stop` on one account, only with `--go`;
- `probe`: `GET /v1/models` on an endpoint, refused when the app has 0 containers (a probe would cold-start a paid H100);
- a JSONL journal and a `--dry-run` mode.

## Review findings (before anything was run)

**Secrets: no problem found.**
- The vLLM key is read only by `probe` and `deploy --probe`. It is redacted from stdout, stderr and the journal, the
  `Authorization` header is journaled as `Bearer <redacted>`, and no traceback is ever printed. The test
  `test_key_never_in_stdout_stderr_or_journal` covers this.
- Child processes do not inherit `MODAL_TOKEN_ID/SECRET`, `MODAL_PROFILE`, `HOLO_VLLM_KEY`, `HOLO_CKPT`, `HOLO_NAME` or
  `HOLO_SCALEDOWN`.
- `status` never reads the key.

**Network: only Modal and our endpoints.**
- Modal is reached only through the `modal` CLI, as a subprocess with `MODAL_PROFILE`.
- HTTP goes only to the endpoint URL of a manifest or of `--url`. Redirects are followed on the same host only.
- There is no other host, telemetry or upload anywhere in the code.
- The notify command is whatever the operator passes with `--notify-cmd`, run without a shell.
- One operator caveat: `probe --url <URL> --allow-cold-start` sends the bearer key to any URL typed by the operator. Without
  `--allow-cold-start`, a URL outside `https://<profile>--<app>-serve.us-east.modal.run/v1` is refused.

**Destructive actions: none by default.**
- `modal deploy` runs only with `deploy ... --go`, `modal app stop` only with `stop ... --go` or `guard --enforce`.
- `holo-jury-probe` can never be stopped by the guard.
- `--dry-run` spawns no subprocess and makes no network call; tests check this with a runner that raises.
- Without `--go`, read-only commands still run (`modal app list`, `modal billing report`, `git diff --quiet`).
- Without `--enforce`, the guard still sends notifications. A notification is outward-facing but changes nothing.

**Minor points (no fix needed for the read-only use):**
- The README and the comment say "any inherited `HOLO_*`" is stripped, but the code strips the four names listed above.
  `osworld/modal_vllm.py` and `modal_judge.py` read only `HOLO_CKPT`, `HOLO_NAME` and `HOLO_SCALEDOWN`, so nothing reaches
  a deploy through that gap.
- `test_newest_manifest_selected` pins the newest manifest of the frozen input bundle. Against today's
  `osworld/modal_deploys/` it fails, because `20261108T105705_acct1_Holo-3.1-4B-modal-orig.json` was written after the
  bundle was frozen. The code picks that newer file, which is the correct choice; the test is tied to the snapshot.
- The tests need `<repo_root>/fixtures`, which only the input bundle contains. Set `GPU_CTL_REPO_ROOT` to an extracted
  copy of the bundle.
- `accounts.example.json` keeps account 1 at stop 24 $. Martin raised that cap to 28 $ (`osworld/MODAL_COST.md`). The real
  `accounts.json` must say 28 before `guard --enforce` is used. `accounts.json` and the journal are not tracked
  (`.gitignore`).

## Real outputs on the argos server (Python 3.14.4, modal client 1.6.3)

### Tests

```
$ GPU_CTL_REPO_ROOT=<extracted input bundle> python3 -m unittest -v test_gpu_ctl.py
...
test_already_stopped_or_absent (test_gpu_ctl.StopTest.test_already_stopped_or_absent) ... ok
test_stop_with_go (test_gpu_ctl.StopTest.test_stop_with_go) ... ok
test_stop_without_go_executes_nothing (test_gpu_ctl.StopTest.test_stop_without_go_executes_nothing) ... ok
----------------------------------------------------------------------
Ran 39 tests in 0.596s

OK
```

Against today's `osworld/` instead of the bundle: 38/39, with the one failure explained above.

### Dry run (fixtures of the bundle, example config)

```
$ python3 gpu_ctl.py --dry-run --fixtures <bundle>/fixtures guard --enforce --notify-cmd "argos send ares"
DRY RUN: no subprocess, no network, fixtures from <bundle>/fixtures
account 1 (emilejouannet): 20.16 $  (warn 20.00, stop 24.00)  -> WARN
  would run: argos send ares 'gpu_ctl guard: account 1 (emilejouannet) at 20.16 $ >= warn 20.00 $; automatic stop at 24.00 $'
account 2 (martinbon39): 23.18 $  (warn 27.00, stop 29.50)  -> OK
exit 10

$ python3 gpu_ctl.py --dry-run stop holo-vllm --account 1 --go
DRY RUN: no subprocess, no network
  would run: MODAL_PROFILE=emilejouannet modal app list --json
  would run: MODAL_PROFILE=emilejouannet modal app stop holo-vllm -y
exit 0
```

### One real read-only command on both Modal accounts (2026-11-08 11:44 UTC)

The command ran with the CLI profiles of `~/.modal.toml` and the current caps (account 1 warn 25 / stop 28 $, account 2
warn 27 / stop 29.5 $). Amounts are rounded to 0.1 $ and app ids are shortened.

```
$ python3 gpu_ctl.py --config accounts.json status
account 1 (emilejouannet)  budget since 2026-11-01
  apps not stopped:
    holo-vllm          deployed   tasks=0  created 2026-11-08 09:37:33+00:00  ap-…
  cost today per app:
    holo-vllm             22.6 $
    holo-slot              0.3 $
  spend: full days 0.0 + today 22.9 = 22.9 $  (warn 25.00, stop 28.00)  -> OK
account 2 (martinbon39)  budget since 2026-11-01
  apps not stopped:
    holo-jury-probe    deployed   tasks=0  created 2026-11-08 06:51:58+00:00  ap-…
  cost today per app:
    holo-vllm             15.3 $
    holo-judge             8.8 $
    holo-slot              0.0 $
    holo-jury-probe        0.0 $
  spend: full days 0.0 + today 24.1 = 24.1 $  (warn 27.00, stop 29.50)  -> OK
exit 0
```

- The journal shows 6 subprocesses, all read-only and all with rc 0: `modal app list --json`,
  `modal billing report --start 2026-11-01 --json` and `modal billing report --for today --json`, on each profile.
- No stop, no deploy, no HTTP request.
- Check of the spend formula: `modal billing report --for "this month"` gives the same totals, 22.9 $ and 24.1 $. "Full
  days 0" is correct, because both accounts started spending on 2026-11-08 at 00:14 UTC (`osworld/MODAL_COST.md`).
- During the manual check, one raw `modal billing report` call returned an empty stdout once, then valid JSON. In that
  case `gpu_ctl` reports "billing unreadable" (exit 3), and the guard notifies after 3 such rounds in a row.
