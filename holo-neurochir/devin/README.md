# Devin API integration

**Status (2026-11-08):** the Devin API integration is installed and authenticated. One mission, a GPU infrastructure
controller, is written and tested in dry-run. **No Devin session was launched during the hackathon, to preserve
credits: 0 ACU consumed.** Devin wrote no code in this repository, and it runs or manages nothing.

## What exists
| File | Role |
|---|---|
| `devin_client.py` | Devin API client, Python stdlib only. It creates sessions, sends and lists messages, waits, reads structured output, and uploads and downloads attachments. `check-auth` makes a read-only call. `--dry-run` needs no key. |
| `missions/M4_gpu_ctl.md` | The prepared mission. Devin would write `holo-neurochir/infra/gpu_ctl.py` with unit tests: Modal apps and cost of the day per account, budget guard (warn, then stop only with `--enforce`), deploy and stop of the vLLM apps (`holo-vllm`, `holo-judge`) from `osworld/modal_deploys/` manifests, `/v1/models` probe that refuses to cold-start a paid GPU, JSON journal, `--dry-run`. Cap: 6 ACU. |
| `missions/m4_fixtures/` | Real Modal CLI 1.6.3 outputs captured on our server (`app list`, `billing report`, help texts). The mission uses them as offline test data. They contain no credentials. |
| `run_missions.py` | Builds the input archive from git, scans it for secrets, and writes the request. Live mode would launch and follow a session. It also writes `STATUS.json` and the status page. |
| `render_page.py` | Status page "Devin dans le labo". |
| `test_devin.py` | 9 offline tests against a fake Devin server on localhost (`python3 -m unittest test_devin -v`). |

## What was actually run
1. **Authentication check, read-only:** `python3 devin_client.py check-auth` sent `GET /v1/sessions?limit=1`. The key
   is a legacy `apk_` key, so it uses API v1. The call returned `{"api_version": "v1", "authenticated": true}`. It
   creates no session. Per the Devin billing docs, ACUs are consumed only by sessions doing work
   (https://docs.devin.ai/admin/billing/usage). The key is read from `~/.devin_key` and is never printed or written.
2. **Mission dry-run:** `python3 run_missions.py --dry-run --missions M4` built the input archive
   `gpu_ctl_inputs-<commit>.tar.gz`: 63 files, about 30 KB, 0 secret-pattern hits. It also wrote the exact requests
   it would send to `build/M4.dry_run.json`: `POST /v1/attachments`, then `POST /v1/sessions` with
   `max_acu_limit: 6`. Nothing was sent.
3. **Client tests:** `python3 -m unittest test_devin -v`: 9 tests passed. They cover state mapping, key redaction,
   the session flow, a read-only auth check, message pagination and blocked states.

## What was NOT done
- No Devin session was created, so no Devin messages, no Devin-written code and no Devin-produced diff exist.
  `holo-neurochir/infra/gpu_ctl.py` does not exist.
- No PR and no push to any third-party repository.
- The attachment download path (`download`) has been checked only against the docs, never live.
- Missions M1 to M3 (earlier drafts) are not part of this integration and were never launched.

## API notes (checked against docs.devin.ai on 2026-11-08)
- v3: `https://api.devin.ai/v3/organizations/{org_id}/…`, `Authorization: Bearer cog_…`; `GET /v3/self` gives
  `org_id`.
- v1, legacy `apk_` keys: `https://api.devin.ai/v1/…`. Attachments go in the prompt as `ATTACHMENT:"<url>"` lines.
- `POST /sessions` takes `prompt`, `title`, `tags`, `attachment_urls`, `structured_output_schema`, `max_acu_limit`
  and `session_secrets`.
- Messages are paginated with `first` (at most 200) and `after` (cursor). `GET …/attachments` returns a bare list.
- The attachment download answers 307 to a presigned URL, which must be fetched without the bearer header.
- Sending a message to a session needs the `ManageOrgSessions` permission.

## To launch the mission later (spends at most 6 ACU)
```
python3 holo-neurochir/devin/run_missions.py --missions M4      # launches, follows, writes STATUS.json and the page
```
The result must then be reviewed and its tests run on our server before `gpu_ctl.py` touches the real accounts.
Start with `--dry-run`, then a read-only `status`.
