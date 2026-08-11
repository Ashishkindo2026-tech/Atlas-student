"""CBSE/NCERT curriculum primitives for Atlas Student.

This module stores structure and metadata, not copyrighted textbook content.
Actual books should be supplied through the approved ingestion pipeline.
"""
from dataclasses import dataclass, field
from typing import Dict, List, Optional


@dataclass
class Concept:
    name: str
    section: Optional[str] = None


@dataclass
class Chapter:
    number: str
    title: str
    concepts: List[Concept] = field(default_factory=list)


@dataclass
class Book:
    title: str
    subject: str
    class_level: int
    chapters: List[Chapter] = field(default_factory=list)
    source: str = "NCERT/CBSE"


class Curriculum:
    """Registry for Class 1-12 academic structure."""

    def __init__(self):
        self.books: Dict[str, Book] = {}

    def add_book(self, book: Book) -> None:
        key = self.key(book.class_level, book.subject, book.title)
        self.books[key] = book

    def get_book(self, class_level: int, subject: str, title: str) -> Optional[Book]:
        return self.books.get(self.key(class_level, subject, title))

    def list_books(self, class_level: Optional[int] = None, subject: Optional[str] = None) -> List[Book]:
        result = list(self.books.values())
        if class_level is not None:
            result = [b for b in result if b.class_level == class_level]
        if subject is not None:
            result = [b for b in result if b.subject.lower() == subject.lower()]
        return result

    @staticmethod
    def key(class_level: int, subject: str, title: str) -> str:
        if not 1 <= int(class_level) <= 12:
            raise ValueError("class_level must be between 1 and 12")
        return f"{int(class_level)}:{subject.strip().lower()}:{title.strip().lower()}"
