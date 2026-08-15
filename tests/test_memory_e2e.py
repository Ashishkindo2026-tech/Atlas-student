import os
import tempfile
import unittest

from memory.memory_manager import MemoryManager
from memory.memory_router import MemoryRouter


class MemoryEndToEndTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.old_cwd = os.getcwd()
        os.chdir(self.temp.name)
        os.makedirs("memory", exist_ok=True)
        self.manager = MemoryManager()
        self.router = MemoryRouter()
        self.router.long_term = self.manager
        self.router.archive.memory = self.manager

    def tearDown(self):
        os.chdir(self.old_cwd)
        self.temp.cleanup()

    def test_realistic_memory_lifecycle(self):
        # 1–2: remember a durable fact through the user-facing router.
        command = self.router.route("Remember that I am building Atlas Student")
        self.assertEqual(command["type"], "memory_request")
        saved = self.router.save_memory(command["value"])
        self.assertTrue(saved)

        # 3–4: unrelated conversation does not erase the memory.
        self.assertEqual(self.router.route("What is 2 + 2?")["type"], "conversation")
        results = self.router.search("What am I building?")
        self.assertTrue(results)
        self.assertIn("Atlas Student", results[0]["content"])

        # 5: update the same concept; history must retain the old state.
        self.manager.remember("current_project", "Atlas Student")
        self.manager.remember("current_project", "Atlas Core")
        self.assertEqual(self.manager.recall("current_project"), "Atlas Core")
        history = self.manager.get_all_records()
        self.assertTrue(any(r.get("status") == "superseded" and r.get("value") == "Atlas Student" for r in history))

        # 6: forget the remembered project; it becomes archived, not destroyed.
        forget = self.router.route("Forget Atlas Student")
        self.assertEqual(forget["type"], "forget_request")
        self.assertTrue(self.router.forget_memory(forget["value"]))
        active = self.router.search("Atlas Student")
        self.assertFalse(any(r.get("status") == "active" and "Atlas Student" in r.get("content", "") for r in active))
        archived = self.router.get_archive()["items"]
        self.assertTrue(any("Atlas Student" in r.get("content", "") for r in archived))

    def test_forget_all_lifecycle(self):
        self.manager.remember("project", "Atlas Student")
        self.manager.add_important_memory("User wants persistent local memory")
        command = self.router.route("forget everything")
        self.assertEqual(command["type"], "forget_all")
        count = self.router.forget_all_memory()
        self.assertEqual(count, 2)
        self.assertEqual(self.manager.get_all_records(include_archived=False), [])
        self.assertEqual(len(self.manager.get_archive()["items"]), 2)


if __name__ == "__main__":
    unittest.main()
