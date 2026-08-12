"""Document primitives and deterministic word-level retrieval for Atlas Student."""
from dataclasses import dataclass
from typing import Optional
import re


_TOKEN_RE = re.compile(r"[\w]+(?:['’-][\w]+)?", re.UNICODE)


def tokenize(text: str) -> list[str]:
    """Normalize text into searchable words while preserving apostrophes."""
    return [token.lower().replace("’", "'") for token in _TOKEN_RE.findall(text)]


@dataclass(frozen=True)
class DocumentChunk:
    text: str
    page: Optional[int] = None
    chapter: Optional[str] = None
    section: Optional[str] = None
    source: str = "unknown"
    class_level: Optional[int] = None
    subject: Optional[str] = None

    def searchable_text(self) -> str:
        """Return the chunk text used for normal content retrieval."""
        return self.text

    def metadata_text(self) -> str:
        """Return searchable metadata without inventing missing fields."""
        parts = [self.chapter, self.section, self.source, self.subject]
        return " ".join(part for part in parts if part)


@dataclass(frozen=True)
class SearchResult:
    chunk: DocumentChunk
    score: float = 0.0


class DocumentIndex:
    """Small deterministic full-text index with class/subject filtering.

    It is intentionally dependency-free: Atlas can search an indexed NCERT
    library on a modest local machine before a vector backend is introduced.
    """

    def __init__(self):
        self.chunks: list[DocumentChunk] = []
        self._tokens: list[set[str]] = []
        self._metadata_tokens: list[set[str]] = []

    def add(self, chunk: DocumentChunk) -> None:
        if not chunk.text.strip():
            return
        self.chunks.append(chunk)
        self._tokens.append(set(tokenize(chunk.searchable_text())))
        self._metadata_tokens.append(set(tokenize(chunk.metadata_text())))

    def search(
        self,
        query: str,
        limit: int = 5,
        class_level: Optional[int] = None,
        subject: Optional[str] = None,
    ) -> list[SearchResult]:
        terms = set(tokenize(query))
        if not terms or limit <= 0:
            return []

        wanted_subject = subject.strip().lower() if subject else None
        scored: list[SearchResult] = []
        for chunk, words, metadata_words in zip(
            self.chunks, self._tokens, self._metadata_tokens
        ):
            # A requested class is a hard boundary. Unknown class metadata is
            # not allowed to leak into a class-specific retrieval request.
            if class_level is not None and chunk.class_level != class_level:
                continue
            if wanted_subject and (
                not chunk.subject or chunk.subject.strip().lower() != wanted_subject
            ):
                continue

            matched_text = terms & words
            matched_metadata = terms & metadata_words
            matched = matched_text | matched_metadata
            if not matched:
                continue

            # Content matches are stronger than metadata-only matches.
            score = (len(matched_text) / len(terms)) + (
                0.20 * len(matched_metadata) / len(terms)
            )
            normalized_text = " ".join(tokenize(chunk.text))
            normalized_query = " ".join(tokenize(query))
            if normalized_query and normalized_query in normalized_text:
                score += 0.35
            if chunk.chapter and any(term in tokenize(chunk.chapter) for term in terms):
                score += 0.10
            if chunk.section and any(term in tokenize(chunk.section) for term in terms):
                score += 0.05
            scored.append(SearchResult(chunk, score))

        scored.sort(key=lambda result: (-result.score, result.chunk.page or 0))
        return scored[:limit]
