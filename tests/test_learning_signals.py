import unittest

from learning.learning_signal_detector import detect


class LearningSignalTests(unittest.TestCase):
    def test_understood_signal(self):
        signal = detect("Now I understand quadratic equations")
        self.assertIsNotNone(signal)
        self.assertEqual(signal.kind, "understood")
        self.assertEqual(signal.confidence, 0.90)
        self.assertEqual(signal.concept, "quadratic equations")

    def test_difficulty_signal(self):
        signal = detect("I still don't understand vectors")
        self.assertIsNotNone(signal)
        self.assertEqual(signal.kind, "difficulty")
        self.assertEqual(signal.concept, "vectors")

    def test_neutral_message_is_not_learning_evidence(self):
        self.assertIsNone(detect("Explain vectors to me"))

    def test_explicit_concept_overrides_extraction(self):
        signal = detect("I got it", concept="Newton's laws")
        self.assertEqual(signal.concept, "Newton's laws")


if __name__ == "__main__":
    unittest.main()
