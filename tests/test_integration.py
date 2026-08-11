import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from brain.agent import AtlasAgent


class FakeLLM:
    def __init__(self):
        self.calls = []

    def ask(self, prompt, **kwargs):
        self.calls.append(prompt)
        return "Integration test response"


class AtlasIntegrationTests(unittest.TestCase):
    def test_agent_builds_context_and_reaches_llm(self):
        fake = FakeLLM()
        with patch("brain.agent.Ollama_Client", return_value=fake):
            agent = AtlasAgent()
            result = agent.process("Explain Atlas in one sentence.")

        self.assertEqual(result, "Integration test response")
        self.assertEqual(len(fake.calls), 1)
        self.assertIn("Explain Atlas", fake.calls[0])
        self.assertIn("Atlas Student", fake.calls[0])
        self.assertIn("ACTIVE GOALS", fake.calls[0])
        self.assertIn("CURRENT USER MESSAGE", fake.calls[0])

    def test_agent_handles_empty_input(self):
        agent = AtlasAgent()
        result = agent.process("")
        self.assertIsInstance(result, str)
        self.assertTrue(result.strip())

    def test_learning_signal_flows_from_conversation_to_progress(self):
        fake = FakeLLM()
        with tempfile.TemporaryDirectory() as tmp:
            progress_file = Path(tmp) / "progress.json"
            with patch("brain.agent.Ollama_Client", return_value=fake), \
                 patch("student.progress_manager.FILE", progress_file):
                agent = AtlasAgent()
                result = agent.process("I still don't understand friction in physics.")
                data = agent.progress.data()

        self.assertEqual(result, "Integration test response")
        self.assertEqual(len(data["learning_signals"]), 1)
        signal = data["learning_signals"][0]
        self.assertEqual(signal["kind"], "difficulty")
        self.assertEqual(signal["subject"], "physics")
        self.assertIn("friction", signal["evidence"].lower())
        self.assertIn("LEARNING PROGRESS", fake.calls[0])


if __name__ == "__main__":
    unittest.main()
