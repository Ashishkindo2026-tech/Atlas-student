"""End-to-end regression test for a realistic Atlas Student session."""
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from brain.agent import AtlasAgent
from learning.learning_signal_detector import detect
from student.progress_manager import ProgressManager


class FakeLLM:
    def __init__(self):
        self.calls = []

    def ask(self, prompt, **kwargs):
        self.calls.append(prompt)
        return "Let's focus on the concept you found difficult and practice it."


class StudentJourneyTests(unittest.TestCase):
    def test_student_journey_memory_learning_progress_and_plan_context(self):
        with tempfile.TemporaryDirectory() as tmp:
            progress_file = Path(tmp) / "progress.json"
            with patch("student.progress_manager.FILE", progress_file):
                manager = ProgressManager()

                # Student explicitly reports a difficulty signal.
                signal = detect(
                    "I still don't understand Newton's third law",
                    "Newton's Third Law",
                )
                self.assertIsNotNone(signal)
                self.assertTrue(manager.record_learning_signal(
                    signal.kind, signal.concept, signal.confidence,
                    signal.evidence, subject="Physics",
                ))

                # A real study session is recorded separately from mastery.
                manager.record_session("Physics", 35, "Newton's Third Law")

                # A later positive signal becomes additional evidence.
                signal = detect(
                    "Now I understand Newton's third law",
                    "Newton's Third Law",
                )
                self.assertIsNotNone(signal)
                manager.record_learning_signal(
                    signal.kind, signal.concept, signal.confidence,
                    signal.evidence, subject="Physics",
                )

                data = manager.data()
                self.assertEqual(len(data["learning_signals"]), 2)
                self.assertEqual(data["learning_signals"][0]["kind"], "difficulty")
                self.assertEqual(data["learning_signals"][1]["kind"], "understood")
                self.assertEqual(data["subjects"]["Physics"]["minutes"], 35)

                # Atlas still reaches the LLM with its normal integrated context.
                fake = FakeLLM()
                with patch("brain.agent.Ollama_Client", return_value=fake):
                    agent = AtlasAgent()
                    result = agent.process("Help me revise Newton's third law.")

                self.assertTrue(result.strip())
                self.assertEqual(len(fake.calls), 1)
                prompt = fake.calls[0].lower()
                self.assertIn("atlas student", prompt)
                self.assertIn("newton's third law", prompt)
                self.assertIn("current user message", prompt)


if __name__ == "__main__":
    unittest.main()
