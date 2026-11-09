"""Arm D: placebo stub and the supplementary analysis (stdlib only)."""
import os
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import analysis_placebo as AP  # noqa: E402
import neutral_verifier as nv  # noqa: E402
import synth  # noqa: E402


class PlaceboStub(unittest.TestCase):
    def test_rate_and_determinism(self):
        draws = [nv.placebo_refuses(s, f"task{t}", c) for s in range(3) for t in range(2000) for c in range(2)]
        rate = sum(draws) / len(draws)
        print(f"\nplacebo refusal rate over {len(draws)} draws: {rate:.4f} (target {nv.PLACEBO_RATE})")
        self.assertLess(abs(rate - nv.PLACEBO_RATE), 0.01)
        self.assertEqual(nv.placebo_refuses(1, "t", 0), nv.placebo_refuses(1, "t", 0))

    def test_same_draws_on_rerun_and_same_latency_as_B(self):
        for seed, task in ((0, "a"), (1, "b"), (2, "c")):
            runs = []
            for _ in range(2):
                f, slept = nv.PlaceboFeci(seed, task, sleep=lambda s: None), []
                f.sleep = slept.append
                runs.append([(f.check("x", b"png")["verdict"], slept[-1]) for _ in range(4)])
            self.assertEqual(runs[0], runs[1])
            b = nv.NeutralFeci(seed, task, sleep=lambda s: None)
            self.assertEqual([x[1] for x in runs[0]], [b.check("x", b"png")["detail"]["latency_s"] for _ in range(4)])

    def test_refusal_shape(self):
        f = nv.PlaceboFeci(0, "t", sleep=lambda s: None)
        rs = [f.check("x", b"png") for _ in range(40)]
        rej = [r for r in rs if r["verdict"] == "reject"]
        self.assertTrue(rej)
        for r in rej:
            self.assertEqual((r["kind"], r["feedback"]), ("incomplete", nv.PLACEBO_MESSAGE))
            self.assertEqual(r["detail"]["backend"], "placebo_stub")
        self.assertTrue(all(r["kind"] == "complete" for r in rs if r["verdict"] == "accept"))
        self.assertTrue(nv.PlaceboFeci.VERIFIER_SHA.startswith("placebo-"))


    def test_no_screenshot_passes_like_the_real_guard(self):
        f = nv.PlaceboFeci(0, "t", sleep=lambda s: None)
        rs = [f.check("x", None) for _ in range(20)]
        self.assertTrue(all(r["verdict"] == "accept" and r["kind"] == "no_verdict" for r in rs))


class FrozenStudyUntouched(unittest.TestCase):
    def test_dead_D_episode_does_not_reach_frozen_outputs(self):
        import analysis as A
        sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        import runner
        with tempfile.TemporaryDirectory() as d:
            tasks = synth.make(d, {"A": .25, "B": .25, "C": .1, "D": .2}, dead=[("D", 0, 3)],
                               refusal={"C": .23, "D": .23})
            r = A.analyse(d, tasks, [0, 1, 2])
            self.assertEqual(r["n_pairs_valid"], 360)
            self.assertEqual(r["dropped_task_seed"], [])
            self.assertFalse(any("armD" in x for x in r["ledger"]["dead_attempts"] + r["ledger"]["reruns"]))
            st = runner.status(d, n_tasks=120)
            self.assertEqual(st[0]["dead_first_attempt"], 0)
            self.assertEqual(st[0]["arm_D"]["dead_first_attempt"], 1)
            self.assertEqual(AP.analyse(d, tasks)["n_pairs_valid"], 359)


class SupplementaryAnalysis(unittest.TestCase):
    def run_one(self, p, refusal):
        with tempfile.TemporaryDirectory() as d:
            tasks = synth.make(d, p, refusal=refusal)
            return AP.analyse(d, tasks)

    def test_guard_better_than_placebo_detected(self):
        r = self.run_one({"A": .25, "B": .25, "C": .08, "D": .22}, {"C": .23, "D": .23})
        p = r["primary_C_minus_D_false_done"]
        print(f"\nC-D planted: {p['diff']:+.3f} {p['ci95']}  kill={p['kill_rule']['killed']}")
        self.assertFalse(p["kill_rule"]["killed"])
        self.assertTrue(p["verdict_lowers_false_done"])
        self.assertEqual(sum(r["s3_competing_risks"]["C"].values()), 360)
        self.assertLess(r["s4_signflip"]["C_minus_D_false_done_p"], 0.01)

    def test_no_difference_not_claimed(self):
        r = self.run_one({"A": .25, "B": .25, "C": .2, "D": .2}, {"C": .23, "D": .23})
        p = r["primary_C_minus_D_false_done"]
        self.assertFalse(p["verdict_lowers_false_done"])

    def test_kill_rule(self):
        r = self.run_one({"A": .25, "B": .25, "C": .08, "D": .22}, {"C": .03, "D": .23})
        p = r["primary_C_minus_D_false_done"]
        self.assertTrue(p["kill_rule"]["killed"])
        self.assertFalse(p["verdict_lowers_false_done"])


if __name__ == "__main__":
    unittest.main()
