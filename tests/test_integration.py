import os
import unittest
from unittest.mock import patch

from brain.agent import AtlasAgent


class FakeLLM:
    def __init__(self):
        self.calls = []

    def generate(self, prompt, **kwargs):
        self.calls.append(prompt)
        return "Integration test response"


class AtlasIntegrationTests(unittest.TestCase):
    def test_agent_builds_context_and_reaches_llm(self):
        fake = FakeLLM()
        with patch("brain.agent.OllamaClient", return_value=fake):
            agent = AtlasAgent()
            result = agent.process("Explain Atlas in one sentence.")

        self.assertIsInstance(result, str)
        self.assertEqual(result, "Integration test response")
        self.assertEqual(len(fake.calls), 1)
        self.assertIn("Explain Atlas", fake.calls[0])

    def test_agent_handles_empty_input(self):
        agent = AtlasAgent()
        result = agent.process("")
        self.assertIsInstance(result, str)
        self.assertTrue(result.strip())


if __name__ == "__main__":
    unittest.main()
