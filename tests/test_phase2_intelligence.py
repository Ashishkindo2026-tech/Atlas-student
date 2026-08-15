import unittest
from brain.agent import AtlasAgent


class Phase2IntelligenceTests(unittest.TestCase):
    def test_mistake_is_recorded_and_acknowledged(self):
        agent = AtlasAgent()
        response = agent.process("I made mistakes in physics chapter 3")
        self.assertIn("difficulty signal", response.lower())
        data = agent.progress.data()
        self.assertTrue(any(s["kind"] == "difficulty" and s["subject"] == "physics" for s in data["learning_signals"]))

    def test_weak_topics_are_reported_from_evidence(self):
        agent = AtlasAgent()
        agent.process("I made mistakes in physics chapter 3")
        response = agent.process("which topics am I weak in?")
        self.assertIn("Physics / chapter 3", response)
        self.assertIn("difficulty signal", response)

    def test_natural_language_goal_is_saved(self):
        agent = AtlasAgent()
        response = agent.process("set my goal to finish physics chapter 3 this week")
        self.assertIn("added this goal", response.lower())
        self.assertTrue(any(g["text"] == "finish physics chapter 3 this week" for g in agent.goals.get_goals()))

    def test_goal_persists_for_new_agent(self):
        agent = AtlasAgent()
        agent.process("set my goal to finish physics chapter 3 this week")
        fresh = AtlasAgent()
        self.assertTrue(any(g["text"] == "finish physics chapter 3 this week" for g in fresh.goals.get_goals()))


if __name__ == "__main__":
    unittest.main()
