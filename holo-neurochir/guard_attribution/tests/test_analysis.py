"""analysis.py on synthetic results: a planted effect is recovered; with no effect the interval covers 0."""
import os
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import analysis  # noqa: E402
import synth  # noqa: E402


class Synthetic(unittest.TestCase):
    def run_one(self, p, gen_seed=0, dead=None, n_boot=None):
        with tempfile.TemporaryDirectory() as d:
            tasks = synth.make(d, p, gen_seed=gen_seed, dead=dead)
            if n_boot:
                old = analysis.N_BOOT
                analysis.boot.__defaults__ = (n_boot, analysis.BOOT_SEED)
                try:
                    return analysis.analyse(d, tasks, [0, 1, 2])
                finally:
                    analysis.boot.__defaults__ = (old, analysis.BOOT_SEED)
            return analysis.analyse(d, tasks, [0, 1, 2])

    def test_planted_effect_recovered(self):
        r = self.run_one({"A": 0.25, "B": 0.25, "C": 0.08})
        p = r["primary_C_minus_B_false_done"]
        print(f"\nplanted -17 pts: diff {p['diff']:+.3f} CI {p['ci95']}")
        self.assertEqual(p["n_tasks"], 120)
        self.assertLess(p["ci95"][1], 0)
        self.assertTrue(p["guard_reduces_false_done"])
        self.assertLess(abs(r["s1_B_minus_A_false_done"]["diff"]), 0.03)
        self.assertGreater(r["s3_seed_fidelity_A_vs_B"]["share"], 0.9)

    def test_no_effect_covers_zero(self):
        r = self.run_one({"A": 0.2, "B": 0.2, "C": 0.2})
        p = r["primary_C_minus_B_false_done"]
        print(f"\nnull: diff {p['diff']:+.3f} CI {p['ci95']}")
        self.assertLess(p["ci95"][0], 0)
        self.assertGreater(p["ci95"][1], 0)
        self.assertFalse(p["guard_reduces_false_done"])

    def test_null_coverage(self):
        cover = 0
        n = 30
        for g in range(1, n + 1):
            p = self.run_one({"A": 0.2, "B": 0.2, "C": 0.2}, gen_seed=g, n_boot=1000)["primary_C_minus_B_false_done"]
            cover += p["ci95"][0] <= 0 <= p["ci95"][1]
        print(f"\nnull coverage {cover}/{n}")
        self.assertGreaterEqual(cover / n, 0.83)

    def test_dead_episode_drops_task_seed_in_all_arms(self):
        r = self.run_one({"A": 0.2, "B": 0.2, "C": 0.1}, dead=[("B", 1, 5)])
        self.assertEqual(r["n_pairs_valid"], 359)
        self.assertEqual(len(r["dropped_task_seed"]), 1)
        self.assertIn("seed1", r["dropped_task_seed"][0])
        self.assertEqual(r["n_tasks_valid"], 120)
        self.assertEqual(r["s4_never_answered_step_cap"]["rates"]["A"]["episodes"], 359)

    def test_boot_matches_online_guard_analysis(self):
        here = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        sys.path.insert(0, os.path.join(here, "report"))
        import online_guard_analysis as oga
        d = [1.0, 0.0, -1.0, 0.0, 0.0, -1.0, 0.5]
        self.assertEqual(oga.boot(d), analysis.boot(d))


if __name__ == "__main__":
    unittest.main()
