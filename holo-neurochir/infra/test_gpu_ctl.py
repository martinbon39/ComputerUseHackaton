"""Offline tests of gpu_ctl.py (unittest; no network, no Modal: fake command runner, fake opener, local http.server).

Uses the recorded fixtures and the deploy manifests of the repo: <repo_root>/fixtures and <repo_root>/osworld, where
repo_root is ../.. of this file (override with GPU_CTL_REPO_ROOT).
  python3 -m unittest -v test_gpu_ctl.py
"""
import http.server
import io
import json
import os
import shutil
import subprocess
import sys
import tempfile
import threading
import unittest
import urllib.request
from decimal import Decimal
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import gpu_ctl  # noqa: E402

REPO = Path(os.environ.get("GPU_CTL_REPO_ROOT", HERE.parent.parent)).resolve()
FIXTURES = REPO / "fixtures"
DEPLOYS = REPO / "osworld" / "modal_deploys"
KEY = "sk-test-SECRET-9f8e7d6c5b4a"

VLLM_CKPT = DEPLOYS / "20261108T065932_acct2_Holo-3.1-4B-merge_cua_b050.json"
VLLM_ORIG = DEPLOYS / "20261108T093735_acct1_Holo-3.1-4B-modal-orig.json"
JUDGE = DEPLOYS / "20261108T090300_acct2_Holo4-27B-agent.json"


def setUpModule():
    missing = [p for p in (FIXTURES / "emilejouannet.billing_today.json", VLLM_CKPT, VLLM_ORIG, JUDGE,
                           REPO / "osworld" / "modal_vllm.py", REPO / "osworld" / "modal_judge.py") if not p.exists()]
    if missing:
        raise RuntimeError(f"inputs not found (set GPU_CTL_REPO_ROOT): {missing}")


def fx(name):
    return (FIXTURES / name).read_text()


def billing(total):
    return json.dumps([{"object_id": "ap-x", "description": "holo-vllm", "cost": str(total)}])


class FakeRunner:
    """Answers `modal ...` / `git ...` from a table keyed by (MODAL_PROFILE, argv-prefix); records every call."""

    def __init__(self, table=None, default=(0, "", "")):
        self.table = table or {}
        self.default = default
        self.calls = []

    def __call__(self, argv, env, cwd, timeout):
        prof = env.get("MODAL_PROFILE")
        self.calls.append({"argv": list(argv), "profile": prof, "env": dict(env), "cwd": cwd})
        best = None
        for (p, prefix), resp in self.table.items():
            if p in (None, prof) and tuple(argv[:len(prefix)]) == prefix:
                if best is None or len(prefix) > len(best[0]):
                    best = (prefix, resp)
        if best is None:
            return self.default
        resp = best[1]
        return resp() if callable(resp) else resp

    def cmds(self, *prefix):
        return [c for c in self.calls if tuple(c["argv"][:len(prefix)]) == prefix]


def fixture_table():
    t = {}
    for p in ("emilejouannet", "martinbon39"):
        t[(p, ("modal", "app", "list"))] = (0, fx(f"{p}.app_list.json"), "")
        t[(p, ("modal", "billing", "report", "--for", "today"))] = (0, fx(f"{p}.billing_today.json"), "")
        t[(p, ("modal", "billing", "report", "--start"))] = (0, fx(f"{p}.billing_since_2026-11-01.json"), "")
    return t


def no_subprocess(*a, **k):
    raise AssertionError(f"subprocess called: {a}")


def no_network(*a, **k):
    raise AssertionError(f"network called: {a}")


class FakeResp:
    def __init__(self, status, body):
        self.status, self._body = status, body

    def read(self, n=-1):
        return self._body

    def close(self):
        pass


class FakeOpener:
    def __init__(self, ids, status=200):
        self.ids, self.status, self.requests = ids, status, []

    def __call__(self, req, timeout):
        self.requests.append((req.full_url, req.get_header("Authorization")))
        if self.status != 200:
            raise urllib.error.HTTPError(req.full_url, self.status, "err", {}, None)
        return FakeResp(200, json.dumps({"object": "list", "data": [{"id": i} for i in self.ids]}).encode())


class Base(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, self.tmp)
        self.journal = self.tmp / "gpu_ctl.jsonl"
        self.config = self.write_config()

    def write_config(self, repo_root=REPO, **over):
        cfg = json.loads((HERE / "accounts.example.json").read_text())
        cfg["repo_root"] = str(repo_root)
        cfg["vllm_key_file"] = str(self.tmp / "missing_key")
        for n, vals in over.items():
            cfg["accounts"][n].update(vals)
        path = self.tmp / f"accounts{len(list(self.tmp.glob('accounts*')))}.json"
        path.write_text(json.dumps(cfg))
        return path

    def run_ctl(self, *argv, runner=no_subprocess, opener=no_network, environ=None, config=None, **kw):
        out, err = io.StringIO(), io.StringIO()
        full = ["--config", str(config or self.config), "--journal", str(self.journal), *argv]
        code = gpu_ctl.main(full, runner=runner, opener=opener, out=out, err=err,
                            environ=environ if environ is not None else {"PATH": "/usr/bin"}, **kw)
        return code, out.getvalue(), err.getvalue()

    def journal_lines(self):
        return [json.loads(line) for line in self.journal.read_text().splitlines()]


class SpendTest(Base):
    def test_spend_formula_on_fixtures_dry_run(self):
        code, out, _ = self.run_ctl("--dry-run", "--fixtures", str(FIXTURES), "status")
        self.assertEqual(code, 0)
        self.assertIn("full days 0.00 + today 20.16 = 20.16 $", out)
        self.assertIn("full days 0.00 + today 23.18 = 23.18 $", out)
        accts = {a["account"]: a for a in self.journal_lines()[-1]["accounts"]}
        self.assertEqual(accts["1"]["total_usd"], "20.16")
        self.assertEqual(accts["2"]["total_usd"], "23.18")
        self.assertEqual(accts["1"]["today_per_app"], {"holo-vllm": "19.84", "holo-slot": "0.32"})

    def test_spend_formula_with_runner_sums_both_reports(self):
        cfg = gpu_ctl.load_config(self.config)
        t = fixture_table()
        t[("emilejouannet", ("modal", "billing", "report", "--start"))] = (0, billing("1.50"), "")
        runner = FakeRunner(t)
        ctx = gpu_ctl.Ctx(cfg, runner=runner, out=io.StringIO(), environ={})
        sp1 = gpu_ctl.read_spend(ctx, cfg["accounts"]["1"])
        sp2 = gpu_ctl.read_spend(ctx, cfg["accounts"]["2"])
        self.assertEqual(gpu_ctl.money(sp1["today"]), "20.16")
        self.assertEqual(gpu_ctl.money(sp1["total"]), "21.66")
        self.assertEqual(gpu_ctl.money(sp2["total"]), "23.18")
        argvs = [c["argv"] for c in runner.calls if c["profile"] == "emilejouannet"]
        self.assertIn(["modal", "billing", "report", "--start", "2026-11-01", "--json"], argvs)
        self.assertIn(["modal", "billing", "report", "--for", "today", "--json"], argvs)
        self.assertNotIn("MODAL_TOKEN_ID", runner.calls[0]["env"])

    def test_modal_tokens_and_key_not_passed_to_children(self):
        runner = FakeRunner(fixture_table())
        env = {"PATH": "/usr/bin", "MODAL_TOKEN_ID": "ak-x", "MODAL_TOKEN_SECRET": "as-x", "HOLO_VLLM_KEY": KEY}
        self.run_ctl("status", runner=runner, environ=env)
        for c in runner.calls:
            for k in ("MODAL_TOKEN_ID", "MODAL_TOKEN_SECRET", "HOLO_VLLM_KEY"):
                self.assertNotIn(k, c["env"])
            self.assertIn(c["profile"], ("emilejouannet", "martinbon39"))


class GuardTest(Base):
    def table(self, total1, total2, apps1=None, apps2=None):
        t = fixture_table()
        t[("emilejouannet", ("modal", "billing", "report", "--for", "today"))] = (0, billing(total1), "")
        t[("martinbon39", ("modal", "billing", "report", "--for", "today"))] = (0, billing(total2), "")
        if apps1 is not None:
            t[("emilejouannet", ("modal", "app", "list"))] = (0, json.dumps(apps1), "")
        if apps2 is not None:
            t[("martinbon39", ("modal", "app", "list"))] = (0, json.dumps(apps2), "")
        return t

    def test_exit_codes_0_10_20(self):
        for t1, t2, expect in [("5", "5", 0), ("19.99", "26.99", 0), ("20.00", "5", 10), ("5", "27", 10),
                               ("24", "5", 20), ("21", "29.5", 20), ("100", "100", 20)]:
            runner = FakeRunner(self.table(t1, t2))
            code, out, _ = self.run_ctl("guard", "--once", runner=runner)
            self.assertEqual(code, expect, (t1, t2, out))
            self.assertEqual(runner.cmds("modal", "app", "stop"), [], "no stop without --enforce")
        self.assertEqual(self.run_ctl("--dry-run", "--fixtures", str(FIXTURES), "guard")[0], 10)

    def test_below_warn_does_nothing(self):
        runner = FakeRunner(self.table("1", "1"))
        code, out, _ = self.run_ctl("guard", "--notify-cmd", "notify-me", runner=runner)
        self.assertEqual(code, 0)
        self.assertEqual(runner.cmds("notify-me"), [])

    def test_warn_notify_deduplicated_across_runs(self):
        runner = FakeRunner(self.table("20.5", "1"))
        for _ in range(3):
            code, _, _ = self.run_ctl("guard", "--notify-cmd", "argos send ares", runner=runner)
            self.assertEqual(code, 10)
        sent = runner.cmds("argos", "send", "ares")
        self.assertEqual(len(sent), 1)
        msg = sent[0]["argv"][-1]
        self.assertNotIn("\n", msg)
        self.assertIn("account 1", msg)
        self.assertIn("20.50", msg)
        self.assertTrue((self.tmp / "gpu_ctl.state.json").exists())

    def test_failed_notify_is_retried(self):
        runner = FakeRunner(self.table("20.5", "1"))
        runner.table[(None, ("notify-me",))] = (1, "", "boom")
        self.run_ctl("guard", "--notify-cmd", "notify-me", runner=runner)
        runner.table[(None, ("notify-me",))] = (0, "", "")
        self.run_ctl("guard", "--notify-cmd", "notify-me", runner=runner)
        self.run_ctl("guard", "--notify-cmd", "notify-me", runner=runner)
        self.assertEqual(len(runner.cmds("notify-me")), 2)

    def test_stop_without_enforce_reports_only(self):
        runner = FakeRunner(self.table("30", "1"))
        code, out, _ = self.run_ctl("guard", runner=runner)
        self.assertEqual(code, 20)
        self.assertIn("WOULD STOP holo-vllm", out)
        self.assertEqual(runner.cmds("modal", "app", "stop"), [])

    def test_enforce_stops_only_running_gpu_apps(self):
        apps2 = [
            {"app_id": "a1", "description": "holo-vllm", "state": "deployed", "tasks": "1"},
            {"app_id": "a2", "description": "holo-slot", "state": "stopped", "tasks": "0"},
            {"app_id": "a3", "description": "holo-judge", "state": "deployed", "tasks": "0"},
            {"app_id": "a4", "description": "holo-jury-probe", "state": "deployed", "tasks": "1"},
            {"app_id": "a5", "description": "other-app", "state": "deployed", "tasks": "1"},
        ]
        runner = FakeRunner(self.table("1", "30", apps2=apps2))
        code, out, _ = self.run_ctl("guard", "--enforce", "--notify-cmd", "notify-me", runner=runner)
        self.assertEqual(code, 20)
        stops = [(c["profile"], c["argv"]) for c in runner.cmds("modal", "app", "stop")]
        self.assertEqual(stops, [("martinbon39", ["modal", "app", "stop", "holo-vllm", "-y"]),
                                 ("martinbon39", ["modal", "app", "stop", "holo-judge", "-y"])])
        self.assertEqual(len(runner.cmds("notify-me")), 1)
        self.assertIn("holo-vllm:stopped", runner.cmds("notify-me")[0]["argv"][-1])

    def test_enforce_on_fixtures_account2_never_touches_jury_probe(self):
        runner = FakeRunner(self.table("1", "29.5"))  # app list: real fixture of account 2
        self.run_ctl("guard", "--enforce", "--account", "2", runner=runner)
        stops = [c["argv"][3] for c in runner.cmds("modal", "app", "stop")]
        self.assertEqual(stops, ["holo-judge"])

    def test_enforce_nothing_running_stops_nothing(self):
        runner = FakeRunner(self.table("30", "1", apps1=[{"description": "holo-vllm", "state": "stopped"}]))
        code, _, _ = self.run_ctl("guard", "--enforce", "--notify-cmd", "n", runner=runner)
        self.assertEqual(code, 20)
        self.assertEqual(runner.cmds("modal", "app", "stop"), [])
        self.run_ctl("guard", "--enforce", "--notify-cmd", "n", runner=runner)
        self.assertEqual(len(runner.cmds("n")), 1)

    def test_jury_probe_refused_in_gpu_apps(self):
        cfg = self.write_config(**{"2": {"gpu_apps": ["holo-vllm", "holo-jury-probe"]}})
        code, _, err = self.run_ctl("guard", config=cfg)
        self.assertEqual(code, 2)
        self.assertIn("CPU-only", err)

    def test_billing_unreadable_three_times_notifies_once(self):
        t = self.table("1", "1")
        t[("emilejouannet", ("modal", "billing", "report", "--for", "today"))] = (1, "", "auth error")
        runner = FakeRunner(t)
        codes = [self.run_ctl("guard", "--notify-cmd", "n", runner=runner)[0] for _ in range(4)]
        self.assertEqual(codes, [3, 3, 3, 3])
        sent = runner.cmds("n")
        self.assertEqual(len(sent), 1)
        self.assertIn("unreadable 3 times", sent[0]["argv"][-1])

    def test_loop_needs_max_hours_and_ends(self):
        self.assertEqual(self.run_ctl("guard", "--interval", "300")[0], 2)
        now = [0.0]
        sleeps = []

        def sleep(s):
            sleeps.append(s)
            now[0] += s
        runner = FakeRunner(self.table("20.5", "1"))
        code, _, _ = self.run_ctl("guard", "--interval", "600", "--max-hours", "1", "--notify-cmd", "n",
                                  runner=runner, sleep=sleep, clock=lambda: now[0])
        self.assertEqual(code, 10)
        self.assertEqual(sum(sleeps), 3600)
        self.assertEqual(len(runner.cmds("n")), 1)
        self.assertGreaterEqual(len(self.journal_lines()), 6)


class DeployTest(Base):
    def test_deploy_command_rebuilt_exactly(self):
        cases = [
            (VLLM_CKPT, "MODAL_PROFILE=martinbon39 HOLO_CKPT=merge_cua_b050 HOLO_NAME=Holo-3.1-4B-merge_cua_b050 "
                        "modal deploy osworld/modal_vllm.py"),
            (VLLM_ORIG, "MODAL_PROFILE=emilejouannet HOLO_CKPT='' HOLO_NAME=Holo-3.1-4B-modal-orig "
                        "modal deploy osworld/modal_vllm.py"),
            (JUDGE, "MODAL_PROFILE=martinbon39 modal deploy osworld/modal_judge.py"),
        ]
        for manifest, expected in cases:
            runner = FakeRunner()
            code, out, _ = self.run_ctl("deploy", str(manifest), "--go", runner=runner)
            self.assertEqual(code, 0, out)
            dep = runner.cmds("modal", "deploy")
            self.assertEqual(len(dep), 1)
            got = gpu_ctl.render(dep[0]["argv"], {k: dep[0]["env"][k] for k in ("MODAL_PROFILE", "HOLO_CKPT", "HOLO_NAME")
                                                  if k in dep[0]["env"]})
            self.assertEqual(got, expected)
            self.assertEqual(dep[0]["cwd"], str(REPO))
            self.assertEqual(runner.cmds("git", "diff")[0]["argv"][-1], dep[0]["argv"][-1])
            _, plan, _ = self.run_ctl("deploy", str(manifest), runner=FakeRunner())
            self.assertIn(f"would run: {expected}", plan)

    def test_every_deploy_manifest_of_the_repo_builds(self):
        cfg = gpu_ctl.load_config(self.config)
        manifests = gpu_ctl.deploy_manifests(DEPLOYS)
        self.assertGreater(len(manifests), 20)
        refused = []
        for f, d in manifests:
            try:
                argv, env, module, _, _ = gpu_ctl.build_deploy(cfg, d)
            except gpu_ctl.GpuCtlError as e:
                refused.append((f.name, str(e)))
                continue
            self.assertEqual(argv, ["modal", "deploy", module], f)
        # the first judge deploy ran with {"image": 2}; modal_judge.py now has {"image": 5}
        self.assertEqual([r[0] for r in refused], ["20261108T075938_acct2_Holo4-27B.json"])
        self.assertIn("vllm_args", refused[0][1])

    def test_inherited_holo_env_does_not_leak_into_deploy(self):
        runner = FakeRunner()
        self.run_ctl("deploy", str(JUDGE), "--go", runner=runner,
                     environ={"HOLO_CKPT": "x", "HOLO_NAME": "y", "HOLO_SCALEDOWN": "5", "MODAL_PROFILE": "emilejouannet"})
        env = runner.cmds("modal", "deploy")[0]["env"]
        self.assertEqual(env["MODAL_PROFILE"], "martinbon39")
        for k in ("HOLO_CKPT", "HOLO_NAME", "HOLO_SCALEDOWN"):
            self.assertNotIn(k, env)

    def copy_repo(self, rev=None):
        root = self.tmp / "repo"
        (root / "osworld").mkdir(parents=True)
        for m in ("modal_vllm.py", "modal_judge.py"):
            src = (REPO / "osworld" / m).read_text()
            if rev and m == "modal_vllm.py":
                src = src.replace(gpu_ctl.module_constant(src, "HF_REV"), rev)
            (root / "osworld" / m).write_text(src)
        return root

    def test_refuses_revision_mismatch(self):
        cfg = self.write_config(repo_root=self.copy_repo(rev="0" * 40))
        runner = FakeRunner()
        code, out, err = self.run_ctl("deploy", str(VLLM_ORIG), "--go", runner=runner, config=cfg)
        self.assertEqual(code, 2)
        self.assertIn("revision mismatch", err)
        self.assertEqual(runner.calls, [])
        bad = json.loads(JUDGE.read_text())
        bad["checkpoint"] = "Hcompany/Holo4-27B@deadbeef"
        (self.tmp / "m.json").write_text(json.dumps(bad))
        self.assertEqual(self.run_ctl("deploy", str(self.tmp / "m.json"), "--go", runner=runner)[0], 2)
        self.assertEqual(runner.cmds("modal"), [])

    def test_refuses_vllm_args_drift(self):
        m = json.loads(VLLM_CKPT.read_text())
        m["vllm_args"][m["vllm_args"].index("0.40")] = "0.50"
        (self.tmp / "m.json").write_text(json.dumps(m))
        runner = FakeRunner()
        code, _, err = self.run_ctl("deploy", str(self.tmp / "m.json"), "--go", runner=runner)
        self.assertEqual(code, 2)
        self.assertIn("0.50!=0.40", err)
        self.assertEqual(runner.calls, [])

    def test_ckpt_manifest_ignores_hf_rev(self):
        cfg = self.write_config(repo_root=self.copy_repo(rev="0" * 40))
        code, _, _ = self.run_ctl("deploy", str(VLLM_CKPT), "--go", runner=FakeRunner(), config=cfg)
        self.assertEqual(code, 0)

    def test_refuses_dirty_module_fake_git(self):
        runner = FakeRunner({(None, ("git", "diff", "--quiet", "--")): (1, "", "")})
        code, out, _ = self.run_ctl("deploy", str(VLLM_CKPT), "--go", runner=runner)
        self.assertEqual(code, 2)
        self.assertIn("uncommitted changes", out)
        self.assertEqual(runner.cmds("modal"), [])

    @unittest.skipUnless(shutil.which("git"), "git not installed")
    def test_refuses_dirty_module_real_git(self):
        root = self.copy_repo()
        g = ["git", "-c", "user.email=t@t", "-c", "user.name=t"]
        subprocess.run(g + ["init", "-q", str(root)], check=True)
        subprocess.run(g + ["-C", str(root), "add", "."], check=True)
        subprocess.run(g + ["-C", str(root), "commit", "-qm", "init"], check=True)
        cfg = self.write_config(repo_root=root)
        modal_calls = []

        def runner(argv, env, cwd, timeout):
            if argv[0] == "git":
                return gpu_ctl.default_runner(argv, env, cwd, timeout)
            modal_calls.append(argv)
            return 0, "", ""
        self.assertEqual(self.run_ctl("deploy", str(VLLM_CKPT), "--go", runner=runner, config=cfg)[0], 0)
        self.assertEqual(len(modal_calls), 1)
        with open(root / "osworld" / "modal_vllm.py", "a") as f:
            f.write("# edit\n")
        self.assertEqual(self.run_ctl("deploy", str(VLLM_CKPT), "--go", runner=runner, config=cfg)[0], 2)
        subprocess.run(["git", "-C", str(root), "add", "."], check=True)  # staged but not committed
        self.assertEqual(self.run_ctl("deploy", str(VLLM_CKPT), "--go", runner=runner, config=cfg)[0], 2)
        self.assertEqual(self.run_ctl("deploy", str(JUDGE), "--go", runner=runner, config=cfg)[0], 0)
        self.assertEqual(len(modal_calls), 2)

    def test_refuses_probe_records_and_foreign_profile(self):
        smoke = DEPLOYS / "20261108T090300_acct2_Holo4-27B-agent.smoke.json"
        self.assertEqual(self.run_ctl("deploy", str(smoke), "--go", runner=FakeRunner())[0], 2)
        m = json.loads(VLLM_CKPT.read_text())
        m["modal_profile"] = "emilejouannet"
        (self.tmp / "m.json").write_text(json.dumps(m))
        runner = FakeRunner()
        self.assertEqual(self.run_ctl("deploy", str(self.tmp / "m.json"), "--go", runner=runner)[0], 2)
        self.assertEqual(runner.calls, [])

    def test_deploy_without_go_executes_nothing(self):
        for manifest in (VLLM_CKPT, VLLM_ORIG, JUDGE):
            runner = FakeRunner()
            code, out, _ = self.run_ctl("deploy", str(manifest), "--probe", runner=runner)
            self.assertEqual(code, 0)
            self.assertEqual([c["argv"][0] for c in runner.calls], ["git", "git"])  # read-only checks only
            self.assertIn("nothing executed", out)
            entry = self.journal_lines()[-1]
            dep = [a for a in entry["actions"] if "modal deploy" in a["cmd"]]
            self.assertEqual([a["executed"] for a in dep], [False])

    def test_deploy_probe_polls_until_ready(self):
        now = [0.0]

        def sleep(s):
            now[0] += s
        calls = []

        def opener(req, timeout):
            calls.append(req.full_url)
            now[0] += 5
            if len(calls) < 3:
                raise urllib.error.HTTPError(req.full_url, 503, "starting", {}, None)
            return FakeResp(200, json.dumps({"data": [{"id": "Holo4-27B"}]}).encode())
        code, out, _ = self.run_ctl("deploy", str(JUDGE), "--go", "--probe", "--timeout", "120", runner=FakeRunner(),
                                    opener=opener, environ={"HOLO_VLLM_KEY": KEY}, sleep=sleep, clock=lambda: now[0])
        self.assertEqual(code, 0, out)
        self.assertEqual(calls, ["https://martinbon39--holo-judge-serve.us-east.modal.run/v1/models"] * 3)
        self.assertNotIn(KEY, out + self.journal.read_text())


class StopTest(Base):
    def test_stop_without_go_executes_nothing(self):
        runner = FakeRunner(fixture_table())
        code, out, _ = self.run_ctl("stop", "holo-judge", "--account", "2", runner=runner)
        self.assertEqual(code, 0)
        self.assertEqual(runner.cmds("modal", "app", "stop"), [])
        self.assertIn("would run: MODAL_PROFILE=martinbon39 modal app stop holo-judge -y", out)

    def test_stop_with_go(self):
        runner = FakeRunner(fixture_table())
        code, _, _ = self.run_ctl("stop", "holo-vllm", "--account", "1", "--go", runner=runner)
        self.assertEqual(code, 0)
        stops = runner.cmds("modal", "app", "stop")
        self.assertEqual([(c["profile"], c["argv"]) for c in stops],
                         [("emilejouannet", ["modal", "app", "stop", "holo-vllm", "-y"])])
        runner.table[("emilejouannet", ("modal", "app", "stop"))] = (1, "", "err")
        self.assertEqual(self.run_ctl("stop", "holo-vllm", "--account", "1", "--go", runner=runner)[0], 1)

    def test_already_stopped_or_absent(self):
        for app in ("holo-slot", "holo-vllm-typo"):
            runner = FakeRunner(fixture_table())
            code, out, _ = self.run_ctl("stop", app, "--account", "1", "--go", runner=runner)
            self.assertEqual(code, 0)
            self.assertIn("already stopped or absent", out)
            self.assertEqual(runner.cmds("modal", "app", "stop"), [])


class ProbeServer:
    def __init__(self, ids):
        seen = self.seen = []

        class H(http.server.BaseHTTPRequestHandler):
            def do_GET(self):
                seen.append((self.path, self.headers.get("Authorization")))
                if self.headers.get("Authorization") != f"Bearer {KEY}":
                    self.send_response(401)
                    self.end_headers()
                    return
                body = json.dumps({"object": "list", "data": [{"id": i, "object": "model"} for i in ids]}).encode()
                self.send_response(200)
                self.send_header("Content-Type", "application/json")
                self.send_header("Content-Length", str(len(body)))
                self.end_headers()
                self.wfile.write(body)

            def log_message(self, *a):
                pass
        self.httpd = http.server.HTTPServer(("127.0.0.1", 0), H)
        self.url = f"http://127.0.0.1:{self.httpd.server_address[1]}/v1"
        threading.Thread(target=self.httpd.serve_forever, daemon=True).start()

    def close(self):
        self.httpd.shutdown()
        self.httpd.server_close()


LOCAL_OPENER = urllib.request.build_opener(urllib.request.ProxyHandler({})).open


class ProbeTest(Base):
    def test_refuses_zero_task_app_without_allow_cold_start(self):
        t = fixture_table()
        t[("emilejouannet", ("modal", "app", "list"))] = (
            0, json.dumps([{"description": "holo-vllm", "state": "deployed", "tasks": "0"}]), "")
        opener = FakeOpener(["Holo-3.1-4B-modal-orig"])
        env = {"HOLO_VLLM_KEY": KEY}
        code, out, _ = self.run_ctl("probe", "--account", "1", "--app", "holo-vllm",
                                    runner=FakeRunner(t), opener=opener, environ=env)
        self.assertEqual(code, 2)
        self.assertIn("cold-start", out)
        self.assertEqual(opener.requests, [])
        code, out, _ = self.run_ctl("probe", "--account", "1", "--app", "holo-vllm", "--allow-cold-start",
                                    runner=FakeRunner(t), opener=opener, environ=env)
        self.assertEqual(code, 0, out)
        self.assertEqual(opener.requests, [("https://emilejouannet--holo-vllm-serve.us-east.modal.run/v1/models",
                                            f"Bearer {KEY}")])

    def test_zero_task_refusal_from_url_and_fixture(self):
        # holo-jury-probe has 0 tasks in the real fixture of account 2: refused before any request
        code, out, _ = self.run_ctl("--dry-run", "--fixtures", str(FIXTURES), "probe", "--url",
                                    "https://martinbon39--holo-jury-probe-serve.us-east.modal.run/v1")
        self.assertEqual(code, 2)
        self.assertIn("0 running containers", out)
        line = self.journal_lines()[-1]
        self.assertEqual([a for a in line["actions"] if a["type"] == "http"], [])

    def test_newest_manifest_selected(self):
        f, d = gpu_ctl.newest_manifest(DEPLOYS, "holo-vllm", "1")
        self.assertEqual(f.name, "20261108T093735_acct1_Holo-3.1-4B-modal-orig.json")
        f, d = gpu_ctl.newest_manifest(DEPLOYS, "holo-judge", "2")
        self.assertEqual(f.name, "20261108T090300_acct2_Holo4-27B-agent.json")

    def test_passes_on_local_models_endpoint_and_fails_on_wrong_name(self):
        srv = ProbeServer(["Holo-3.1-4B-merge_cua_b050"])
        self.addCleanup(srv.close)
        m = json.loads(VLLM_CKPT.read_text())
        m["url"] = srv.url
        (self.tmp / "m.json").write_text(json.dumps(m))
        t = fixture_table()
        t[("martinbon39", ("modal", "app", "list"))] = (
            0, json.dumps([{"description": "holo-vllm", "state": "deployed", "tasks": "1"}]), "")
        runner = FakeRunner(t)
        env = {"HOLO_VLLM_KEY": KEY}
        code, out, err = self.run_ctl("probe", "--manifest", str(self.tmp / "m.json"), runner=runner,
                                      opener=LOCAL_OPENER, environ=env)
        self.assertEqual(code, 0, out + err)
        self.assertRegex(out, r"OK  Holo-3.1-4B-merge_cua_b050  latency \d+\.\d\d s")
        self.assertEqual(srv.seen, [("/v1/models", f"Bearer {KEY}")])
        m["served_model_name"] = "Holo-3.1-4B-wrong"
        (self.tmp / "m.json").write_text(json.dumps(m))
        code, out, _ = self.run_ctl("probe", "--manifest", str(self.tmp / "m.json"), runner=runner,
                                    opener=LOCAL_OPENER, environ=env)
        self.assertEqual(code, 1)
        self.assertIn("FAIL", out)
        # --url with an unknown host: needs --allow-cold-start (cannot check), then any id is accepted
        self.assertEqual(self.run_ctl("probe", "--url", srv.url, opener=LOCAL_OPENER, environ=env)[0], 2)
        code, out, _ = self.run_ctl("probe", "--url", srv.url, "--allow-cold-start", opener=LOCAL_OPENER, environ=env)
        self.assertEqual(code, 0, out)
        # wrong key -> 401 -> FAIL
        code, out, _ = self.run_ctl("probe", "--url", srv.url, "--allow-cold-start", opener=LOCAL_OPENER,
                                    environ={"HOLO_VLLM_KEY": "other-key-123"})
        self.assertEqual(code, 1)
        self.assertIn("HTTP 401", out)

    def test_key_read_from_file(self):
        keyfile = self.tmp / "key"
        keyfile.write_text(KEY + "\n")
        cfg = json.loads(self.config.read_text())
        cfg["vllm_key_file"] = str(keyfile)
        self.config.write_text(json.dumps(cfg))
        opener = FakeOpener(["x"])
        code, out, _ = self.run_ctl("probe", "--url", "http://h/v1", "--allow-cold-start", opener=opener, environ={})
        self.assertEqual(code, 0)
        self.assertEqual(opener.requests[0][1], f"Bearer {KEY}")
        self.assertNotIn(KEY, out + self.journal.read_text())

    def test_missing_key_refused(self):
        code, _, err = self.run_ctl("probe", "--url", "http://h/v1", "--allow-cold-start", environ={})
        self.assertEqual(code, 2)
        self.assertIn("no vLLM key", err)


class SecrecyTest(Base):
    def test_key_never_in_stdout_stderr_or_journal(self):
        env = {"HOLO_VLLM_KEY": KEY, "PATH": "/usr/bin"}
        t = fixture_table()
        t[("emilejouannet", ("modal", "app", "list"))] = (
            0, json.dumps([{"description": "holo-vllm", "state": "deployed", "tasks": "1"}]), "")
        outputs = []

        def leaky_opener(req, timeout):  # an error message that echoes the header must still be redacted
            raise urllib.error.URLError(f"refused with header {req.get_header('Authorization')}")

        def crashing_opener(req, timeout):
            raise RuntimeError(f"boom {req.get_header('Authorization')}")
        for opener in (FakeOpener(["Holo-3.1-4B-modal-orig"]), FakeOpener(["nope"]), FakeOpener([], status=401),
                       leaky_opener, crashing_opener):
            outputs.append(self.run_ctl("probe", "--account", "1", "--app", "holo-vllm", runner=FakeRunner(t),
                                        opener=opener, environ=env))
        outputs.append(self.run_ctl("--dry-run", "probe", "--account", "1", "--app", "holo-vllm", environ=env))
        outputs.append(self.run_ctl("deploy", str(VLLM_ORIG), "--go", "--probe", "--timeout", "1",
                                    runner=FakeRunner(), opener=leaky_opener, environ=env, sleep=lambda s: None))
        self.assertEqual([o[0] for o in outputs], [0, 1, 1, 1, 1, 0, 1])
        text = "".join(o[1] + o[2] for o in outputs) + self.journal.read_text()
        self.assertNotIn(KEY, text)
        self.assertIn("Bearer <redacted>", self.journal.read_text())
        self.assertIn("<redacted>", text)  # the leaky error was redacted, not dropped

    def test_journal_fields(self):
        self.run_ctl("--dry-run", "--fixtures", str(FIXTURES), "guard", "--enforce")
        e = self.journal_lines()[-1]
        for k in ("ts_utc", "command", "argv", "dry_run", "actions", "decision", "exit_code"):
            self.assertIn(k, e)
        self.assertEqual((e["command"], e["dry_run"], e["exit_code"]), ("guard", True, 10))
        self.assertTrue(all(a["executed"] is False for a in e["actions"]))


class DryRunTest(Base):
    def test_dry_run_makes_zero_subprocess_and_network_calls(self):
        fxd = ["--fixtures", str(FIXTURES)]
        cases = [
            fxd + ["status"], ["status"], fxd + ["guard", "--enforce", "--notify-cmd", "n"], ["guard", "--enforce"],
            fxd + ["stop", "holo-judge", "--account", "2", "--go"], ["stop", "holo-vllm", "--account", "1", "--go"],
            fxd + ["deploy", str(VLLM_CKPT), "--go", "--probe"], ["deploy", str(JUDGE), "--go"],
            fxd + ["probe", "--account", "1", "--app", "holo-vllm"], ["probe", "--url", "http://h/v1", "--allow-cold-start"],
        ]
        cfg = self.write_config(**{"2": {"warn_usd": 20, "stop_usd": 23}})  # account 2 at stop level on the fixtures
        for argv in cases:
            before = set(self.tmp.iterdir())
            code, out, err = self.run_ctl("--dry-run", *argv, config=cfg, environ={"HOLO_VLLM_KEY": KEY})
            self.assertIn(code, (0, 10, 20), (argv, out, err))
            self.assertEqual(set(self.tmp.iterdir()) - before - {self.journal}, set(), argv)
            self.assertNotIn(KEY, out + err)
        out = self.run_ctl("--dry-run", *fxd, "guard", "--enforce", config=cfg)[1]
        self.assertIn("would run: MODAL_PROFILE=martinbon39 modal app stop holo-judge -y", out)
        self.assertNotIn("holo-jury-probe -y", out)
        out = self.run_ctl("--dry-run", "status")[1]
        self.assertIn("would run: MODAL_PROFILE=emilejouannet modal billing report --for today --json", out)

    def test_dry_run_with_real_runner_spawns_nothing(self):
        orig = subprocess.run

        def boom(*a, **k):
            raise AssertionError("subprocess.run called")
        subprocess.run = boom
        try:
            for argv in (["status"], ["guard", "--enforce"], ["deploy", str(VLLM_ORIG), "--go"],
                         ["stop", "holo-vllm", "--account", "1", "--go"]):
                code = gpu_ctl.main(["--config", str(self.config), "--journal", str(self.journal), "--dry-run", *argv],
                                    out=io.StringIO(), err=io.StringIO())
                self.assertEqual(code, 0, argv)
        finally:
            subprocess.run = orig

    def test_fixtures_require_dry_run(self):
        self.assertEqual(self.run_ctl("--fixtures", str(FIXTURES), "status")[0], 2)


if __name__ == "__main__":
    unittest.main()
