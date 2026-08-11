import json
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
            with patch("personality.personality.FILE", path):
                first = Personality()
                first.observe("verbosity", "concise", 0.7, "test", "general")
                second = Personality()
                data = second.get()
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
            path = os.path.join(d, "goals.json")
            with patch("goals.goal_manager.FILE", path):
                goals = GoalManager()
                self.assertTrue(goals.add_goal("Build Atlas Student"))
                self.assertFalse(goals.add_goal("Build Atlas Student"))
                self.assertTrue(goals.complete_goal("Build Atlas Student"))
                self.assertFalse(goals.complete_goal("Build Atlas Student"))

    def test_corrupt_personality_file_recovers(self):
        with tempfile.TemporaryDirectory() as d:
            path = os.path.join(d, "adaptation.json")
            with open(path, "w", encoding="utf-8") as f:
                f.write("{broken json")
            with patch("personality.personality.FILE", path):
                personality = Personality()
                data = personality.get()
                self.assertIsInstance(data, dict)
                self.assertIn("preferences", data)


if __name__ == "__main__":
    unittest.main()
