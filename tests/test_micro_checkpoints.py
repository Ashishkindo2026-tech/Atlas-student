import json
import tempfile
import unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path
from unittest.mock import patch

from atlas_core.backup import export_bundle, restore_bundle
from atlas_core.service_registry import ServiceRegistry
from gui.theme_store import normalize_theme
from student.growth_system import GrowthSystem
from student.learning_system import LearningSystem


class MicroCheckpointTests(unittest.TestCase):
    def test_theme_migration(self):
        theme = normalize_theme({
            "background": "#000000",
            "panel": "#111111",
            "panel_alt": "#222222",
            "panel_hover": "#333333",
            "accent": "#ABCDEF",
            "accent_hover": "#FEDCBA",
        })
        self.assertEqual(theme["surface"], "#111111")
        self.assertEqual(theme["surface_2"], "#222222")
        self.assertEqual(theme["surface_hover"], "#333333")
        self.assertEqual(theme["accent_2"], "#FEDCBA")

    def test_adaptive_learning_and_revision(self):
        with tempfile.TemporaryDirectory() as tmp:
            state = Path(tmp) / "learning_state.json"
            with patch("student.learning_system.FILE", state):
                engine = LearningSystem()
                for _ in range(4):
                    engine.record_attempt("Physics", "Friction", False, difficulty=1)
                engine.record_attempt("Physics", "Friction", True, difficulty=1)
                self.assertTrue(engine.weak_topics("Physics"))
                self.assertEqual(engine.next_difficulty("Physics", "Friction"), 1)
                plan = engine.practice_plan("Physics", "Friction", 5)
                self.assertEqual(len(plan), 5)
                engine.schedule_revision("Physics", "Friction")
                due = engine.due_revisions(now=datetime.now(timezone.utc) + timedelta(days=2))
                self.assertTrue(due)

    def test_growth_goals_habits_and_insights(self):
        with tempfile.TemporaryDirectory() as tmp:
            state = Path(tmp) / "growth_state.json"
            with patch("student.growth_system.FILE", state):
                growth = GrowthSystem()
                goal = growth.create_goal("Finish Kinematics", target="Chapter 3")
                self.assertTrue(growth.update_goal(goal["id"], progress=50))
                habit = growth.add_habit("Study", 5)
                self.assertTrue(growth.check_habit(habit["id"]))
                growth.set_skill("Problem solving", 40, "Repeated calculation errors")
                insights = growth.insights()
                self.assertEqual(insights["active_goals"], 1)
                self.assertEqual(insights["habits"][0]["checks_this_week"], 1)
                self.assertTrue(insights["skills_needing_work"])

    def test_backup_round_trip(self):
        with tempfile.TemporaryDirectory() as tmp:
            project = Path(tmp)
            memory_dir = project / "memory"
            student_dir = project / "student"
            memory_dir.mkdir(); student_dir.mkdir()
            (memory_dir / "sample.json").write_text(json.dumps({"name": "Atlas"}), encoding="utf-8")
            (student_dir / "sample.json").write_text(json.dumps({"mastery": 82}), encoding="utf-8")
            backup = project / "backup.json"
            with patch("atlas_core.backup.ROOT", project), patch(
                "atlas_core.backup.DEFAULT_ROOTS",
                (memory_dir, student_dir),
            ):
                export_bundle(backup)
                (memory_dir / "sample.json").write_text("{}", encoding="utf-8")
                restored = restore_bundle(backup)
                self.assertIn("memory/sample.json", restored)
                self.assertEqual(json.loads((memory_dir / "sample.json").read_text())["name"], "Atlas")

    def test_service_registry_is_failure_safe(self):
        registry = ServiceRegistry()
        registry.register("ok", lambda: True)
        registry.register("broken", lambda: 1 / 0)
        states = registry.check_all()
        self.assertTrue(states["ok"].ok)
        self.assertFalse(states["broken"].ok)
        self.assertIn("ZeroDivisionError", states["broken"].detail)


if __name__ == "__main__":
    unittest.main()
