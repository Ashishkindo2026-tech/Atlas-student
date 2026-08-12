import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from education.library_watcher import scan_library, scan_and_ingest


class LibraryWatcherTests(unittest.TestCase):
    def test_scans_class_subject_pdf_layout(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            pdf = root / "class10" / "Science" / "science.pdf"
            pdf.parent.mkdir(parents=True)
            pdf.write_bytes(b"pdf")
            self.assertEqual(scan_library(root), [(pdf, 10, "Science")])

    def test_ignores_non_core_classes(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            pdf = root / "class8" / "Science" / "science.pdf"
            pdf.parent.mkdir(parents=True)
            pdf.write_bytes(b"pdf")
            self.assertEqual(scan_library(root), [])

    def test_repeated_scan_skips_indexed_pdf(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            pdf = root / "class10" / "Science" / "science.pdf"
            pdf.parent.mkdir(parents=True)
            pdf.write_bytes(b"pdf")
            fake = {"original_path": str(pdf.resolve()), "id": "existing"}
            with patch("education.library_watcher.list_indexed_books", return_value=[fake]), patch(
                "education.library_watcher.ingest_pdf"
            ) as ingest:
                self.assertEqual(scan_and_ingest(root), [])
                ingest.assert_not_called()

    def test_new_pdf_is_ingested_once(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            pdf = root / "class12" / "Physics" / "physics.pdf"
            pdf.parent.mkdir(parents=True)
            pdf.write_bytes(b"pdf")
            metadata = {"id": "physics"}
            with patch("education.library_watcher.list_indexed_books", return_value=[]), patch(
                "education.library_watcher.ingest_pdf", return_value=metadata
            ) as ingest:
                self.assertEqual(scan_and_ingest(root), [metadata])
                ingest.assert_called_once_with(pdf, 12, "Physics")


if __name__ == "__main__":
    unittest.main()
