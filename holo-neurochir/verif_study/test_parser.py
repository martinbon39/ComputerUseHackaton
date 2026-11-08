import unittest

from analyze import parse_response


def response(text, finish='stop'):
    return {'status': 'ok', 'response': {'choices': [
        {'finish_reason': finish, 'message': {'content': text, 'reasoning': 'Evidence check'}}]}}


class RequirementParserTests(unittest.TestCase):
    def test_requirement_negation_does_not_become_no_rating(self):
        text = ('1. Colors are exact (no variations) - yes\n'
                '2. Ensure replies start with a clean slate (no quoted content)\n'
                '3. Text colors must be exact (no variations like light red)\n'
                '4. Six blank slides (no textboxes) - condition not satisfied\n'
                'VERDICT: INCOMPLETE')
        decisions = parse_response(response(text))['requirement_decisions']
        self.assertEqual([row['decision'] for row in decisions], ['yes'])

    def test_explicit_terminal_parenthetical_ratings(self):
        text = '1. Total row is at the bottom (yes)\n2. Correct file name (no).\n3. Saved (cannot tell)\nVERDICT: INCOMPLETE'
        decisions = parse_response(response(text))['requirement_decisions']
        self.assertEqual([row['decision'] for row in decisions], ['yes', 'no', 'cannot tell'])

    def test_truncation_cannot_supply_a_valid_verdict(self):
        self.assertEqual(parse_response(response('VERDICT: COMPLETE', 'length'))['verdict'], 'TRUNCATED')

    def test_missing_and_conflicting_verdicts_are_distinct(self):
        self.assertEqual(parse_response(response('No final decision'))['verdict'], 'MISSING_VERDICT')
        self.assertEqual(parse_response(response('VERDICT: COMPLETE\nVERDICT: INCOMPLETE'))['verdict'], 'CONFLICTING_VERDICTS')

    def test_quoted_verdict_field_is_an_explicit_verdict(self):
        self.assertEqual(parse_response(response('{"VERDICT": "INCOMPLETE"}'))['verdict'], 'INCOMPLETE')
        self.assertEqual(parse_response(response('{"VERDICT": "COMPLETE"}'))['verdict'], 'COMPLETE')
        self.assertEqual(parse_response(response('{"VERDICT": "COMPLETE"}\n{"VERDICT": "INCOMPLETE"}'))['verdict'], 'CONFLICTING_VERDICTS')

    def test_echoed_choice_list_is_not_a_verdict(self):
        text = 'Finally answer VERDICT: COMPLETE or INCOMPLETE.\nVERDICT: INCOMPLETE'
        self.assertEqual(parse_response(response(text))['verdict'], 'INCOMPLETE')
        self.assertEqual(parse_response(response('VERDICT: COMPLETE or INCOMPLETE.'))['verdict'], 'MALFORMED_VERDICT')


if __name__ == '__main__':
    unittest.main()
