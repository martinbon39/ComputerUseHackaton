"""Seed function and neutral verifier stub (stdlib only)."""
import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import neutral_verifier as nv  # noqa: E402
import seeding  # noqa: E402


class SeedFunction(unittest.TestCase):
    def test_deterministic_and_in_range(self):
        a = seeding.request_seed(0, "44ee5668-ecd5-4366-a6ce-c1c9b8d4e938", 3, 0)
        self.assertEqual(a, seeding.request_seed(0, "44ee5668-ecd5-4366-a6ce-c1c9b8d4e938", 3, 0))
        self.assertTrue(0 <= a < 2 ** 31)

    def test_each_argument_matters(self):
        base = seeding.request_seed(0, "t", 3, 0)
        for other in (seeding.request_seed(1, "t", 3, 0), seeding.request_seed(0, "u", 3, 0),
                      seeding.request_seed(0, "t", 4, 0), seeding.request_seed(0, "t", 3, 1)):
            self.assertNotEqual(base, other)

    def test_no_collisions_over_the_study(self):
        seeds = {seeding.request_seed(s, f"task{t}", st, 0) for s in range(3) for t in range(120) for st in range(50)}
        self.assertGreater(len(seeds), 3 * 120 * 50 - 5)


class SeededClass(unittest.TestCase):
    """seeded() on a stand-in loop with the same contract as HoloComputerAgent (client, on_step, _call_model)."""

    class FakeCompletions:
        def __init__(self):
            self.seeds = []

        def create(self, **kw):
            self.seeds.append(kw.get("seed"))
            return None

    class Loop:
        def __init__(self, client, on_step=None):
            self.client, self.on_step = client, on_step

        def _call_model(self, messages):
            self.client.chat.completions.create(model="m", messages=messages)
            return "", ""

        def run(self, plan):
            steps = 0
            for kind in plan:
                self._call_model([])
                if kind == "retry":
                    continue
                if self.on_step:
                    self.on_step(steps, None, None, {}, "")
                steps += 1

    def _client(self):
        comp = self.FakeCompletions()
        chat = type("Chat", (), {"completions": comp})()
        return type("Client", (), {"chat": chat})(), comp

    def test_step_and_retry_indices(self):
        client, comp = self._client()
        seeding.EpisodeContext.set(2, "task", None)
        try:
            agent = seeding.seeded(self.Loop)(client, on_step=lambda *a: None)
        finally:
            seeding.EpisodeContext.clear()
        agent.run(["ok", "retry", "ok", "ok"])
        want = [seeding.request_seed(2, "task", 0, 0), seeding.request_seed(2, "task", 1, 0),
                seeding.request_seed(2, "task", 1, 1), seeding.request_seed(2, "task", 2, 0)]
        self.assertEqual(comp.seeds, want)

    def test_refuses_without_context(self):
        client, _ = self._client()
        with self.assertRaises(RuntimeError):
            seeding.seeded(self.Loop)(client)


class NeutralStub(unittest.TestCase):
    def test_always_complete_with_recorded_delay(self):
        slept = []
        f = nv.NeutralFeci(0, "t", sleep=slept.append)
        r = f.check("do x", b"png", "done")
        self.assertEqual((r["verdict"], r["kind"], r["feedback"]), ("accept", "complete", ""))
        self.assertIn(slept[0], nv.recorded())
        self.assertEqual(r["detail"]["latency_s"], slept[0])

    def test_delay_reproducible(self):
        self.assertEqual(nv.draw_latency(1, "t", 0), nv.draw_latency(1, "t", 0))

    def test_distribution_matches_recorded(self):
        r = nv.report(10000)
        print("\nquantile recorded drawn")
        for q in r["quantiles_recorded"]:
            print(f"  {q:>5} {r['quantiles_recorded'][q]:6.2f} {r['quantiles_drawn'][q]:6.2f}")
        print(f"KS D={r['ks_D']:.4f} p={r['ks_p']:.3f} (n_recorded={r['n_recorded']})")
        self.assertEqual(r["n_recorded"], 96)
        self.assertGreater(r["ks_p"], 0.05)
        for q in (0.25, 0.5, 0.75):
            self.assertLessEqual(abs(r["quantiles_recorded"][q] - r["quantiles_drawn"][q]), 0.5)


if __name__ == "__main__":
    unittest.main()
