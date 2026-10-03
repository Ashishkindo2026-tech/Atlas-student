import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import fitz

from education import ingest
from education import library_watcher


def make_pdf(path: Path, text: str) -> None:
    doc = fitz.open()
    page = doc.new_page()
    page.insert_text((72, 72), text)
    doc.save(path)
    doc.close()


class PdfIncrementalTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        self.index = self.root / "index"
        self.manifest = self.index / "manifest.json"
        self.watch = self.root / "books"
        (self.watch / "class10" / "Physics").mkdir(parents=True)
        self.pdf = self.watch / "class10" / "Physics" / "physics.pdf"
        make_pdf(self.pdf, "velocity and acceleration")

    def tearDown(self):
        self.tmp.cleanup()

    def test_new_same_and_changed_pdf(self):
        with patch.object(ingest, "INDEX_ROOT", self.index), patch.object(
            ingest, "MANIFEST_FILE", self.manifest
        ):
            first = ingest.ingest_pdf(self.pdf, 10, "Physics")
            self.assertEqual(first["status"], "indexed")
            self.assertTrue(first["fingerprint"])

            second = ingest.ingest_pdf(self.pdf, 10, "Physics")
            self.assertEqual(second["status"], "skipped")
            self.assertEqual(second["reason"], "unchanged")

            make_pdf(self.pdf, "NEW CONTENT: momentum and impulse")
            third = ingest.ingest_pdf(self.pdf, 10, "Physics")
            self.assertEqual(third["status"], "indexed")
            self.assertNotEqual(first["fingerprint"], third["fingerprint"])
            books = ingest.list_indexed_books()
            self.assertEqual(len(books), 1)

    def test_watcher_removes_deleted_pdf(self):
        with patch.object(ingest, "INDEX_ROOT", self.index), patch.object(
            ingest, "MANIFEST_FILE", self.manifest
        ), patch.object(library_watcher, "USER_ROOT", self.watch):
            created = library_watcher.scan_and_ingest(self.watch)
            self.assertTrue(any(x.get("status") == "indexed" for x in created))
            self.pdf.unlink()
            removed = library_watcher.scan_and_ingest(self.watch)
            self.assertTrue(any(x.get("status") == "removed" for x in removed))
            self.assertEqual(ingest.list_indexed_books(), [])


if __name__ == "__main__":
    unittest.main()
