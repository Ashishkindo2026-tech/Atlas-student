import os
import tempfile
import unittest
from unittest.mock import patch

from brain.memory_router import MemoryRouter
from personality.personality import Personality
from goals.goal_manager import GoalManager
from user.knowledge import UserKnowledge


class AtlasRobustnessTests(unittest.TestCase):
    def test_memory_router_commands(self):
        router = MemoryRouter()
        self.assertEqual(router.route("remember that I like Atlas")["type"], "memory_request")
        self.assertEqual(router.route("forget Atlas")["type"], "forget_request")
        self.assertEqual(router.route("what do you remember")["type"], "show_memory")
        self.assertEqual(router.route("forget everything")["type"], "forget_all")
        self.assertEqual(router.route("show archive")["type"], "show_archive")

    def test_personality_survives_reload(self):
        with tempfile.TemporaryDirectory() as d:
            path = os.path.join(d, "adaptation.json")
            with patch("personality.personality.ADAPTATION_FILE", path):
                first = Personality()
                first.observe("Keep it short, please.")
                second = Personality()
                data = second.get_adaptation()
                self.assertIn("verbosity", data["preferences"])
                self.assertEqual(data["preferences"]["verbosity"]["value"], "concise")

    def test_user_knowledge_round_trip(self):
        with tempfile.TemporaryDirectory() as d:
            path = os.path.join(d, "user_knowledge.json")
            with patch("user.knowledge.FILE", path):
                profile = UserKnowledge()
                profile.remember("preferences", "language", "Hinglish")
                reloaded = UserKnowledge()
                self.assertEqual(reloaded.get()["preferences"]["language"]["value"], "Hinglish")

    def test_goal_round_trip(self):
        with tempfile.TemporaryDirectory() as d:
            old_cwd = os.getcwd()
            try:
                os.chdir(d)
                goals = GoalManager()
                self.assertTrue(goals.add_goal("Build Atlas Student"))
                self.assertFalse(goals.add_goal("Build Atlas Student"))
                self.assertTrue(goals.update_progress("Build Atlas Student", 50))
                self.assertEqual(goals.get_goals()[0]["progress"], 50)
                self.assertTrue(goals.complete_goal("Build Atlas Student"))
                self.assertFalse(goals.complete_goal("Build Atlas Student"))
            finally:
                os.chdir(old_cwd)

    def test_corrupt_personality_file_recovers(self):
        with tempfile.TemporaryDirectory() as d:
            path = os.path.join(d, "adaptation.json")
            with open(path, "w", encoding="utf-8") as f:
                f.write("{broken json")
            with patch("personality.personality.ADAPTATION_FILE", path):
                personality = Personality()
                data = personality.get_adaptation()
                self.assertIsInstance(data, dict)
                self.assertIn("preferences", data)


if __name__ == "__main__":
    unittest.main()
