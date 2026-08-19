import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from project import project_manager


class ProjectManagerTests(unittest.TestCase):
    def test_project_store_round_trip_and_atomic_save(self):
        with tempfile.TemporaryDirectory() as tmp:
            target = Path(tmp) / "projects.json"
            with patch.object(project_manager, "PROJECT_FILE", str(target)):
                self.assertTrue(project_manager.create_project("Atlas"))
                self.assertTrue(project_manager.add_task("Atlas", "test"))
                data = project_manager.list_projects()
                self.assertEqual(data["Atlas"]["tasks"], ["test"])
                self.assertFalse(target.with_suffix(".json.tmp").exists())

    def test_corrupt_store_is_preserved(self):
        with tempfile.TemporaryDirectory() as tmp:
            target = Path(tmp) / "projects.json"
            target.write_text("{broken", encoding="utf-8")
            with patch.object(project_manager, "PROJECT_FILE", str(target)):
                data = project_manager.load_projects()
            self.assertEqual(data, {})
            self.assertTrue(Path(str(target) + ".corrupt").exists())
            json.loads(target.read_text(encoding="utf-8"))


if __name__ == "__main__":
    unittest.main()
