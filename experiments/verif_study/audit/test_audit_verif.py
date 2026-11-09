import unittest

from audit_verif import classify_verdict, explicit_requirement_decisions, wilson


class AuditParserTests(unittest.TestCase):
    def test_requirement_parentheses_do_not_override_explicit_status(self):
        text = (
            "1. Colors are exact (no variations) - yes\n"
            "2. Clean slate (no quoted content)\n"
            "3. Total row complete (no)\n"
            "VERDICT: INCOMPLETE"
        )
        counts, status = explicit_requirement_decisions(text)
        self.assertEqual(dict(counts), {"yes": 1, "no": 1})
        self.assertEqual(status, "parsed_explicit_lines")

    def test_markdown_verdict_and_truncation(self):
        self.assertEqual(
            classify_verdict(
                '\"VERDICT\": \"INCOMPLETE\"', status="ok", finish_reason="stop"
            )[0],
            "incomplete",
        )
        self.assertEqual(
            classify_verdict(
                "**VERDICT:** COMPLETE", status="ok", finish_reason="stop"
            )[0],
            "complete",
        )
        self.assertEqual(
            classify_verdict(
                "VERDICT: COMPLETE", status="ok", finish_reason="length"
            )[0],
            "truncated",
        )
        self.assertEqual(
            classify_verdict(None, status="ok", finish_reason="length")[0],
            "truncated",
        )

    def test_missing_malformed_and_conflicting_verdicts(self):
        self.assertEqual(
            classify_verdict("No decision", status="ok", finish_reason="stop")[0],
            "missing",
        )
        self.assertEqual(
            classify_verdict("VERDICT maybe", status="ok", finish_reason="stop")[0],
            "malformed",
        )
        self.assertEqual(
            classify_verdict(
                "VERDICT: COMPLETE\nVERDICT: INCOMPLETE",
                status="ok",
                finish_reason="stop",
            )[0],
            "ambiguous",
        )
        self.assertEqual(
            classify_verdict(
                "Finally answer VERDICT: COMPLETE or INCOMPLETE.\nVERDICT: INCOMPLETE",
                status="ok",
                finish_reason="stop",
            )[0],
            "incomplete",
        )

    def test_wilson_zero_of_two(self):
        low, high = wilson(0, 2)
        self.assertAlmostEqual(low, 0.0)
        self.assertAlmostEqual(high, 0.6576197724933469)


if __name__ == "__main__":
    unittest.main()
