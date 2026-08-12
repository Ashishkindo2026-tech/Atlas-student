"""Automatic importer for PDFs dropped into Atlas Student's local library.

The watcher is deliberately polling-based: it needs no always-on third-party
file-system dependency and can be called at Atlas startup or periodically.
Original PDFs stay where the student placed them; ingestion only creates the
compact local index.
"""
from __future__ import annotations

from pathlib import Path
from .ingest import ingest_pdf, LIBRARY_ROOT, list_indexed_books

CORE_ROOT = LIBRARY_ROOT / "core"
USER_ROOT = Path(__file__).resolve().parent.parent / "ncert_books"
CORE_CLASSES = {9, 10, 11, 12}


def _class_from_folder(name: str) -> int | None:
    value = name.strip().lower().replace("class", "")
    try:
        number = int(value)
    except ValueError:
        return None
    return number if number in CORE_CLASSES else None


def _scan_root(root: Path) -> list[tuple[Path, int, str]]:
    found = []
    if not root.exists():
        return found
    for pdf in root.rglob("*.pdf"):
        relative = pdf.relative_to(root)
        parts = relative.parts
        if len(parts) < 3:
            continue
        class_level = _class_from_folder(parts[0])
        if class_level is None:
            continue
        subject = parts[1].strip()
        if not subject:
            continue
        found.append((pdf, class_level, subject))
    return found


def scan_library(root: str | Path | None = None) -> list[tuple[Path, int, str]]:
    """Return valid Class 9-12 PDF candidates without indexing them."""
    scan_root = Path(root).expanduser().resolve() if root else USER_ROOT
    return _scan_root(scan_root)


def scan_and_ingest(root: str | Path | None = None) -> list[dict]:
    """Detect and ingest newly dropped core PDFs.

    Already-indexed PDFs are skipped using their canonical original path. This
    makes repeated startup scans safe and prevents duplicate index entries.
    """
    existing = {
        str(Path(book.get("original_path", "")).expanduser().resolve())
        for book in list_indexed_books()
        if book.get("original_path")
    }
    results = []
    for pdf, class_level, subject in scan_library(root):
        canonical = str(pdf.resolve())
        if canonical in existing:
            continue
        try:
            metadata = ingest_pdf(pdf, class_level, subject)
            existing.add(canonical)
            results.append(metadata)
        except Exception as exc:
            results.append({"path": str(pdf), "error": str(exc)})
    return results
