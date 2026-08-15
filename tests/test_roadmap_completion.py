import unittest
import tempfile
import json
from pathlib import Path

from brain.student_intelligence import StudentIntelligence, AdaptiveLearning
from guidance.career import GuidanceEngine
from student.lifecycle import AtlasLifecycle, PHASES


class RoadmapCompletionTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.old = Path.cwd()
        import os; os.chdir(self.tmp.name)
        Path("student").mkdir()
        # Intelligence module resolves its own repo path, so use a direct temp file only for API sanity.
        self.intelligence = StudentIntelligence()

    def tearDown(self):
        import os; os.chdir(self.old); self.tmp.cleanup()

    def test_all_six_phases_registered(self):
        self.assertEqual(set(PHASES), {1, 2, 3, 4, 5, 6})
        self.assertTrue(all(PHASES[i][1] for i in PHASES))

    def test_mistakes_create_weak_topic_evidence(self):
        self.intelligence.record_attempt("Physics", "Kinematics", False)
        self.intelligence.record_attempt("Physics", "Kinematics", True)
        self.intelligence.record_mistake("Physics", "Kinematics", "mixed up velocity and acceleration")
        weak = self.intelligence.weak_topics()
        self.assertTrue(any(x["topic"] == "Kinematics" for x in weak))

    def test_adaptive_path_uses_weak_topics(self):
        self.intelligence.record_mistake("Math", "Trigonometry", "identity error")
        path = AdaptiveLearning(self.intelligence).next_path("Math")
        self.assertEqual(path[0]["topic"], "Trigonometry")

    def test_career_guidance_is_ranked(self):
        results = GuidanceEngine().recommend({"mathematics": 90, "physics": 85, "computer science": 95}, ["programming"])
        self.assertGreaterEqual(len(results), 1)
        self.assertGreaterEqual(results[0]["score"], results[-1]["score"])

    def test_lifecycle_defaults_offline(self):
        lifecycle = AtlasLifecycle()
        self.assertTrue(lifecycle.status()["state"]["offline"])


if __name__ == "__main__": unittest.main()
