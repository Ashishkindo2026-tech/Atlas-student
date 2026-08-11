"""Core CBSE Class 9-12 configuration for Atlas Student.

This contains curriculum metadata/configuration only. It deliberately does not
bundle copyrighted textbook PDFs. Authorized/user-provided books are ingested
through the document pipeline and mapped to this structure.
"""
from dataclasses import dataclass, field
from typing import Dict, List

CORE_CLASSES = (9, 10, 11, 12)

# High-level subject registry. It is intentionally extensible because CBSE
# subject offerings can vary by school/academic year.
DEFAULT_SUBJECTS: Dict[int, List[str]] = {
    9: ["Mathematics", "Science", "Social Science", "English", "Hindi"],
    10: ["Mathematics", "Science", "Social Science", "English", "Hindi"],
    11: ["Physics", "Chemistry", "Mathematics", "Biology", "English", "Computer Science"],
    12: ["Physics", "Chemistry", "Mathematics", "Biology", "English", "Computer Science"],
}


@dataclass
class CoreBook:
    class_level: int
    subject: str
    title: str
    path: str = ""
    indexed: bool = False
    pages: int = 0
    metadata: Dict[str, str] = field(default_factory=dict)

    def __post_init__(self):
        if self.class_level not in CORE_CLASSES:
            raise ValueError("CoreBook only supports Classes 9-12")
        if not self.subject.strip() or not self.title.strip():
            raise ValueError("subject and title are required")


class CBSECore:
    """Registry and validation layer for Atlas Student's Classes 9-12 core."""

    def __init__(self):
        self.books: Dict[str, CoreBook] = {}

    def register_book(self, book: CoreBook) -> None:
        key = self.key(book.class_level, book.subject, book.title)
        self.books[key] = book

    def get_book(self, class_level: int, subject: str, title: str):
        return self.books.get(self.key(class_level, subject, title))

    def books_for_class(self, class_level: int) -> List[CoreBook]:
        if class_level not in CORE_CLASSES:
            raise ValueError("Atlas Student core supports Classes 9-12")
        return [b for b in self.books.values() if b.class_level == class_level]

    @staticmethod
    def key(class_level: int, subject: str, title: str) -> str:
        if class_level not in CORE_CLASSES:
            raise ValueError("Atlas Student core supports Classes 9-12")
        return f"{class_level}:{subject.strip().lower()}:{title.strip().lower()}"

    @staticmethod
    def subjects_for_class(class_level: int) -> List[str]:
        if class_level not in CORE_CLASSES:
            raise ValueError("Atlas Student core supports Classes 9-12")
        return list(DEFAULT_SUBJECTS.get(class_level, []))
