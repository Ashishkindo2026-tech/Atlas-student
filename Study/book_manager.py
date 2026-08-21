"""Local study-book catalog with deterministic CRUD operations."""
from __future__ import annotations

from dataclasses import asdict, dataclass
import json
from pathlib import Path


@dataclass(frozen=True)
class Book:
    title: str
    subject: str = "general"
    path: str | None = None


class BookManager:
    """Manage a small local catalog without requiring a database service."""

    def __init__(self, catalog_path: Path | str):
        self.catalog_path = Path(catalog_path)
        self.books: list[Book] = []
        self.load()

    def add(self, title: str, subject: str = "general", path: str | None = None) -> Book:
        title = title.strip()
        subject = subject.strip() or "general"
        if not title:
            raise ValueError("title must not be empty")
        book = Book(title=title, subject=subject, path=path)
        if not any(existing.title.casefold() == title.casefold() for existing in self.books):
            self.books.append(book)
        return book

    def search(self, query: str) -> list[Book]:
        query = query.strip().casefold()
        if not query:
            return list(self.books)
        return [book for book in self.books if query in book.title.casefold() or query in book.subject.casefold()]

    def remove(self, title: str) -> bool:
        target = title.strip().casefold()
        before = len(self.books)
        self.books = [book for book in self.books if book.title.casefold() != target]
        return len(self.books) != before

    def save(self) -> None:
        self.catalog_path.parent.mkdir(parents=True, exist_ok=True)
        self.catalog_path.write_text(
            json.dumps([asdict(book) for book in self.books], indent=2), encoding="utf-8"
        )

    def load(self) -> None:
        if not self.catalog_path.exists():
            return
        data = json.loads(self.catalog_path.read_text(encoding="utf-8"))
        if not isinstance(data, list):
            raise ValueError("book catalog must contain a list")
        self.books = [Book(**item) for item in data if isinstance(item, dict) and item.get("title")]
