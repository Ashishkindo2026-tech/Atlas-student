"""Document primitives for searchable educational material."""
from dataclasses import dataclass
from typing import Optional


@dataclass(frozen=True)
class DocumentChunk:
    text: str
    page: Optional[int] = None
    chapter: Optional[str] = None
    section: Optional[str] = None
    source: str = "unknown"

    def searchable_text(self) -> str:
        return self.text


@dataclass(frozen=True)
class SearchResult:
    chunk: DocumentChunk
    score: float = 0.0


class DocumentIndex:
    """Small deterministic index foundation; replace with vector/full-text backend later."""

    def __init__(self):
        self.chunks = []

    def add(self, chunk: DocumentChunk) -> None:
        if chunk.text.strip():
            self.chunks.append(chunk)

    def search(self, query: str, limit: int = 5):
        terms = {t.lower() for t in query.split() if t.strip()}
        if not terms:
            return []
        scored = []
        for chunk in self.chunks:
            words = set(chunk.text.lower().split())
            score = sum(term in words for term in terms) / len(terms)
            if score > 0:
                scored.append(SearchResult(chunk, score))
        return sorted(scored, key=lambda r: r.score, reverse=True)[:limit]
