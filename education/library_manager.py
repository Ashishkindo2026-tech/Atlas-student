"""Automatic local NCERT library discovery and registry for Atlas Student.

The manager discovers user-provided/authorized PDFs under ``ncert_books`` and
maps them to Classes 9-12. It never copies or commits the PDFs; ingestion is
performed only when explicitly requested by the caller.
"""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

from .ncert_library import CORE_CLASSES


@dataclass(frozen=True)
class LibraryBook:
    class_level: int
    subject: str
    path: Path
    title: str


class LibraryManager:
    """Discover and report the student's local NCERT PDF library."""

    def __init__(self, root: str | Path | None = None):
        self.root = Path(root) if root is not None else Path(__file__).resolve().parent.parent / "ncert_books"

    @staticmethod
    def _class_from_dir(name: str) -> int | None:
        value = name.strip().lower().replace("class", "").strip()
        try:
            level = int(value)
        except ValueError:
            return None
        return level if level in CORE_CLASSES else None

    def discover(self) -> list[LibraryBook]:
        """Return PDFs found in ``class9`` ... ``class12`` folders.

        Subject is taken from the immediate subfolder when present; otherwise
        ``Unknown`` is used so the manager never invents a subject.
        """
        if not self.root.exists():
            return []
        books: list[LibraryBook] = []
        for class_dir in sorted(self.root.iterdir()):
            if not class_dir.is_dir():
                continue
            level = self._class_from_dir(class_dir.name)
            if level is None:
                continue
            for pdf in sorted(class_dir.rglob("*.pdf")):
                relative_parts = pdf.relative_to(class_dir).parts
                subject = relative_parts[0] if len(relative_parts) > 1 else "Unknown"
                books.append(LibraryBook(level, subject, pdf, pdf.stem))
        return books

    def registry(self) -> dict[int, dict[str, list[str]]]:
        """Return a compact class -> subject -> book-title registry."""
        result = {level: {} for level in CORE_CLASSES}
        for book in self.discover():
            result.setdefault(book.class_level, {}).setdefault(book.subject, []).append(book.title)
        return result

    def missing_classes(self) -> list[int]:
        present = {book.class_level for book in self.discover()}
        return [level for level in CORE_CLASSES if level not in present]

    def missing_subjects(self, expected: dict[int, Iterable[str]]) -> dict[int, list[str]]:
        registry = self.registry()
        missing: dict[int, list[str]] = {}
        for level, subjects in expected.items():
            if level not in CORE_CLASSES:
                raise ValueError("NCERT core library supports Classes 9-12")
            existing = {subject.strip().lower() for subject in registry.get(level, {})}
            absent = [subject for subject in subjects if subject.strip().lower() not in existing]
            if absent:
                missing[level] = absent
        return missing
