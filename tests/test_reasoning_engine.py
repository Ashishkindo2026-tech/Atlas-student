import unittest

from brain.reasoning_engine import ReasoningEngine


class ReasoningEngineTests(unittest.TestCase):
    def setUp(self):
        self.engine = ReasoningEngine()

    def test_study_request_without_subject_reports_missing_subject(self):
        plan = self.engine.plan("I have 2 hours to study for tomorrow's exam")
        self.assertEqual(plan.intent, "study_planning")
        self.assertEqual(plan.constraints["available_hours"], "2")
        self.assertIn("subject", plan.missing)

    def test_study_topic_without_subject_is_accepted_as_explicit_context(self):
        plan = self.engine.plan("I have 2 hours to revise quadratic equations for tomorrow")
        self.assertEqual(plan.intent, "study_planning")
        self.assertNotIn("subject", plan.missing)
        self.assertEqual(plan.constraints["available_hours"], "2")
        self.assertEqual(plan.constraints["deadline"], "tomorrow")

    def test_explicit_subject_is_not_marked_missing(self):
        plan = self.engine.plan("I have 45 minutes to revise physics for tomorrow")
        self.assertEqual(plan.intent, "study_planning")
        self.assertNotIn("subject", plan.missing)
        self.assertEqual(plan.constraints["available_minutes"], "45")
        self.assertEqual(plan.constraints["deadline"], "tomorrow")

    def test_decision_plan_has_verification(self):
        plan = self.engine.plan("Which option should I choose?")
        self.assertEqual(plan.intent, "decision")
        self.assertTrue(plan.steps)
        self.assertTrue(plan.verification)

    def test_unrelated_preference_is_not_used_as_subject(self):
        self.assertFalse(self.engine._subject_is_explicit("I like physics but my exam is tomorrow"))


if __name__ == "__main__":
    unittest.main()
