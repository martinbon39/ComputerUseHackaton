#!/usr/bin/env python3
"""GPU infrastructure controller of the lab: Modal vLLM apps on two accounts (status, budget guard, deploy, stop, probe).

Standard library only. Talks to Modal through the `modal` CLI (subprocess, env MODAL_PROFILE=<profile>), never the SDK,
and to the vLLM endpoints through urllib. Every command appends one JSON line to the journal. The vLLM key never
appears in any output: it is redacted from stdout, stderr and the journal, and no traceback is ever printed.

  python3 gpu_ctl.py [--config accounts.json] [--journal PATH] [--dry-run] [--fixtures DIR] <command> ...
  status [--account N] | guard [...] | deploy MANIFEST.json [...] | stop APP --account N [--go] | probe [...]

Exit codes: 0 ok / below warn, 1 failure, 2 refused or usage error, 3 billing unreadable, 10 warn, 20 stop.
"""
from __future__ import annotations

import argparse
import ast
import datetime as dt
import json
import os
import re
import shlex
import subprocess
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from decimal import Decimal, InvalidOperation
from pathlib import Path

HERE = Path(__file__).resolve().parent
DEFAULT_JOURNAL = HERE / "gpu_ctl.jsonl"
DEFAULT_CONFIG = HERE / "accounts.json"
EXAMPLE_CONFIG = HERE / "accounts.example.json"

EXIT_OK, EXIT_FAIL, EXIT_REFUSED, EXIT_BILLING, EXIT_WARN, EXIT_STOP = 0, 1, 2, 3, 10, 20
NEVER_GUARD_STOP = frozenset({"holo-jury-probe"})  # CPU-only: the guard never stops it, whatever the config says
APP_MODULES = {"holo-vllm": "osworld/modal_vllm.py", "holo-judge": "osworld/modal_judge.py"}
URL_FMT = "https://{profile}--{app}-serve.us-east.modal.run/v1"
URL_RE = re.compile(r"^https://([A-Za-z0-9_]+(?:-[A-Za-z0-9_]+)*?)--([a-z0-9-]+)-serve\.us-east\.modal\.run/v1/?$")
DEPLOY_KEYS = ("app", "account", "modal_profile", "url", "served_model_name", "checkpoint")
VOLUME_PREFIX = "holo-models:/ckpt/"
CKPT_SUBDIR_RE = re.compile(r"^[A-Za-z0-9._-]+(?:/[A-Za-z0-9._-]+)*$")
# Never inherited by a child process: tokens in the environment would override MODAL_PROFILE (wrong account),
# the vLLM key is not needed by any child, and HOLO_* must come from the manifest only.
STRIPPED_ENV = ("MODAL_TOKEN_ID", "MODAL_TOKEN_SECRET", "MODAL_PROFILE", "HOLO_VLLM_KEY",
                "HOLO_CKPT", "HOLO_NAME", "HOLO_SCALEDOWN")
REDACTED = "<redacted>"
AUTH_REDACTED = "Bearer " + REDACTED
MODAL_TIMEOUT_S = 90
DEPLOY_TIMEOUT_S = 1800
UNREADABLE_NOTIFY_AFTER = 3


class GpuCtlError(Exception):
    def __init__(self, msg, code=EXIT_REFUSED):
        super().__init__(msg)
        self.code = code


# ---------------------------------------------------------------- config

def load_config(path):
    path = Path(path).expanduser().resolve()
    try:
        raw = json.loads(path.read_text())
    except (OSError, ValueError) as e:
        raise GpuCtlError(f"cannot read config {path}: {e}")
    base = path.parent
    repo_root = (base / os.path.expanduser(raw.get("repo_root", "."))).resolve()
    cfg = {
        "path": str(path),
        "repo_root": repo_root,
        "deploys_dir": (repo_root / os.path.expanduser(raw.get("deploys_dir", "osworld/modal_deploys"))).resolve(),
        "vllm_key_file": Path(os.path.expanduser(raw.get("vllm_key_file", "~/.holo_modal_key"))),
        "accounts": {},
    }
    accounts = raw.get("accounts")
    if not isinstance(accounts, dict) or not accounts:
        raise GpuCtlError(f"{path}: 'accounts' must be a non-empty object")
    for n, a in accounts.items():
        try:
            acct = {
                "n": str(n), "profile": str(a["profile"]),
                "warn_usd": Decimal(str(a["warn_usd"])), "stop_usd": Decimal(str(a["stop_usd"])),
                "budget_start": dt.date.fromisoformat(str(a["budget_start"])).isoformat(),
                "gpu_apps": [str(x) for x in a["gpu_apps"]],
            }
        except (KeyError, TypeError, ValueError, InvalidOperation) as e:
            raise GpuCtlError(f"{path}: account {n}: invalid or missing field ({e!r})")
        if not re.fullmatch(r"[A-Za-z0-9_-]+", acct["profile"]):
            raise GpuCtlError(f"{path}: account {n}: invalid profile name")
        if acct["warn_usd"] > acct["stop_usd"]:
            raise GpuCtlError(f"{path}: account {n}: warn_usd > stop_usd")
        bad = NEVER_GUARD_STOP.intersection(acct["gpu_apps"])
        if bad:
            raise GpuCtlError(f"{path}: account {n}: {sorted(bad)} is CPU-only and cannot be a gpu_app")
        cfg["accounts"][str(n)] = acct
    return cfg


def pick_accounts(cfg, n):
    if n is None:
        return list(cfg["accounts"].values())
    if str(n) not in cfg["accounts"]:
        raise GpuCtlError(f"unknown account {n} (config has {', '.join(cfg['accounts'])})")
    return [cfg["accounts"][str(n)]]


def account_by_profile(cfg, profile):
    for a in cfg["accounts"].values():
        if a["profile"] == profile:
            return a
    return None


# ---------------------------------------------------------------- execution context

def render(argv, env=None):
    pre = " ".join(f"{k}={shlex.quote(v)}" for k, v in (env or {}).items())
    cmd = " ".join(shlex.quote(a) for a in argv)
    return f"{pre} {cmd}" if pre else cmd


def default_runner(argv, env, cwd, timeout):
    try:
        p = subprocess.run(argv, env=env, cwd=cwd, capture_output=True, text=True, timeout=timeout)
        return p.returncode, p.stdout, p.stderr
    except FileNotFoundError as e:
        return 127, "", f"not found: {e.filename}"
    except subprocess.TimeoutExpired:
        return 124, "", f"timeout after {timeout} s"


class _SameHostRedirect(urllib.request.HTTPRedirectHandler):
    """Follow redirects on the same host only, so the Authorization header never leaves the endpoint's host."""

    def redirect_request(self, req, fp, code, msg, headers, newurl):
        if urllib.parse.urlsplit(newurl).netloc != urllib.parse.urlsplit(req.full_url).netloc:
            return None
        return super().redirect_request(req, fp, code, msg, headers, newurl)


def default_opener(req, timeout):
    return urllib.request.build_opener(_SameHostRedirect).open(req, timeout=timeout)


class Ctx:
    def __init__(self, cfg, dry_run=False, fixtures=None, runner=None, opener=None, out=None, err=None,
                 environ=None, sleep=time.sleep, clock=time.monotonic):
        self.cfg = cfg
        self.dry_run = dry_run
        self.fixtures = Path(fixtures) if fixtures else None
        self.runner = runner or default_runner
        self.opener = opener or default_opener
        self._out = out or sys.stdout
        self._err = err or sys.stderr
        self.environ = dict(os.environ if environ is None else environ)
        self.sleep = sleep
        self.clock = clock
        self.secrets = []
        self.actions = []

    # -- output, always redacted
    def red(self, s):
        s = str(s)
        for sec in self.secrets:
            if sec:
                s = s.replace(sec, REDACTED)
        return s

    def say(self, msg=""):
        print(self.red(msg), file=self._out, flush=True)

    def warn(self, msg):
        print(self.red(msg), file=self._err, flush=True)

    # -- secrets
    def vllm_key(self):
        key = self.environ.get("HOLO_VLLM_KEY", "").strip()
        if not key:
            try:
                key = self.cfg["vllm_key_file"].read_text().strip()
            except OSError:
                key = ""
        if not key:
            raise GpuCtlError(f"no vLLM key: set HOLO_VLLM_KEY or fill {self.cfg['vllm_key_file']}")
        if key not in self.secrets:
            self.secrets.append(key)
        return key

    # -- subprocess
    def child_env(self, overrides):
        env = {k: v for k, v in self.environ.items() if k not in STRIPPED_ENV}
        env.update(overrides)
        return env

    def run(self, argv, env=None, cwd=None, timeout=MODAL_TIMEOUT_S, execute=True):
        """Run (or, in dry-run / when execute is False, only show and journal) one external command."""
        env = dict(env or {})
        action = {"type": "cmd", "cmd": render(argv, env), "cwd": str(cwd) if cwd else None,
                  "executed": False, "rc": None}
        self.actions.append(action)
        if self.dry_run or not execute:
            self.say(f"  would run: {action['cmd']}" + (f"   (in {cwd})" if cwd else ""))
            return None
        rc, out, err = self.runner(list(argv), env=self.child_env(env), cwd=str(cwd) if cwd else None,
                                   timeout=timeout)
        action.update(executed=True, rc=rc)
        if rc != 0 and err:
            action["stderr_tail"] = self.red(err.strip()[-300:])
        return rc, out, err

    def modal_json(self, profile, args, fixture_name):
        """Read-only `modal ... --json`. Returns (data, why): data None when unreadable or unknown (dry-run)."""
        argv = ["modal", *args, "--json"]
        env = {"MODAL_PROFILE": profile}
        if self.dry_run and self.fixtures:
            fx = self.fixtures / fixture_name
            self.actions.append({"type": "fixture", "cmd": render(argv, env), "fixture": str(fx), "executed": False})
            try:
                return json.loads(fx.read_text()), None
            except (OSError, ValueError) as e:
                return None, f"fixture {fx}: {e}"
        res = self.run(argv, env=env)
        if res is None:
            return None, "dry-run"
        rc, out, err = res
        if rc != 0:
            return None, f"exit {rc}"
        try:
            return json.loads(out), None
        except ValueError:
            return None, "invalid JSON"

    # -- HTTP
    def http_get(self, url, key, timeout, execute=True):
        action = {"type": "http", "method": "GET", "url": url, "headers": {"Authorization": AUTH_REDACTED},
                  "executed": False, "status": None}
        self.actions.append(action)
        if self.dry_run or not execute:
            self.say(f"  would request: GET {url}  (Authorization: {AUTH_REDACTED})")
            return None
        req = urllib.request.Request(url, headers={"Authorization": f"Bearer {key}", "Accept": "application/json"})
        t0 = self.clock()
        status, body, error = None, b"", None
        try:
            resp = self.opener(req, timeout=timeout)
            try:
                status = getattr(resp, "status", None) or resp.getcode()
                body = resp.read(1 << 20)
            finally:
                close = getattr(resp, "close", None)
                if close:
                    close()
        except urllib.error.HTTPError as e:
            status, error = e.code, f"HTTP {e.code}"
        except (urllib.error.URLError, OSError, ValueError) as e:
            error = type(e).__name__ + ": " + str(getattr(e, "reason", e))
        latency = round(self.clock() - t0, 3)
        action.update(executed=True, status=status, latency_s=latency)
        if error:
            action["error"] = self.red(error)
        return status, body, latency, error


# ---------------------------------------------------------------- Modal readers

def live_apps(app_list):
    """Entries of `modal app list --json` that are not stopped."""
    return [a for a in app_list if isinstance(a, dict) and str(a.get("state", "")).lower() != "stopped"]


def tasks_of(entry):
    try:
        return int(entry.get("tasks") or 0)
    except (TypeError, ValueError):
        return 0


def read_app_list(ctx, acct):
    data, why = ctx.modal_json(acct["profile"], ["app", "list"], f"{acct['profile']}.app_list.json")
    if data is not None and not isinstance(data, list):
        return None, "unexpected app list format"
    return data, why


def sum_billing(rows):
    if not isinstance(rows, list):
        raise ValueError("billing report is not a list")
    total, per_app = Decimal(0), {}
    for r in rows:
        c = Decimal(str(r["cost"]))
        total += c
        name = str(r.get("description") or r.get("object_id") or "?")
        per_app[name] = per_app.get(name, Decimal(0)) + c
    return total, per_app


def read_spend(ctx, acct):
    """Spend = sum(cost) of `billing report --start <budget_start>` (full days) + sum(cost) of `--for today`.

    Returns a dict with status 'ok', 'unreadable' or 'unknown' (dry-run without fixtures)."""
    p, start = acct["profile"], acct["budget_start"]
    since, why1 = ctx.modal_json(p, ["billing", "report", "--start", start], f"{p}.billing_since_{start}.json")
    today, why2 = ctx.modal_json(p, ["billing", "report", "--for", "today"], f"{p}.billing_today.json")
    if why1 == "dry-run" or why2 == "dry-run":
        return {"status": "unknown"}
    if since is None or today is None:
        return {"status": "unreadable", "why": why1 or why2}
    try:
        s_total, _ = sum_billing(since)
        t_total, per_app = sum_billing(today)
    except (KeyError, TypeError, ValueError, InvalidOperation, AttributeError) as e:
        return {"status": "unreadable", "why": f"bad billing rows: {e!r}"}
    return {"status": "ok", "since": s_total, "today": t_total, "total": s_total + t_total, "today_per_app": per_app}


def money(d):
    return f"{Decimal(d).quantize(Decimal('0.01'))}"


def level_of(acct, total):
    if total >= acct["stop_usd"]:
        return "STOP", EXIT_STOP
    if total >= acct["warn_usd"]:
        return "WARN", EXIT_WARN
    return "OK", EXIT_OK


# ---------------------------------------------------------------- status

def cmd_status(ctx, args, rec):
    code = EXIT_OK
    for acct in pick_accounts(ctx.cfg, args.account):
        ctx.say(f"account {acct['n']} ({acct['profile']})  budget since {acct['budget_start']}")
        apps, why = read_app_list(ctx, acct)
        if apps is None:
            ctx.say(f"  apps: {'not read (dry run)' if why == 'dry-run' else 'unreadable: ' + why}")
        else:
            live = live_apps(apps)
            ctx.say("  apps not stopped:" + ("" if live else " none"))
            for a in live:
                ctx.say(f"    {a.get('description', '?'):<18} {a.get('state', '?'):<10} tasks={tasks_of(a)}  "
                        f"created {a.get('created_at', '?')}  {a.get('app_id', '')}")
        sp = read_spend(ctx, acct)
        entry = {"account": acct["n"], "spend_status": sp["status"]}
        if sp["status"] == "ok":
            ctx.say("  cost today per app:")
            for name, c in sorted(sp["today_per_app"].items(), key=lambda kv: -kv[1]):
                ctx.say(f"    {name:<18} {money(c):>8} $")
            lvl, _ = level_of(acct, sp["total"])
            ctx.say(f"  spend: full days {money(sp['since'])} + today {money(sp['today'])} = {money(sp['total'])} $"
                    f"  (warn {money(acct['warn_usd'])}, stop {money(acct['stop_usd'])})  -> {lvl}")
            entry.update(total_usd=money(sp["total"]), today_usd=money(sp["today"]), level=lvl,
                         today_per_app={k: money(v) for k, v in sp["today_per_app"].items()})
        elif sp["status"] == "unknown":
            ctx.say("  spend: not read (dry run without --fixtures)")
        else:
            ctx.say(f"  spend: billing unreadable ({sp['why']})")
            code = EXIT_BILLING
        rec.setdefault("accounts", []).append(entry)
    rec["decision"] = "status"
    return code


# ---------------------------------------------------------------- guard

def state_path(journal):
    return Path(journal).with_suffix(".state.json")


def load_state(path):
    try:
        st = json.loads(Path(path).read_text())
        if isinstance(st, dict):
            st.setdefault("notified", {})
            st.setdefault("fails", {})
            return st
    except (OSError, ValueError):
        pass
    return {"notified": {}, "fails": {}}


def save_state(ctx, path, st):
    if ctx.dry_run:
        return
    tmp = Path(str(path) + ".tmp")
    tmp.write_text(json.dumps(st, indent=1, sort_keys=True))
    os.replace(tmp, path)


def notify(ctx, notify_cmd, msg):
    """Run `<notify-cmd> <message>` (message as the last argument, no shell). True when delivered."""
    if not notify_cmd:
        ctx.say(f"  NOTIFY (no --notify-cmd): {msg}")
        return False
    res = ctx.run(shlex.split(notify_cmd) + [msg], timeout=60)
    if res is None:
        return False
    if res[0] != 0:
        ctx.warn(f"notify command failed (exit {res[0]})")
    return res[0] == 0


def guard_round(ctx, args, st):
    worst, decisions = EXIT_OK, {}
    for acct in pick_accounts(ctx.cfg, args.account):
        n, p = acct["n"], acct["profile"]
        sp = read_spend(ctx, acct)
        if sp["status"] == "unknown":
            ctx.say(f"account {n} ({p}): spend not read (dry run without --fixtures)")
            decisions[n] = "unknown"
            continue
        if sp["status"] == "unreadable":
            fails = int(st["fails"].get(n, 0)) + 1
            st["fails"][n] = fails
            ctx.say(f"account {n} ({p}): billing unreadable ({sp['why']}), {fails} in a row")
            if fails == UNREADABLE_NOTIFY_AFTER:
                notify(ctx, args.notify_cmd, f"gpu_ctl guard: billing of account {n} ({p}) unreadable "
                                             f"{fails} times in a row; spend unknown")
            decisions[n] = f"billing unreadable x{fails}"
            worst = max(worst, EXIT_BILLING)
            continue
        st["fails"][n] = 0
        total, warn_usd, stop_usd = sp["total"], acct["warn_usd"], acct["stop_usd"]
        lvl, code = level_of(acct, total)
        worst = max(worst, code)
        ctx.say(f"account {n} ({p}): {money(total)} $  (warn {money(warn_usd)}, stop {money(stop_usd)})  -> {lvl}")
        if lvl == "OK":
            decisions[n] = f"ok {money(total)}"
            continue
        warn_key = f"{n}:warn:{warn_usd}:{acct['budget_start']}"
        stop_key = f"{n}:stop:{stop_usd}:{acct['budget_start']}"
        if lvl == "WARN":
            decisions[n] = f"warn {money(total)}"
            if warn_key in st["notified"]:
                ctx.say("  warning already sent")
            elif notify(ctx, args.notify_cmd, f"gpu_ctl guard: account {n} ({p}) at {money(total)} $ "
                                              f">= warn {money(warn_usd)} $; automatic stop at {money(stop_usd)} $"):
                st["notified"][warn_key] = dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds")
            continue
        apps, why = read_app_list(ctx, acct)
        if apps is None:
            targets = [a for a in acct["gpu_apps"] if a not in NEVER_GUARD_STOP]
            ctx.say(f"  app list not read ({why}): every gpu app is a target")
        else:
            live = {a.get("description") for a in live_apps(apps)}
            targets = [a for a in acct["gpu_apps"] if a in live and a not in NEVER_GUARD_STOP]
        if not args.enforce:
            ctx.say(f"  WOULD STOP {' '.join(targets) if targets else '(nothing running)'}  (no --enforce)")
            decisions[n] = f"would stop {targets} at {money(total)}"
            if stop_key not in st["notified"] and notify(
                    ctx, args.notify_cmd, f"gpu_ctl guard: account {n} ({p}) at {money(total)} $ >= stop "
                                          f"{money(stop_usd)} $; WOULD STOP {' '.join(targets) or 'nothing'} "
                                          f"(guard not enforcing)"):
                st["notified"][stop_key] = dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds")
            continue
        results = []
        for app in targets:
            res = ctx.run(["modal", "app", "stop", app, "-y"], env={"MODAL_PROFILE": p})
            rc = None if res is None else res[0]
            results.append(f"{app}:{'planned' if rc is None else ('stopped' if rc == 0 else f'FAILED rc={rc}')}")
            ctx.say(f"  stop {app}: {results[-1].split(':', 1)[1]}")
        decisions[n] = f"stop {results} at {money(total)}"
        if (targets or stop_key not in st["notified"]) and notify(
                ctx, args.notify_cmd, f"gpu_ctl guard: account {n} ({p}) at {money(total)} $ >= stop "
                                      f"{money(stop_usd)} $; {', '.join(results) if results else 'nothing running'}"):
            st["notified"][stop_key] = dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds")
    return worst, decisions


def cmd_guard(ctx, args, rec, journal, write_journal):
    if args.interval is not None and args.max_hours is None:
        raise GpuCtlError("guard --interval needs --max-hours")
    if args.max_hours is not None and args.interval is None:
        raise GpuCtlError("guard --max-hours needs --interval")
    if args.interval is not None and (args.interval <= 0 or args.max_hours <= 0):
        raise GpuCtlError("--interval and --max-hours must be > 0")
    spath = state_path(journal)
    if args.interval is None:
        st = load_state(spath)
        code, decisions = guard_round(ctx, args, st)
        save_state(ctx, spath, st)
        rec["decision"] = decisions
        return code
    start, worst, i = ctx.clock(), EXIT_OK, 0
    end = start + args.max_hours * 3600
    while True:
        i += 1
        st = load_state(spath)
        code, decisions = guard_round(ctx, args, st)
        save_state(ctx, spath, st)
        worst = max(worst, code)
        rec.update(round=i, decision=decisions)
        remaining = end - ctx.clock()
        if remaining <= 0:
            return worst
        write_journal(rec, code)  # one journal line per round; the last round is written by main()
        rec.clear()
        ctx.actions.clear()
        ctx.sleep(min(args.interval, remaining))
        if ctx.clock() >= end:
            rec.update(round=i, decision="max-hours reached")
            return worst


# ---------------------------------------------------------------- deploy

def is_deploy_manifest(d):
    return isinstance(d, dict) and all(k in d for k in DEPLOY_KEYS)


def module_constant(src, name):
    m = re.search(rf"^{name}\s*=\s*([\"'])([^\"'\n]*)\1", src, re.M)
    return m.group(2) if m else None


def module_list(src, name):
    """Literal list assigned to `name` at module level (ast text parse, the module is never imported)."""
    try:
        for node in ast.parse(src).body:
            if isinstance(node, ast.Assign) and any(getattr(t, "id", None) == name for t in node.targets):
                value = ast.literal_eval(node.value)
                return value if isinstance(value, list) else None
    except (SyntaxError, ValueError):
        return None
    return None


def build_deploy(cfg, manifest):
    """(argv, env, module) rebuilt from a deploy manifest, or GpuCtlError if it must be refused."""
    if not is_deploy_manifest(manifest):
        raise GpuCtlError(f"not a deploy manifest (needs keys {', '.join(DEPLOY_KEYS)})")
    app, profile = str(manifest["app"]), str(manifest["modal_profile"])
    if app not in APP_MODULES:
        raise GpuCtlError(f"unknown app {app!r} (known: {', '.join(APP_MODULES)})")
    acct = cfg["accounts"].get(str(manifest["account"]))
    if acct is None or acct["profile"] != profile:
        raise GpuCtlError(f"manifest account {manifest['account']} / profile {profile} does not match the config")
    if str(manifest["url"]).rstrip("/") != URL_FMT.format(profile=profile, app=app):
        raise GpuCtlError(f"manifest url {manifest['url']} does not match {URL_FMT.format(profile=profile, app=app)}")
    module = APP_MODULES[app]
    try:
        src = (cfg["repo_root"] / module).read_text()
    except OSError as e:
        raise GpuCtlError(f"cannot read {module} in {cfg['repo_root']}: {e}")
    hf_id, hf_rev = module_constant(src, "HF_ID"), module_constant(src, "HF_REV")
    if not hf_id or not hf_rev:
        raise GpuCtlError(f"cannot read HF_ID / HF_REV from {module}")
    ckpt, name = str(manifest["checkpoint"]), str(manifest["served_model_name"])
    subdir = None
    if ckpt.startswith(VOLUME_PREFIX):
        subdir = ckpt[len(VOLUME_PREFIX):]
        if app != "holo-vllm":
            raise GpuCtlError(f"{app} serves {hf_id} only, not a Volume checkpoint")
        if not CKPT_SUBDIR_RE.match(subdir) or ".." in subdir.split("/"):
            raise GpuCtlError(f"invalid checkpoint subdir {subdir!r}")
    elif "@" in ckpt:
        repo, rev = ckpt.rsplit("@", 1)
        if repo != hf_id:
            raise GpuCtlError(f"checkpoint {repo} differs from HF_ID {hf_id} of {module}")
        if rev != hf_rev:
            raise GpuCtlError(f"revision mismatch: manifest {rev} != HF_REV {hf_rev} of {module}")
    else:
        raise GpuCtlError(f"unrecognised checkpoint {ckpt!r}")
    if isinstance(manifest.get("vllm_args"), list):
        recorded = [str(a) for a in manifest["vllm_args"]]
        if recorded[-2:] == ["--api-key", "***"]:
            recorded = recorded[:-2]
        current = module_list(src, "VLLM_ARGS")
        if current is None:
            raise GpuCtlError(f"cannot read VLLM_ARGS from {module}")
        if recorded != [str(a) for a in current]:
            diff = [f"{a}!={b}" for a, b in zip(recorded, current) if a != b] or ["length differs"]
            raise GpuCtlError(f"vllm_args of the manifest differ from VLLM_ARGS of {module} ({', '.join(diff)}): "
                              f"deploying would not reproduce it")
    if not name or not re.fullmatch(r"[A-Za-z0-9._/-]+", name):
        raise GpuCtlError(f"invalid served_model_name {name!r}")
    env = {"MODAL_PROFILE": profile}
    if app == "holo-vllm":
        env["HOLO_CKPT"] = subdir or ""
        env["HOLO_NAME"] = name
        if "scaledown_s" in manifest:
            env["HOLO_SCALEDOWN"] = str(int(manifest["scaledown_s"]))
    else:
        fixed = module_constant(src, "NAME")
        if name != fixed:
            raise GpuCtlError(f"{module} always serves {fixed!r}, manifest says {name!r}")
    return ["modal", "deploy", module], env, module, acct, name


def poll_ready(ctx, url, expected, timeout_s, key):
    deadline = ctx.clock() + timeout_s
    attempt = 0
    while True:
        attempt += 1
        remaining = deadline - ctx.clock()
        status, body, latency, error = ctx.http_get(url.rstrip("/") + "/models", key, max(1.0, min(60.0, remaining)))
        ok, ids = check_models(status, body, expected)
        if ok:
            ctx.say(f"  ready after {attempt} request(s): {', '.join(ids)}  (last request {latency:.2f} s)")
            return True
        ctx.say(f"  not ready ({error or f'HTTP {status}, ids {ids}'})")
        if ctx.clock() + 10 >= deadline:
            return False
        ctx.sleep(10)


def cmd_deploy(ctx, args, rec):
    mpath = Path(args.manifest)
    try:
        manifest = json.loads(mpath.read_text())
    except (OSError, ValueError) as e:
        raise GpuCtlError(f"cannot read manifest {mpath}: {e}")
    rec["manifest"] = str(mpath)
    argv, env, module, acct, name = build_deploy(ctx.cfg, manifest)
    root = ctx.cfg["repo_root"]
    for git in (["git", "diff", "--quiet", "--", module], ["git", "diff", "--quiet", "--cached", "--", module]):
        res = ctx.run(git, cwd=root, timeout=60)  # read-only: runs without --go too, not in --dry-run
        if res is not None and res[0] != 0:
            what = "uncommitted changes" if res[0] == 1 else f"cannot check git state (exit {res[0]})"
            rec["decision"] = f"refused: {module} {what}"
            ctx.say(f"REFUSED: {module} has {what}: commit it first")
            return EXIT_REFUSED
    go = args.go and not ctx.dry_run
    ctx.say(f"deploy {manifest['app']} on account {acct['n']} ({acct['profile']}) serving {name}:")
    res = ctx.run(argv, env=env, cwd=root, timeout=DEPLOY_TIMEOUT_S, execute=go)
    if args.probe:
        ctx.say(f"  then poll {manifest['url'].rstrip('/')}/models until {name} is listed (timeout {args.timeout} s)")
    if not go:
        rec["decision"] = "plan only (no --go)" if not ctx.dry_run else "plan only (dry run)"
        if not ctx.dry_run:
            ctx.say("nothing executed: add --go to deploy")
        return EXIT_OK
    rc, out, err = res
    for line in (out + err).splitlines()[-15:]:
        ctx.say("  | " + line)
    if rc != 0:
        rec["decision"] = f"deploy failed rc={rc}"
        ctx.say(f"DEPLOY FAILED (exit {rc})")
        return EXIT_FAIL
    rec["decision"] = "deployed"
    if args.probe:
        key = ctx.vllm_key()
        ok = poll_ready(ctx, manifest["url"], name, args.timeout, key)
        rec["decision"] = "deployed, ready" if ok else "deployed, NOT ready before timeout"
        if not ok:
            ctx.say(f"NOT READY after {args.timeout} s (the app keeps running: stop it if needed)")
            return EXIT_FAIL
    return EXIT_OK


# ---------------------------------------------------------------- stop

def cmd_stop(ctx, args, rec):
    acct = pick_accounts(ctx.cfg, args.account)[0]
    apps, why = read_app_list(ctx, acct)
    if apps is not None:
        live = [a for a in live_apps(apps) if a.get("description") == args.app]
        if not live:
            ctx.say(f"{args.app} on account {acct['n']} ({acct['profile']}) is already stopped or absent: nothing to do")
            rec["decision"] = "already stopped or absent"
            return EXIT_OK
        ctx.say(f"{args.app} on account {acct['n']} ({acct['profile']}): "
                + ", ".join(f"{a.get('state')} tasks={tasks_of(a)}" for a in live))
    elif why != "dry-run":
        ctx.warn(f"app list unreadable ({why}): stopping without checking")
    go = args.go and not ctx.dry_run
    res = ctx.run(["modal", "app", "stop", args.app, "-y"], env={"MODAL_PROFILE": acct["profile"]}, execute=go)
    if not go:
        rec["decision"] = "plan only (no --go)" if not ctx.dry_run else "plan only (dry run)"
        if not ctx.dry_run:
            ctx.say("nothing executed: add --go to stop")
        return EXIT_OK
    rc = res[0]
    rec["decision"] = "stopped" if rc == 0 else f"stop failed rc={rc}"
    ctx.say("stopped" if rc == 0 else f"STOP FAILED (exit {rc})")
    return EXIT_OK if rc == 0 else EXIT_FAIL


# ---------------------------------------------------------------- probe

def deploy_manifests(deploys_dir):
    out = []
    for f in sorted(Path(deploys_dir).glob("*.json")):
        if f.name.endswith((".smoke.json", ".revision.json")):
            continue
        try:
            d = json.loads(f.read_text())
        except (OSError, ValueError):
            continue
        if is_deploy_manifest(d):
            out.append((f, d))
    return out


def newest_manifest(deploys_dir, app, account):
    found = [(f, d) for f, d in deploy_manifests(deploys_dir)
             if d["app"] == app and str(d["account"]) == str(account)]
    return found[-1] if found else (None, None)


def check_models(status, body, expected):
    if status != 200:
        return False, []
    try:
        ids = [str(m["id"]) for m in json.loads(body)["data"]]
    except (ValueError, KeyError, TypeError):
        return False, []
    return (expected in ids) if expected else bool(ids), ids


def cmd_probe(ctx, args, rec):
    given = [x for x in (args.url, args.manifest, args.app) if x]
    if len(given) != 1:
        raise GpuCtlError("probe needs exactly one of --url, --manifest, --app")
    expected = app = acct = None
    if args.url:
        url = args.url.rstrip("/")
        m = URL_RE.match(url)
        if m:
            acct, app = account_by_profile(ctx.cfg, m.group(1)), m.group(2)
        if args.account is not None:
            acct = pick_accounts(ctx.cfg, args.account)[0]
    else:
        if args.manifest:
            mpath = Path(args.manifest)
            try:
                d = json.loads(mpath.read_text())
            except (OSError, ValueError) as e:
                raise GpuCtlError(f"cannot read manifest {mpath}: {e}")
            if not is_deploy_manifest(d):
                raise GpuCtlError(f"{mpath} is not a deploy manifest")
        else:
            if args.account is None:
                raise GpuCtlError("probe --app needs --account")
            acct = pick_accounts(ctx.cfg, args.account)[0]
            mpath, d = newest_manifest(ctx.cfg["deploys_dir"], args.app, acct["n"])
            if d is None:
                raise GpuCtlError(f"no deploy manifest for {args.app} on account {acct['n']} in {ctx.cfg['deploys_dir']}")
        rec["manifest"] = str(mpath)
        url, expected, app = str(d["url"]).rstrip("/"), str(d["served_model_name"]), str(d["app"])
        acct = ctx.cfg["accounts"].get(str(d["account"]))
    rec.update(url=url, expected_model=expected)
    ctx.say(f"probe {url}/models" + (f" expecting {expected}" if expected else ""))
    if acct is None or app is None:
        if not args.allow_cold_start:
            rec["decision"] = "refused: cannot check running containers"
            ctx.say("REFUSED: cannot tell which account/app this URL is, so cannot check it is warm "
                    "(pass --account or --allow-cold-start)")
            return EXIT_REFUSED
    else:
        apps, why = read_app_list(ctx, acct)
        if apps is None and why != "dry-run":
            if not args.allow_cold_start:
                rec["decision"] = f"refused: app list unreadable ({why})"
                ctx.say(f"REFUSED: app list of account {acct['n']} unreadable ({why}); pass --allow-cold-start to probe anyway")
                return EXIT_REFUSED
        elif apps is not None:
            live = [a for a in live_apps(apps) if a.get("description") == app]
            tasks = sum(tasks_of(a) for a in live)
            if not live:
                rec["decision"] = "refused: app not deployed"
                ctx.say(f"REFUSED: {app} is not deployed on account {acct['n']} (stopped or absent)")
                return EXIT_REFUSED
            ctx.say(f"  {app} on account {acct['n']}: {tasks} running container(s)")
            if tasks == 0 and not args.allow_cold_start:
                rec["decision"] = "refused: 0 tasks (would cold-start a paid H100)"
                ctx.say(f"REFUSED: {app} on account {acct['n']} has 0 running containers; a request would cold-start "
                        f"a paid H100 (~4 $/h, 98-512 s). Pass --allow-cold-start to do it anyway.")
                return EXIT_REFUSED
    if ctx.dry_run:
        ctx.http_get(url + "/models", None, args.timeout)
        rec["decision"] = "plan only (dry run)"
        return EXIT_OK
    key = ctx.vllm_key()
    timeout = args.timeout if args.timeout is not None else (600 if args.allow_cold_start else 60)
    status, body, latency, error = ctx.http_get(url + "/models", key, timeout)
    ok, ids = check_models(status, body, expected)
    rec.update(model_ids=ids, latency_s=latency)
    if ok:
        rec["decision"] = "ok"
        ctx.say(f"OK  {', '.join(ids)}  latency {latency:.2f} s")
        return EXIT_OK
    rec["decision"] = "fail"
    why = error or (f"HTTP {status}" if status != 200 else (f"{expected} not in {ids}" if ids else "no model listed"))
    ctx.say(f"FAIL  {why}  latency {latency:.2f} s")
    return EXIT_FAIL


# ---------------------------------------------------------------- journal & main

def append_journal(path, line):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "a", encoding="utf-8") as f:
        f.write(line + "\n")


def build_parser():
    p = argparse.ArgumentParser(prog="gpu_ctl.py", description="Modal GPU controller (status, guard, deploy, stop, probe)")
    p.add_argument("--config", help=f"accounts config (default {DEFAULT_CONFIG.name}, else {EXAMPLE_CONFIG.name})")
    p.add_argument("--journal", default=str(DEFAULT_JOURNAL), help="JSONL journal (default: %(default)s)")
    p.add_argument("--dry-run", action="store_true", help="no subprocess, no network, no write except the journal")
    p.add_argument("--fixtures", help="with --dry-run: read <profile>.app_list.json / billing_*.json from DIR")
    sub = p.add_subparsers(dest="command", required=True)
    s = sub.add_parser("status", help="apps not stopped and spend per account (read-only)")
    s.add_argument("--account")
    g = sub.add_parser("guard", help="budget guard: warn, then stop GPU apps")
    g.add_argument("--account")
    g.add_argument("--enforce", action="store_true", help="really stop the GPU apps at stop_usd")
    g.add_argument("--notify-cmd", help="command run as: CMD <one-line message>")
    g.add_argument("--once", action="store_true", help="one round (default)")
    g.add_argument("--interval", type=float, help="seconds between rounds (needs --max-hours)")
    g.add_argument("--max-hours", type=float)
    d = sub.add_parser("deploy", help="redeploy exactly what a deploy manifest describes")
    d.add_argument("manifest")
    d.add_argument("--go", action="store_true", help="really deploy (default: print only)")
    d.add_argument("--probe", action="store_true", help="after deploy, poll /v1/models until ready")
    d.add_argument("--timeout", type=float, default=900.0, help="probe timeout in s (default 900)")
    t = sub.add_parser("stop", help="modal app stop APP -y on one account")
    t.add_argument("app")
    t.add_argument("--account", required=True)
    t.add_argument("--go", action="store_true", help="really stop (default: print only)")
    r = sub.add_parser("probe", help="GET <url>/models with the bearer key")
    r.add_argument("--account")
    r.add_argument("--app")
    r.add_argument("--manifest")
    r.add_argument("--url")
    r.add_argument("--allow-cold-start", action="store_true", help="probe even if 0 containers run (starts an H100)")
    r.add_argument("--timeout", type=float, help="request timeout in s (default 60, 600 with --allow-cold-start)")
    return p


def main(argv=None, runner=None, opener=None, out=None, err=None, environ=None, sleep=time.sleep, clock=time.monotonic):
    argv = list(sys.argv[1:] if argv is None else argv)
    err_stream = err or sys.stderr
    try:
        args = build_parser().parse_args(argv)
    except SystemExit as e:
        return EXIT_REFUSED if e.code else EXIT_OK
    journal = Path(args.journal).expanduser()
    rec = {}
    ctx = None
    command = args.command

    def write_journal(r, code):
        entry = {"ts_utc": dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds"), "command": command,
                 "argv": argv, "dry_run": bool(args.dry_run), "actions": list(ctx.actions) if ctx else [],
                 **r, "exit_code": code}
        line = json.dumps(entry, default=str, sort_keys=False)
        append_journal(journal, ctx.red(line) if ctx else line)

    code = EXIT_FAIL
    try:
        if args.fixtures and not args.dry_run:
            raise GpuCtlError("--fixtures only works with --dry-run")
        cfg_path = args.config or (DEFAULT_CONFIG if DEFAULT_CONFIG.exists() else EXAMPLE_CONFIG)
        if not args.config and not DEFAULT_CONFIG.exists():
            print(f"note: {DEFAULT_CONFIG.name} not found, using {EXAMPLE_CONFIG.name}", file=err_stream)
        ctx = Ctx(load_config(cfg_path), dry_run=args.dry_run, fixtures=args.fixtures, runner=runner, opener=opener,
                  out=out, err=err, environ=environ, sleep=sleep, clock=clock)
        if any(k in ctx.environ for k in ("MODAL_TOKEN_ID", "MODAL_TOKEN_SECRET")):
            ctx.warn("note: MODAL_TOKEN_ID/SECRET are not passed to modal; the profile selects the account")
        if ctx.dry_run:
            ctx.say("DRY RUN: no subprocess, no network" + (f", fixtures from {ctx.fixtures}" if ctx.fixtures else ""))
        if command == "status":
            code = cmd_status(ctx, args, rec)
        elif command == "guard":
            code = cmd_guard(ctx, args, rec, journal, write_journal)
        elif command == "deploy":
            code = cmd_deploy(ctx, args, rec)
        elif command == "stop":
            code = cmd_stop(ctx, args, rec)
        elif command == "probe":
            code = cmd_probe(ctx, args, rec)
    except GpuCtlError as e:
        code = e.code
        msg = ctx.red(str(e)) if ctx else str(e)
        rec["decision"] = f"error: {msg}"
        print(f"error: {msg}", file=err_stream)
    except KeyboardInterrupt:
        code = 130
        rec["decision"] = "interrupted"
    except Exception as e:  # never print a traceback: it could carry the key
        code = EXIT_FAIL
        msg = ctx.red(f"{type(e).__name__}: {e}") if ctx else f"{type(e).__name__}: {e}"
        rec["decision"] = f"internal error: {msg}"
        print(f"internal error: {msg}", file=err_stream)
    try:
        write_journal(rec, code)
    except OSError as e:
        print(f"error: cannot write journal {journal}: {e}", file=err_stream)
        code = code or EXIT_FAIL
    return code


if __name__ == "__main__":
    sys.exit(main())
