"""Automatic importer for PDFs dropped into Atlas Student's local library.

The watcher is deliberately polling-based: it needs no always-on third-party
file-system dependency and can be called at Atlas startup or periodically.
Original PDFs stay where the student placed them; ingestion only creates the
compact local index.
"""
from __future__ import annotations

import hashlib
from pathlib import Path

from .ingest import ingest_pdf, LIBRARY_ROOT, list_indexed_books, remove_indexed_book

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


def _fingerprint(path: Path) -> str:
    """Return a stable content fingerprint for incremental indexing."""
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def _matching_books(path: Path) -> list[dict]:
    canonical = str(path.resolve())
    return [
        book for book in list_indexed_books()
        if str(Path(book.get("original_path", "")).expanduser().resolve()) == canonical
    ]


def scan_and_ingest(root: str | Path | None = None) -> list[dict]:
    """Detect new/changed PDFs and incrementally update their local indexes.

    New files are indexed, unchanged files are skipped, and changed files are
    re-indexed. The original PDF is never modified or deleted.
    """
    results = []
    for pdf, class_level, subject in scan_library(root):
        canonical = pdf.resolve()
        fingerprint = _fingerprint(canonical)
        existing = _matching_books(canonical)

        # Fast path: content is unchanged, so startup scans do no work.
        if any(book.get("fingerprint") == fingerprint for book in existing):
            continue

        # Remove stale indexes for this original path before indexing the new
        # content. This also prevents old versions from remaining searchable.
        for book in existing:
            remove_indexed_book(book["id"])

        try:
            metadata = ingest_pdf(pdf, class_level, subject)
            # Persist the fingerprint in the manifest through the metadata
            # update API exposed by ingest.py's manifest-backed storage.
            from . import ingest as ingest_module
            manifest = ingest_module._load_manifest()
            manifest["books"][metadata["id"]]["fingerprint"] = fingerprint
            ingest_module._save_manifest(manifest)
            metadata["fingerprint"] = fingerprint
            metadata["action"] = "indexed" if not existing else "reindexed"
            results.append(metadata)
        except Exception as exc:
            results.append({"path": str(pdf), "error": str(exc)})
    return results
