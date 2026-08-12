"""CBSE/NCERT library management for Atlas Student.

The repository stores the indexing machinery, not textbook PDFs. Authorized
local PDFs are ingested into compact text indexes; the original PDF stays at
its original location. Classes 9-12 are the required core curriculum, while
other classes can be handled separately as user-provided material.
"""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

from .ingest import ingest_pdf, list_indexed_books

CORE_CLASSES = (9, 10, 11, 12)


@dataclass(frozen=True)
class BookSpec:
    class_level: int
    subject: str
    title: str


class NCERTLibrary:
    """Validate and manage the student's local CBSE/NCERT core library."""

    def __init__(self, books: Iterable[dict] | None = None):
        self._books = list(books) if books is not None else list_indexed_books()

    @staticmethod
    def validate_class(class_level: int) -> int:
        if class_level not in CORE_CLASSES:
            raise ValueError("NCERT core library supports Classes 9-12")
        return class_level

    def indexed_books(self, class_level: int | None = None, subject: str | None = None) -> list[dict]:
        result = self._books
        if class_level is not None:
            self.validate_class(class_level)
            result = [b for b in result if b.get("class") == class_level]
        if subject:
            wanted = subject.strip().lower()
            result = [b for b in result if b.get("subject", "").strip().lower() == wanted]
        return result

    def missing_core(self, required_subjects: dict[int, Iterable[str]]) -> list[BookSpec]:
        """Return missing class/subject slots without inventing book titles."""
        present = {(b.get("class"), b.get("subject", "").strip().lower()) for b in self._books}
        missing = []
        for class_level, subjects in required_subjects.items():
            self.validate_class(class_level)
            for subject in subjects:
                if (class_level, subject.strip().lower()) not in present:
                    missing.append(BookSpec(class_level, subject, f"{subject} Class {class_level}"))
        return missing

    def add_authorized_pdf(self, pdf_path: str | Path, class_level: int, subject: str, title: str | None = None) -> dict:
        self.validate_class(class_level)
        metadata = ingest_pdf(pdf_path, class_level, subject, title)
        self._books = list_indexed_books()
        return metadata

    @staticmethod
    def storage_policy() -> dict:
        return {
            "original_pdf": "kept at the user's chosen location",
            "atlas_index": "compact extracted UTF-8 text + metadata",
            "repository_policy": "do not commit textbook PDFs",
            "core_classes": list(CORE_CLASSES),
        }
