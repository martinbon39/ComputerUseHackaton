"""One-task end-to-end dry run of the 3 arms: real run_holo.py / run_holo_guard.py code, mock vLLM, fake VM.
Needs the harness python (openai, desktop_env, holo_agent): HARNESS_PY, default ~/osw/venv/bin/python."""
import glob
import json
import os
import subprocess
import sys
import tempfile
import unittest

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, HERE)
import analysis  # noqa: E402
import seeding  # noqa: E402

PY = os.environ.get("HARNESS_PY", os.path.expanduser("~/osw/venv/bin/python"))
TASK = "44ee5668-ecd5-4366-a6ce-c1c9b8d4e938"


def run(results, *extra):
    p = subprocess.run([PY, os.path.join(HERE, "runner.py"), "run", "--mock", "--results", results, "--max-tasks", "1",
                        *extra], capture_output=True, text=True, timeout=600)
    return p.returncode, p.stdout + p.stderr


def jl(path):
    return [json.loads(x) for x in open(path)] if os.path.exists(path) else []


@unittest.skipUnless(os.path.exists(PY), "harness python not found")
class EndToEnd(unittest.TestCase):
    def test_three_arms_seeded(self):
        with tempfile.TemporaryDirectory() as d:
            code, log = run(d, "--seeds", "0,1")
            self.assertEqual(code, 0, log[-3000:])
            led = [r for r in jl(os.path.join(d, "ledger.jsonl")) if r.get("kind") == "attempt"]
            self.assertEqual(len(led), 6)
            self.assertFalse(any(r["dead"] for r in led))
            req = jl(os.path.join(d, "mock_requests.jsonl"))
            self.assertTrue(all(r["seed"] is not None for r in req if r["model"] != "claude-sonnet"))
            for s in (0, 1):
                ep = {a: glob.glob(os.path.join(d, f"arm{a}", f"seed{s}", "pyautogui", "screenshot", "*", "*", TASK))[0]
                      for a in "ABC"}
                seeds = {a: jl(os.path.join(ep[a], "seeds.jsonl")) for a in "ABC"}
                key = lambda rs: [(r["step"], r["k"], r["request_seed"]) for r in rs]  # noqa: E731
                self.assertEqual(key(seeds["A"]), key(seeds["B"]))
                for r in seeds["A"]:
                    self.assertEqual(r["request_seed"], seeding.request_seed(s, TASK, r["step"], r["k"]))
                n_b = len(seeds["B"])
                self.assertEqual(key(seeds["C"])[:n_b], key(seeds["B"]))
                sent = {r["seed"] for r in req}
                self.assertTrue(all(r["request_seed"] in sent for a in "ABC" for r in seeds[a]))
                g_b = jl(os.path.join(ep["B"], "guard.jsonl"))
                g_c = jl(os.path.join(ep["C"], "guard.jsonl"))
                self.assertEqual([g["decision"] for g in g_b], ["passed_complete"])
                self.assertEqual(g_b[0]["verifier"]["backend"], "neutral_stub")
                self.assertEqual(g_c[0]["decision"], "refused")
                self.assertEqual(g_c[0]["verifier"]["backend"], "openai")
                self.assertFalse(os.path.exists(os.path.join(ep["A"], "guard.jsonl")))
                meta_c = json.load(open(os.path.join(ep["C"], "meta.json")))
                self.assertEqual(meta_c["feci_guard"]["verifier_sha"], "0af76fdbacc72317")
                meta_b = json.load(open(os.path.join(ep["B"], "meta.json")))
                self.assertTrue(meta_b["feci_guard"]["verifier_sha"].startswith("neutral-"))
            r = analysis.analyse(d)
            self.assertEqual(r["n_pairs_valid"], 2)
            self.assertEqual(r["s3_seed_fidelity_A_vs_B"]["identical_until_first_answer"], 2)
            self.assertTrue(os.path.exists(os.path.join(d, "cost.json")))

    def test_infra_dead_rerun_drop_and_stop(self):
        with tempfile.TemporaryDirectory() as d:
            code, log = run(d, "--seeds", "0,1", "--mock-fail-task", TASK)
            self.assertEqual(code, 3, log[-3000:])
            self.assertIn("HARD STOP", log)
            led = jl(os.path.join(d, "ledger.jsonl"))
            att = [r for r in led if r.get("kind") == "attempt"]
            self.assertEqual(sorted((r["arm"], r["attempt"]) for r in att),
                             [("A", 1), ("A", 2), ("B", 1), ("B", 2), ("C", 1), ("C", 2)])
            self.assertTrue(all(r["dead"] for r in att))
            self.assertFalse(any(r["seed"] == 1 for r in att))
            self.assertEqual(len(glob.glob(os.path.join(d, "arm*", "seed0", "pyautogui", "screenshot", "*", "*",
                                                        f"{TASK}.dead1"))), 3)
            st = subprocess.run([sys.executable, os.path.join(HERE, "runner.py"), "status", "--results", d],
                                capture_output=True, text=True)
            self.assertEqual(st.returncode, 3)
            self.assertEqual(analysis.analyse(d, [f"chrome/{TASK}"], [0])["n_pairs_valid"], 0)

    def test_hung_episode_times_out(self):
        with tempfile.TemporaryDirectory() as d:
            code, log = run(d, "--seeds", "0", "--mock-hang-task", TASK, "--episode-timeout-min", "0.05")
            self.assertEqual(code, 3, log[-3000:])
            att = [r for r in jl(os.path.join(d, "ledger.jsonl")) if r.get("kind") == "attempt"]
            self.assertEqual(len(att), 6)
            self.assertTrue(all(r["dead"] and r["error"] == "episode timeout" for r in att))

    def test_refusals_before_any_episode(self):
        with tempfile.TemporaryDirectory() as d:
            runner = os.path.join(HERE, "runner.py")
            p = subprocess.run([PY, runner, "run", "--results", d, "--shard", "0/20", "--seeds", "0,1", "--go"],
                               capture_output=True, text=True, timeout=120)
            self.assertEqual(p.returncode, 2)
            self.assertIn("exactly one seed", p.stdout)
            p = subprocess.run([PY, runner, "run", "--results", d, "--go", "--max-tasks", "1"],
                               capture_output=True, text=True, timeout=120)
            self.assertEqual(p.returncode, 2)
            self.assertIn("no sub-sample", p.stdout)
            env = {k: v for k, v in os.environ.items() if not k.startswith("GUARD_")}
            p = subprocess.run([PY, runner, "run", "--results", d, "--go", "--base-urls", "http://127.0.0.1:9/v1"],
                               capture_output=True, text=True, timeout=300, env=env)
            self.assertEqual(p.returncode, 2)
            self.assertIn("REFUSED, preflight failed", p.stdout)
            self.assertIn("GUARD_BASE_URL unset", p.stdout)
            p = subprocess.run([PY, runner, "run", "--results", d, "--base-urls", "http://127.0.0.1:9/v1"],
                               capture_output=True, text=True, timeout=120)
            self.assertEqual(p.returncode, 0)
            self.assertIn("DRY RUN", p.stdout)
            self.assertFalse(os.path.exists(os.path.join(d, "ledger.jsonl")))


if __name__ == "__main__":
    unittest.main()
