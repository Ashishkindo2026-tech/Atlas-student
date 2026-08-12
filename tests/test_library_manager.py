import tempfile
import unittest
from pathlib import Path

from education.library_manager import LibraryManager


class LibraryManagerTests(unittest.TestCase):
    def make_library(self, root: Path) -> None:
        (root / "class9" / "Science").mkdir(parents=True)
        (root / "class10" / "Mathematics").mkdir(parents=True)
        (root / "class11").mkdir(parents=True)
        (root / "class12" / "Physics").mkdir(parents=True)
        (root / "class9" / "Science" / "science.pdf").write_bytes(b"pdf")
        (root / "class10" / "Mathematics" / "math.pdf").write_bytes(b"pdf")
        (root / "class11" / "chemistry.pdf").write_bytes(b"pdf")
        (root / "class12" / "Physics" / "physics.pdf").write_bytes(b"pdf")
        (root / "class8" / "Old" ).mkdir(parents=True)
        (root / "class8" / "Old" / "old.pdf").write_bytes(b"pdf")

    def test_discovers_only_core_classes(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            self.make_library(root)
            books = LibraryManager(root).discover()
            self.assertEqual({book.class_level for book in books}, {9, 10, 11, 12})
            self.assertEqual(len(books), 4)

    def test_subject_comes_from_folder_without_inventing_unknown(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            self.make_library(root)
            registry = LibraryManager(root).registry()
            self.assertIn("Science", registry[9])
            self.assertIn("Unknown", registry[11])

    def test_registry_and_missing_classes(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            (root / "class10" / "Science").mkdir(parents=True)
            (root / "class10" / "Science" / "book.pdf").write_bytes(b"pdf")
            manager = LibraryManager(root)
            self.assertEqual(manager.missing_classes(), [9, 11, 12])
            self.assertIn("Science", manager.registry()[10])

    def test_missing_subjects_are_reported(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            (root / "class9" / "Science").mkdir(parents=True)
            (root / "class9" / "Science" / "book.pdf").write_bytes(b"pdf")
            missing = LibraryManager(root).missing_subjects({9: ["Science", "Mathematics"]})
            self.assertEqual(missing, {9: ["Mathematics"]})


if __name__ == "__main__":
    unittest.main()
