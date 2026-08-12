"""Helpers for incremental NCERT library indexing."""
from __future__ import annotations

import hashlib
from pathlib import Path


def content_hash(path: str | Path) -> str:
    """Return the same short SHA-256 fingerprint used by PDF book IDs."""
    digest = hashlib.sha256()
    with Path(path).open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()[:16]


def indexed_hash(book: dict) -> str | None:
    """Extract a content fingerprint from an indexed book id."""
    book_id = str(book.get("id", ""))
    return book_id.rsplit("-", 1)[-1] if "-" in book_id else None


def is_unchanged(path: str | Path, book: dict) -> bool:
    """Return True when an indexed book represents the current PDF bytes."""
    return bool(book.get("original_path")) and indexed_hash(book) == content_hash(path)
