import unittest
from unittest.mock import patch

from beta.student_beta_runner import run_beta


class BetaRunnerTests(unittest.TestCase):
    def test_beta_report_all_scenarios_pass(self):
        fake = object.__new__(type("FakeAgent", (), {}))
        responses = {
            "": "Tell me what you'd like to work on.",
            "I have 30 minutes to study": "I can make the plan, but I need one important detail first: what subject is the exam for?",
            "I have 30 minutes for Physics": "I need indexed NCERT material for Physics before I can build a source-grounded plan.",
            "remember that I study best in the evening": 'I can remember this:\n"x"\n\nWould you like me to save it to long-term memory?',
            "I still don't understand Newton's third law": "Let's focus on the concept you found difficult and practice it.",
            "Explain Newton's third law simply.": "Newton's third law explanation.",
        }
        fake.process = lambda text: responses[text]
        report = run_beta(fake)
        self.assertTrue(report.success)
        self.assertEqual(report.total, 6)
        self.assertEqual(report.passed, 6)


if __name__ == "__main__":
    unittest.main()
