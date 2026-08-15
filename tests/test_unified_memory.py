import json
import os
import tempfile
import unittest

from memory.memory_manager import MemoryManager


class UnifiedMemoryTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.old_cwd = os.getcwd()
        os.chdir(self.temp.name)
        os.makedirs("memory", exist_ok=True)
        self.manager = MemoryManager()

    def tearDown(self):
        os.chdir(self.old_cwd)
        self.temp.cleanup()

    def test_single_unified_schema(self):
        self.manager.remember("favorite_subject", "physics")
        self.manager.add_important_memory("Atlas is a long-term project")
        data = self.manager.load()
        self.assertEqual(data["version"], 2)
        self.assertEqual(len(data["memories"]), 2)
        self.assertTrue(all("id" in item and "status" in item for item in data["memories"]))

    def test_fact_update_supersedes_old_value(self):
        self.manager.remember("favorite_subject", "physics")
        self.manager.remember("favorite_subject", "computer science")
        self.assertEqual(self.manager.recall("favorite_subject"), "computer science")
        records = self.manager.get_all_records()
        self.assertEqual(sum(r.get("status") == "superseded" for r in records), 1)

    def test_duplicate_important_memory_is_not_created(self):
        first = self.manager.add_important_memory("Atlas Student matters")
        second = self.manager.add_important_memory("Atlas Student matters")
        self.assertEqual(first["id"], second["id"])
        self.assertEqual(len(self.manager.get_all_records()), 1)

    def test_search_returns_relevant_memory(self):
        self.manager.add_important_memory("Atlas Student uses a unified memory system")
        self.manager.add_important_memory("The user likes chess")
        results = self.manager.search("How does Atlas Student memory work?")
        self.assertTrue(results)
        self.assertIn("unified memory", results[0]["content"])
        self.assertGreater(results[0]["score"], 0.18)

    def test_forget_archives_instead_of_destroying(self):
        self.manager.add_important_memory("remember Atlas architecture")
        self.assertTrue(self.manager.archive_matching("Atlas architecture"))
        self.assertEqual(self.manager.get_important_memories(), [])
        archive = self.manager.get_archive()["items"]
        self.assertEqual(len(archive), 1)
        self.assertEqual(archive[0]["status"], "archived")

    def test_forget_all_archives_every_active_memory(self):
        self.manager.remember("name", "Student")
        self.manager.add_important_memory("Atlas project")
        count = self.manager.archive_all()
        self.assertEqual(count, 2)
        self.assertEqual(self.manager.get_all_records(include_archived=False), [])
        self.assertEqual(len(self.manager.get_archive()["items"]), 2)

    def test_legacy_schema_is_migrated(self):
        path = "memory/memory.json"
        with open(path, "w", encoding="utf-8") as handle:
            json.dump({"facts": {"name": "Student"}, "important_memories": ["Build Atlas"]}, handle)
        manager = MemoryManager(path)
        self.assertEqual(manager.recall("name"), "Student")
        self.assertIn("Build Atlas", manager.get_important_memories())
        self.assertEqual(manager.load()["version"], 2)


if __name__ == "__main__":
    unittest.main()
