import unittest
from datetime import datetime, timedelta, timezone

from student.advanced_intelligence import (
    AdvancedStudentSystem,
    AtlasContinuity,
    AutonomousStudyPlanner,
    LearningCoach,
    PredictiveIntelligence,
    RealWorldAssistant,
    StudentDigitalTwin,
)


class TestPhases7To12(unittest.TestCase):
    def setUp(self):
        self.attempts = [
            {"subject": "Physics", "topic": "Kinematics", "correct": True},
            {"subject": "Physics", "topic": "Kinematics", "correct": False},
            {"subject": "Physics", "topic": "Kinematics", "correct": False},
            {"subject": "Physics", "topic": "Kinematics", "correct": False},
            {"subject": "Math", "topic": "Trigonometry", "correct": True},
            {"subject": "Math", "topic": "Trigonometry", "correct": True},
        ]

    def test_predictive_weak_and_falling(self):
        engine = PredictiveIntelligence()
        weak = engine.predict_weak_chapters(self.attempts)
        self.assertTrue(any(x["topic"] == "Kinematics" for x in weak))
        falling = engine.detect_falling_performance([
            {"subject": "Physics", "topic": "Waves", "correct": True},
            {"subject": "Physics", "topic": "Waves", "correct": True},
            {"subject": "Physics", "topic": "Waves", "correct": False},
            {"subject": "Physics", "topic": "Waves", "correct": False},
        ])
        self.assertTrue(falling)

    def test_revision_and_next_recommendation(self):
        engine = PredictiveIntelligence()
        old = (datetime.now(timezone.utc) - timedelta(days=30)).isoformat()
        due = engine.revision_due([{"subject": "Math", "topic": "Algebra", "last_reviewed": old, "mastery": 20}])
        self.assertTrue(due)
        nxt = engine.recommend_next([], due, [{"goal": "Boards", "done": False}])
        self.assertEqual(nxt[0]["action"], "revise")

    def test_learning_coach(self):
        coach = LearningCoach()
        style = coach.best_style([
            {"style": "visual", "score": 90},
            {"style": "visual", "score": 80},
            {"style": "analogy", "score": 50},
        ])
        self.assertEqual(style, "visual")
        plan = coach.teaching_plan(35, style)
        self.assertEqual(plan["level"], "foundation")
        self.assertEqual(coach.missing_prerequisites("calculus", {"calculus": ["algebra"]}, ["geometry"]), ["algebra"])

    def test_autonomous_session(self):
        session = AutonomousStudyPlanner().session(60, "Kinematics")
        self.assertEqual([x["step"] for x in session["blocks"]], list(AutonomousStudyPlanner.STEPS))
        self.assertEqual(sum(x["minutes"] for x in session["blocks"]), 60)

    def test_real_world_priority(self):
        now = datetime.now(timezone.utc)
        tasks = RealWorldAssistant().prioritize([
            {"title": "Exam", "due": (now + timedelta(hours=12)).isoformat(), "importance": 1},
            {"title": "Project", "due": (now + timedelta(days=10)).isoformat(), "importance": 0},
        ], now=now)
        self.assertEqual(tasks[0]["title"], "Exam")

    def test_digital_twin(self):
        twin = StudentDigitalTwin().build(self.attempts, [{"topic": "Kinematics"}], [{"goal": "Boards", "done": False}], ["Physics"])
        self.assertEqual(twin["knowledge"]["attempts"], 6)
        self.assertIn("Kinematics", twin["skills"])
        self.assertEqual(twin["mistakes"], 1)

    def test_continuity(self):
        continuity = AtlasContinuity()
        bundle = continuity.export({"memories": 10}, [{"name": "Atlas"}], [{"name": "Project"}], [{"topic": "Physics"}], {"style": "step_by_step"})
        self.assertTrue(continuity.validate(bundle))
        self.assertEqual(continuity.migrate(bundle)["schema"], "atlas.student.continuity")

    def test_unified_facade(self):
        system = AdvancedStudentSystem()
        result = system.analyze(self.attempts)
        self.assertIn("weak_predictions", result)
        self.assertIn("next", result)


if __name__ == "__main__":
    unittest.main()
