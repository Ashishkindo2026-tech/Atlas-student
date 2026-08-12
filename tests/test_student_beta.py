"""Student Beta v0.1 acceptance tests for realistic Atlas Student usage."""
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
        return "I can help you revise that step by step."


class StudentBetaTests(unittest.TestCase):
    def test_empty_request_gets_safe_prompt(self):
        agent = AtlasAgent()
        self.assertEqual(agent.process(""), "Tell me what you'd like to work on.")

    def test_explicit_subject_is_used_for_study_planning(self):
        agent = AtlasAgent()
        fake = FakeLLM()
        with patch("brain.agent.Ollama_Client", return_value=fake), patch(
            "brain.agent.retrieve", return_value=[]
        ):
            result = agent.process("I have 30 minutes for Physics")
        self.assertTrue(result.strip())
        self.assertEqual(fake.calls, [])

    def test_missing_subject_is_not_guessed(self):
        agent = AtlasAgent()
        result = agent.process("I have 30 minutes to study")
        self.assertIn("what subject", result.lower())

    def test_learning_signal_is_recorded_as_evidence(self):
        with tempfile.TemporaryDirectory() as tmp:
            progress_file = Path(tmp) / "progress.json"
            with patch("student.progress_manager.FILE", progress_file):
                manager = ProgressManager()
                signal = detect("I still don't understand Newton's third law", "Newton's Third Law")
                self.assertIsNotNone(signal)
                manager.record_learning_signal(
                    signal.kind, signal.concept, signal.confidence,
                    signal.evidence, subject="Physics"
                )
                data = manager.data()
                self.assertEqual(data["learning_signals"][0]["kind"], "difficulty")
                self.assertEqual(data["learning_signals"][0]["subject"], "Physics")

    def test_learning_evidence_does_not_create_mastery(self):
        with tempfile.TemporaryDirectory() as tmp:
            progress_file = Path(tmp) / "progress.json"
            with patch("student.progress_manager.FILE", progress_file):
                manager = ProgressManager()
                signal = detect("Now I understand Newton's third law", "Newton's Third Law")
                manager.record_learning_signal(
                    signal.kind, signal.concept, signal.confidence,
                    signal.evidence, subject="Physics"
                )
                concept = manager.data()["concepts"].get("Newton's Third Law", {})
                self.assertNotIn("mastery", concept)

    def test_study_session_updates_subject_minutes(self):
        with tempfile.TemporaryDirectory() as tmp:
            progress_file = Path(tmp) / "progress.json"
            with patch("student.progress_manager.FILE", progress_file):
                manager = ProgressManager()
                self.assertTrue(manager.record_session("Physics", 35, "Newton's Third Law"))
                self.assertEqual(manager.data()["subjects"]["Physics"]["minutes"], 35)

    def test_memory_requires_explicit_confirmation(self):
        agent = AtlasAgent()
        first = agent.process("remember that my preferred study time is evening")
        self.assertIn("would you like me to save", first.lower())

    def test_realistic_study_question_reaches_llm_with_context(self):
        agent = AtlasAgent()
        fake = FakeLLM()
        with patch("brain.agent.Ollama_Client", return_value=fake):
            result = agent.process("Explain Newton's third law simply.")
        self.assertTrue(result.strip())
        self.assertEqual(len(fake.calls), 1)
        prompt = fake.calls[0].lower()
        self.assertIn("atlas student", prompt)
        self.assertIn("current user message", prompt)
        self.assertIn("newton's third law", prompt)


if __name__ == "__main__":
    unittest.main()
