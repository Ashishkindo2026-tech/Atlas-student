import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from student.progress_manager import ProgressManager


class ProgressManagerTests(unittest.TestCase):
    def test_round_trip(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "progress.json"
            with patch("student.progress_manager.FILE", path):
                manager = ProgressManager()
                manager.record_session("Physics", 45, "Kinematics")
                self.assertIn("Physics", manager.data()["subjects"])
                self.assertEqual(manager.data()["subjects"]["Physics"]["minutes"], 45)
                self.assertTrue(manager.set_mastery("Physics", "Motion", 70))
                self.assertIn("Physics::Motion", manager.data()["concepts"])
                self.assertIn("70%", manager.summary())

    def test_corrupt_file_recovers(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "progress.json"
            path.write_text("not-json", encoding="utf-8")
            with patch("student.progress_manager.FILE", path):
                manager = ProgressManager()
                self.assertEqual(manager.data(), {"subjects": {}, "concepts": {}, "sessions": []})
                manager.record_session("Math", 20)
                self.assertEqual(manager.data()["subjects"]["Math"]["minutes"], 20)


if __name__ == "__main__":
    unittest.main()
