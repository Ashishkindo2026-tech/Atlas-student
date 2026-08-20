import json
import tempfile
import unittest
from pathlib import Path

from memory.memory_manager import MemoryManager


class MemoryReliabilityTests(unittest.TestCase):
    def test_search_score_is_transient(self):
        with tempfile.TemporaryDirectory() as tmp:
            manager = MemoryManager(Path(tmp) / "memory.json")
            manager.remember("subject", "physics", importance=0.9)
            results = manager.search("physics")
            self.assertTrue(results)
            self.assertIn("score", results[0])
            stored = manager.load()["memories"][0]
            self.assertNotIn("score", stored)
            self.assertGreaterEqual(stored["access_count"], 1)

    def test_corrupt_store_is_backed_up(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "memory.json"
            path.write_text("{not valid json", encoding="utf-8")
            manager = MemoryManager(path)
            self.assertEqual(manager.load()["memories"], [])
            self.assertTrue(Path(str(path) + ".corrupt").exists())
            json.loads(path.read_text(encoding="utf-8"))

    def test_round_trip_preserves_unicode(self):
        with tempfile.TemporaryDirectory() as tmp:
            manager = MemoryManager(Path(tmp) / "memory.json")
            manager.add_important_memory("Physics: ऊर्जा और गति 🚀")
            contents = manager.get_important_memories()
            self.assertIn("Physics: ऊर्जा और गति 🚀", contents)


if __name__ == "__main__":
    unittest.main()
